"""Job management for async taxonomy generation."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from delve.api.schemas import (
    ClassifierMetrics,
    JobMetadata,
    JobResponse,
    JobStatus,
    LabeledDocumentResponse,
    TaxonomyCategoryResponse,
    TaxonomyResult,
)


class Job:
    """Represents a taxonomy generation job."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: Optional[str] = None
        self.error: Optional[str] = None
        self.result: Optional[TaxonomyResult] = None
        self._subscribers: List[asyncio.Queue] = []

    def to_response(self) -> JobResponse:
        """Convert to API response."""
        return JobResponse(
            job_id=self.job_id,
            status=self.status,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            progress=self.progress,
            error=self.error,
            result=self.result,
        )

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to job updates. Returns a queue for receiving events."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from job updates."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def notify(self, event: Dict[str, Any]) -> None:
        """Notify all subscribers of an event."""
        for queue in self._subscribers:
            await queue.put(event)


class JobManager:
    """Manages taxonomy generation jobs."""

    def __init__(self, max_jobs: int = 100) -> None:
        """Initialize job manager.

        Args:
            max_jobs: Maximum number of jobs to keep in memory.
        """
        self._jobs: Dict[str, Job] = {}
        self._max_jobs = max_jobs
        self._lock = asyncio.Lock()

    async def create_job(self) -> Job:
        """Create a new job."""
        async with self._lock:
            # Clean up old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()

            job_id = str(uuid.uuid4())
            job = Job(job_id)
            self._jobs[job_id] = job
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Job], int]:
        """List jobs with optional filtering.

        Returns:
            Tuple of (jobs, total_count)
        """
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        total = len(jobs)
        jobs = jobs[offset : offset + limit]

        return jobs, total

    async def update_job_progress(self, job_id: str, message: str) -> None:
        """Update job progress message."""
        job = await self.get_job(job_id)
        if job:
            job.progress = message
            await job.notify(
                {
                    "event": "progress",
                    "job_id": job_id,
                    "message": message,
                }
            )

    async def start_job(self, job_id: str) -> None:
        """Mark job as started."""
        job = await self.get_job(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await job.notify(
                {
                    "event": "started",
                    "job_id": job_id,
                }
            )

    async def complete_job(self, job_id: str, result: TaxonomyResult) -> None:
        """Mark job as completed with result."""
        job = await self.get_job(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            await job.notify(
                {
                    "event": "completed",
                    "job_id": job_id,
                    "result": result.model_dump(),
                }
            )

    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error."""
        job = await self.get_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = error
            await job.notify(
                {
                    "event": "error",
                    "job_id": job_id,
                    "error": error,
                }
            )

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        async with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    async def _cleanup_old_jobs(self) -> None:
        """Remove oldest completed/failed jobs to make room."""
        # Get completed/failed jobs sorted by completion time
        finished_jobs = [
            j
            for j in self._jobs.values()
            if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]
        finished_jobs.sort(key=lambda j: j.completed_at or j.created_at)

        # Remove oldest until under capacity
        while len(self._jobs) >= self._max_jobs and finished_jobs:
            job = finished_jobs.pop(0)
            del self._jobs[job.job_id]


def delve_result_to_api_result(delve_result: Any) -> TaxonomyResult:
    """Convert DelveResult to API TaxonomyResult schema."""
    from delve.result import DelveResult

    if not isinstance(delve_result, DelveResult):
        raise ValueError("Expected DelveResult instance")

    # Convert taxonomy categories
    taxonomy = [
        TaxonomyCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
        )
        for cat in delve_result.taxonomy
    ]

    # Convert labeled documents
    labeled_documents = [
        LabeledDocumentResponse(
            id=doc.id,
            content=doc.content,
            category=doc.category,
            summary=doc.summary,
            explanation=doc.explanation,
        )
        for doc in delve_result.labeled_documents
    ]

    # Convert metadata
    metadata_dict = delve_result.metadata
    classifier_metrics = None
    if "classifier_metrics" in metadata_dict and metadata_dict["classifier_metrics"]:
        cm = metadata_dict["classifier_metrics"]
        classifier_metrics = ClassifierMetrics(
            train_accuracy=cm.get("train_accuracy", 0),
            test_accuracy=cm.get("test_accuracy", 0),
            train_f1=cm.get("train_f1", 0),
            test_f1=cm.get("test_f1", 0),
        )

    metadata = JobMetadata(
        num_documents=metadata_dict.get("num_documents", 0),
        num_categories=metadata_dict.get("num_categories", 0),
        sample_size=metadata_dict.get("sample_size", 0),
        batch_size=metadata_dict.get("batch_size", 0),
        model=metadata_dict.get("model", ""),
        fast_llm=metadata_dict.get("fast_llm", ""),
        run_duration_seconds=metadata_dict.get("run_duration_seconds", 0),
        category_counts=metadata_dict.get("category_counts", {}),
        llm_labeled_count=metadata_dict.get("llm_labeled_count", 0),
        classifier_labeled_count=metadata_dict.get("classifier_labeled_count", 0),
        skipped_document_count=metadata_dict.get("skipped_document_count", 0),
        classifier_metrics=classifier_metrics,
        warnings=metadata_dict.get("warnings", []),
    )

    return TaxonomyResult(
        taxonomy=taxonomy,
        labeled_documents=labeled_documents,
        metadata=metadata,
    )


# Global job manager instance
job_manager = JobManager()
