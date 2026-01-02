"""FastAPI server for Delve taxonomy generation."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from delve import Delve, Doc, __version__
from delve.api.jobs import Job, JobManager, delve_result_to_api_result, job_manager
from delve.api.schemas import (
    CreateTaxonomyRequest,
    ErrorResponse,
    HealthResponse,
    JobListResponse,
    JobResponse,
    JobStatus,
)
from delve.console import Verbosity


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown - cleanup jobs if needed


def create_app(
    title: str = "Delve API",
    cors_origins: Optional[list[str]] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title for documentation
        cors_origins: List of allowed CORS origins. Defaults to ["*"] for development.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description="REST API for AI-powered taxonomy generation",
        version=__version__,
        lifespan=lifespan,
        responses={
            400: {"model": ErrorResponse, "description": "Bad Request"},
            404: {"model": ErrorResponse, "description": "Not Found"},
            500: {"model": ErrorResponse, "description": "Internal Server Error"},
        },
    )

    # Configure CORS
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # ========================================================================
    # Health & Info
    # ========================================================================

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Check API health status."""
        return HealthResponse(
            status="healthy",
            version=__version__,
            timestamp=datetime.utcnow(),
        )

    @app.get("/", tags=["Health"])
    async def root():
        """API root - redirect to docs."""
        return {
            "name": "Delve API",
            "version": __version__,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    # ========================================================================
    # Taxonomy Jobs
    # ========================================================================

    @app.post(
        "/taxonomies",
        response_model=JobResponse,
        status_code=202,
        tags=["Taxonomies"],
        summary="Create taxonomy generation job",
        description="Start a new taxonomy generation job. The job runs asynchronously and can be polled for status.",
    )
    async def create_taxonomy(
        request: CreateTaxonomyRequest,
        background_tasks: BackgroundTasks,
    ) -> JobResponse:
        """Create a new taxonomy generation job.

        The job is started in the background. Use the returned job_id to:
        - Poll status via GET /taxonomies/{job_id}
        - Stream progress via GET /taxonomies/{job_id}/stream
        """
        # Validate request
        if not request.file_path and not request.documents:
            raise HTTPException(
                status_code=400,
                detail="Either 'file_path' or 'documents' must be provided",
            )

        if request.file_path and request.documents:
            raise HTTPException(
                status_code=400,
                detail="Only one of 'file_path' or 'documents' can be provided",
            )

        # Create job
        job = await job_manager.create_job()

        # Start background task
        background_tasks.add_task(
            _run_taxonomy_job,
            job=job,
            request=request,
        )

        return job.to_response()

    @app.get(
        "/taxonomies/{job_id}",
        response_model=JobResponse,
        tags=["Taxonomies"],
        summary="Get job status",
        description="Get the current status and result of a taxonomy generation job.",
    )
    async def get_taxonomy_job(job_id: str) -> JobResponse:
        """Get taxonomy job status and result."""
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found",
            )
        return job.to_response()

    @app.get(
        "/taxonomies/{job_id}/stream",
        tags=["Taxonomies"],
        summary="Stream job progress",
        description="Stream real-time progress updates via Server-Sent Events (SSE).",
    )
    async def stream_taxonomy_job(job_id: str):
        """Stream job progress via SSE."""
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found",
            )

        async def event_generator():
            # Send current status first
            yield _format_sse(
                {
                    "event": "status",
                    "job_id": job_id,
                    "status": job.status.value,
                    "progress": job.progress,
                }
            )

            # If already completed, send result and close
            if job.status == JobStatus.COMPLETED:
                yield _format_sse(
                    {
                        "event": "completed",
                        "job_id": job_id,
                        "result": job.result.model_dump() if job.result else None,
                    }
                )
                return

            if job.status == JobStatus.FAILED:
                yield _format_sse(
                    {
                        "event": "error",
                        "job_id": job_id,
                        "error": job.error,
                    }
                )
                return

            # Subscribe to updates
            queue = job.subscribe()
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield _format_sse(event)

                        # Close stream on completion or error
                        if event.get("event") in ("completed", "error"):
                            break
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield ": keepalive\n\n"
            finally:
                job.unsubscribe(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get(
        "/taxonomies",
        response_model=JobListResponse,
        tags=["Taxonomies"],
        summary="List jobs",
        description="List all taxonomy generation jobs with optional filtering.",
    )
    async def list_taxonomy_jobs(
        status: Optional[JobStatus] = Query(None, description="Filter by job status"),
        limit: int = Query(50, ge=1, le=100, description="Maximum jobs to return"),
        offset: int = Query(0, ge=0, description="Offset for pagination"),
    ) -> JobListResponse:
        """List taxonomy generation jobs."""
        jobs, total = await job_manager.list_jobs(status=status, limit=limit, offset=offset)
        return JobListResponse(
            jobs=[j.to_response() for j in jobs],
            total=total,
        )

    @app.delete(
        "/taxonomies/{job_id}",
        status_code=204,
        tags=["Taxonomies"],
        summary="Delete job",
        description="Delete a taxonomy generation job and its results.",
    )
    async def delete_taxonomy_job(job_id: str):
        """Delete a taxonomy job."""
        deleted = await job_manager.delete_job(job_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found",
            )


def _format_sse(data: dict) -> str:
    """Format data as SSE event."""
    return f"data: {json.dumps(data)}\n\n"


async def _run_taxonomy_job(job: Job, request: CreateTaxonomyRequest) -> None:
    """Run taxonomy generation job in background."""
    try:
        await job_manager.start_job(job.job_id)

        # Build configuration
        config = request.config
        predefined = None
        if request.predefined_taxonomy:
            predefined = [
                {"id": c.id, "name": c.name, "description": c.description}
                for c in request.predefined_taxonomy
            ]

        # Create Delve client
        delve = Delve(
            model=config.model,
            fast_llm=config.fast_llm,
            sample_size=config.sample_size,
            batch_size=config.batch_size,
            max_num_clusters=config.max_num_clusters,
            use_case=config.use_case,
            embedding_model=config.embedding_model,
            classifier_confidence_threshold=config.classifier_confidence_threshold,
            predefined_taxonomy=predefined,
            verbosity=Verbosity.SILENT,  # API runs silently
        )

        # Run taxonomy generation
        if request.documents:
            # Inline documents
            await job_manager.update_job_progress(
                job.job_id,
                f"Processing {len(request.documents)} inline documents...",
            )

            docs = [
                Doc(
                    id=d.id or str(i),
                    content=d.content,
                )
                for i, d in enumerate(request.documents)
            ]

            result = await delve.run_with_docs(docs)
        else:
            # File-based source
            await job_manager.update_job_progress(
                job.job_id,
                f"Loading data from {request.file_path}...",
            )

            adapter_kwargs = {}
            if request.json_path:
                adapter_kwargs["json_path"] = request.json_path

            source_type = request.source_type.value if request.source_type else None

            result = await delve.run(
                request.file_path,
                text_column=request.text_column,
                id_column=request.id_column,
                source_type=source_type,
                **adapter_kwargs,
            )

        # Convert result and complete job
        api_result = delve_result_to_api_result(result)
        await job_manager.complete_job(job.job_id, api_result)

    except Exception as e:
        await job_manager.fail_job(job.job_id, str(e))


# Create default app instance
app = create_app()
