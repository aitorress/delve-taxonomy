"""Pydantic models for API request/response schemas."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import IntEnum


class Verbosity(IntEnum):
    """Verbosity levels for processing output."""

    SILENT = 0
    QUIET = 1
    NORMAL = 2
    VERBOSE = 3
    DEBUG = 4


class TaxonomyCategory(BaseModel):
    """A single taxonomy category."""

    id: str = Field(..., description="Unique category identifier")
    name: str = Field(..., description="Human-readable category name")
    description: str = Field(..., description="Detailed description of the category")


class Document(BaseModel):
    """A document for taxonomy processing."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document text content")
    summary: Optional[str] = Field(None, description="Generated summary")
    explanation: Optional[str] = Field(None, description="Explanation for category assignment")
    category: Optional[str] = Field(None, description="Assigned category ID")


class LabeledDocument(Document):
    """A document with category assignment."""

    category: str = Field(..., description="Assigned category ID")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    labeled_by: Optional[str] = Field(None, description="Labeling method: 'llm' or 'classifier'")


class ClassifierMetrics(BaseModel):
    """Classifier performance metrics."""

    train_accuracy: float = Field(..., description="Accuracy on training set")
    test_accuracy: float = Field(..., description="Accuracy on test set")
    train_f1: float = Field(..., description="F1 score on training set")
    test_f1: float = Field(..., description="F1 score on test set")


class RunMetadata(BaseModel):
    """Metadata about a taxonomy generation run."""

    total_documents: int = Field(..., description="Total documents processed")
    sampled_documents: int = Field(..., description="Documents used for taxonomy discovery")
    llm_labeled_count: int = Field(..., description="Documents labeled by LLM")
    classifier_labeled_count: int = Field(..., description="Documents labeled by classifier")
    skipped_document_count: int = Field(0, description="Documents skipped")
    classifier_metrics: Optional[ClassifierMetrics] = Field(None, description="Classifier metrics")
    duration_ms: int = Field(..., description="Processing duration in milliseconds")
    started_at: str = Field(..., description="Start timestamp ISO format")
    completed_at: str = Field(..., description="Completion timestamp ISO format")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class DelveConfig(BaseModel):
    """Configuration for taxonomy generation."""

    model: str = Field(
        "anthropic/claude-sonnet-4-5-20250929",
        description="Main LLM model for taxonomy generation",
    )
    fast_llm: Optional[str] = Field(
        None,
        description="Fast LLM for summarization/labeling (default: claude-haiku-4-5-20251001)",
    )
    sample_size: int = Field(100, ge=1, description="Documents to sample for taxonomy discovery")
    batch_size: int = Field(200, ge=1, description="Batch size for iterative refinement")
    use_case: Optional[str] = Field(None, description="Description of the use case/domain")
    max_num_clusters: int = Field(5, ge=1, le=20, description="Maximum taxonomy categories")
    embedding_model: str = Field(
        "text-embedding-3-large", description="Embedding model for classifier"
    )
    classifier_confidence_threshold: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence threshold for classifier"
    )
    predefined_taxonomy: Optional[List[TaxonomyCategory]] = Field(
        None, description="Predefined taxonomy (skip discovery)"
    )


class GenerateFromArrayRequest(BaseModel):
    """Request to generate taxonomy from array of objects."""

    data: List[Dict[str, Any]] = Field(..., description="Array of data objects")
    text_field: str = Field("text", description="Field containing text content")
    id_field: Optional[str] = Field(None, description="Field containing document IDs")
    config: DelveConfig = Field(default_factory=DelveConfig, description="Generation config")


class GenerateFromDocsRequest(BaseModel):
    """Request to generate taxonomy from pre-formatted documents."""

    documents: List[Document] = Field(..., description="List of documents to process")
    config: DelveConfig = Field(default_factory=DelveConfig, description="Generation config")


class GenerateFromCSVRequest(BaseModel):
    """Request to generate taxonomy from CSV content."""

    csv_content: str = Field(..., description="CSV file content as string")
    text_column: str = Field(..., description="Column containing text content")
    id_column: Optional[str] = Field(None, description="Column containing document IDs")
    delimiter: str = Field(",", description="CSV delimiter")
    config: DelveConfig = Field(default_factory=DelveConfig, description="Generation config")


class GenerateFromJSONRequest(BaseModel):
    """Request to generate taxonomy from JSON content."""

    json_content: str = Field(..., description="JSON or JSONL content as string")
    text_field: str = Field("text", description="Field containing text content")
    id_field: Optional[str] = Field(None, description="Field containing document IDs")
    json_path: Optional[str] = Field(None, description="JSONPath to extract documents")
    config: DelveConfig = Field(default_factory=DelveConfig, description="Generation config")


class DelveResult(BaseModel):
    """Result from taxonomy generation."""

    taxonomy: List[TaxonomyCategory] = Field(..., description="Generated taxonomy categories")
    labeled_documents: List[LabeledDocument] = Field(..., description="All labeled documents")
    metadata: RunMetadata = Field(..., description="Run metadata and statistics")
    config: DelveConfig = Field(..., description="Configuration used")


class LabelDocumentsRequest(BaseModel):
    """Request to label documents with existing taxonomy."""

    documents: List[Document] = Field(..., description="Documents to label")
    taxonomy: List[TaxonomyCategory] = Field(..., description="Taxonomy to use for labeling")
    config: DelveConfig = Field(default_factory=DelveConfig, description="Labeling config")


class LabelDocumentsResult(BaseModel):
    """Result from document labeling."""

    labeled_documents: List[LabeledDocument] = Field(..., description="Labeled documents")
    metadata: Dict[str, Any] = Field(..., description="Labeling metadata")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
