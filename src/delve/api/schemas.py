"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class JobStatus(str, Enum):
    """Status of a taxonomy generation job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, Enum):
    """Supported data source types."""

    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    INLINE = "inline"


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


# ============================================================================
# Configuration Schemas
# ============================================================================


class TaxonomyConfig(BaseModel):
    """Configuration for taxonomy generation."""

    model: str = Field(
        default="anthropic/claude-sonnet-4-5-20250929",
        description="Main LLM model for taxonomy generation and reasoning",
    )
    fast_llm: str = Field(
        default="anthropic/claude-haiku-4-5-20251001",
        description="Faster model for document summarization",
    )
    sample_size: int = Field(
        default=100,
        ge=0,
        description="Number of documents to sample for LLM labeling. Set to 0 to process all.",
    )
    batch_size: int = Field(
        default=200,
        ge=1,
        description="Number of documents per minibatch during iterative clustering",
    )
    max_num_clusters: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of categories to generate",
    )
    use_case: Optional[str] = Field(
        default=None,
        description="Custom description of the taxonomy use case to guide generation",
    )
    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="OpenAI embedding model for classifier training",
    )
    classifier_confidence_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for classifier predictions (0 = no fallback to LLM)",
    )


class PredefinedCategory(BaseModel):
    """A predefined taxonomy category."""

    id: str = Field(description="Unique category identifier")
    name: str = Field(description="Category name")
    description: str = Field(description="Category description")


# ============================================================================
# Request Schemas
# ============================================================================


class InlineDocument(BaseModel):
    """A document provided inline in the request."""

    id: Optional[str] = Field(default=None, description="Optional document ID")
    content: str = Field(description="Document text content")


class CreateTaxonomyRequest(BaseModel):
    """Request to create a new taxonomy generation job."""

    # Data source - one of these must be provided
    file_path: Optional[str] = Field(
        default=None,
        description="Path to a file on the server (CSV, JSON, JSONL)",
    )
    documents: Optional[List[InlineDocument]] = Field(
        default=None,
        description="Inline documents to process",
    )

    # Source configuration
    source_type: Optional[SourceType] = Field(
        default=None,
        description="Force specific source type (auto-detected if not provided)",
    )
    text_column: Optional[str] = Field(
        default=None,
        description="Column/field name containing text content (required for CSV)",
    )
    id_column: Optional[str] = Field(
        default=None,
        description="Column/field name for document IDs",
    )
    json_path: Optional[str] = Field(
        default=None,
        description="JSONPath expression for nested JSON data",
    )

    # Taxonomy configuration
    config: TaxonomyConfig = Field(
        default_factory=TaxonomyConfig,
        description="Taxonomy generation configuration",
    )

    # Predefined taxonomy (optional)
    predefined_taxonomy: Optional[List[PredefinedCategory]] = Field(
        default=None,
        description="Use predefined categories instead of generating taxonomy",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "file_path": "/data/feedback.csv",
                    "text_column": "comment",
                    "config": {
                        "sample_size": 100,
                        "max_num_clusters": 8,
                        "use_case": "Categorize customer feedback by topic",
                    },
                },
                {
                    "documents": [
                        {"id": "1", "content": "Fix the login button bug"},
                        {"id": "2", "content": "Add dark mode support"},
                        {"id": "3", "content": "Improve loading performance"},
                    ],
                    "config": {"use_case": "Categorize software issues"},
                },
            ]
        }


# ============================================================================
# Response Schemas
# ============================================================================


class TaxonomyCategoryResponse(BaseModel):
    """A taxonomy category in the response."""

    id: str
    name: str
    description: str


class LabeledDocumentResponse(BaseModel):
    """A labeled document in the response."""

    id: str
    content: str
    category: Optional[str] = None
    summary: Optional[str] = None
    explanation: Optional[str] = None


class ClassifierMetrics(BaseModel):
    """Metrics from the classifier training."""

    train_accuracy: float
    test_accuracy: float
    train_f1: float
    test_f1: float


class JobMetadata(BaseModel):
    """Metadata about a taxonomy generation job."""

    num_documents: int
    num_categories: int
    sample_size: int
    batch_size: int
    model: str
    fast_llm: str
    run_duration_seconds: float
    category_counts: Dict[str, int]
    llm_labeled_count: int
    classifier_labeled_count: int
    skipped_document_count: int
    classifier_metrics: Optional[ClassifierMetrics] = None
    warnings: List[str] = Field(default_factory=list)


class TaxonomyResult(BaseModel):
    """Complete taxonomy generation result."""

    taxonomy: List[TaxonomyCategoryResponse]
    labeled_documents: List[LabeledDocumentResponse]
    metadata: JobMetadata


class JobResponse(BaseModel):
    """Response for a taxonomy generation job."""

    job_id: str = Field(description="Unique job identifier")
    status: JobStatus = Field(description="Current job status")
    created_at: datetime = Field(description="Job creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None, description="When job started running"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When job completed"
    )
    progress: Optional[str] = Field(
        default=None, description="Current progress message"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    result: Optional[TaxonomyResult] = Field(
        default=None, description="Result when completed"
    )


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    jobs: List[JobResponse]
    total: int


class ProgressEvent(BaseModel):
    """Server-Sent Event for progress updates."""

    event: str = Field(description="Event type: progress, completed, error")
    job_id: str
    message: Optional[str] = None
    progress_percent: Optional[float] = None
    result: Optional[TaxonomyResult] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
