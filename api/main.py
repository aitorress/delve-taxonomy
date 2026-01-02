"""Delve Taxonomy REST API - Main application."""

import os
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to path for importing delve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from delve import Delve
from delve.state import Doc
from delve.configuration import Verbosity as DelveVerbosity

from .models import (
    DelveConfig,
    DelveResult,
    Document,
    LabeledDocument,
    TaxonomyCategory,
    RunMetadata,
    ClassifierMetrics,
    GenerateFromArrayRequest,
    GenerateFromDocsRequest,
    GenerateFromCSVRequest,
    GenerateFromJSONRequest,
    LabelDocumentsRequest,
    LabelDocumentsResult,
    HealthResponse,
    ErrorResponse,
)

# API version
API_VERSION = "0.1.0"

# Create FastAPI app
app = FastAPI(
    title="Delve Taxonomy API",
    description="REST API for AI-powered taxonomy generation using LLMs",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_delve_client(config: DelveConfig) -> Delve:
    """Create a Delve client from API config."""
    predefined_taxonomy = None
    if config.predefined_taxonomy:
        predefined_taxonomy = [
            {"id": cat.id, "name": cat.name, "description": cat.description}
            for cat in config.predefined_taxonomy
        ]

    return Delve(
        model=config.model,
        fast_llm=config.fast_llm,
        sample_size=config.sample_size,
        batch_size=config.batch_size,
        use_case=config.use_case or "",
        max_num_clusters=config.max_num_clusters,
        embedding_model=config.embedding_model,
        classifier_confidence_threshold=config.classifier_confidence_threshold,
        predefined_taxonomy=predefined_taxonomy,
        verbosity=DelveVerbosity.SILENT,
    )


def convert_result(result, config: DelveConfig, duration_ms: int) -> DelveResult:
    """Convert Delve SDK result to API response."""
    # Convert taxonomy
    taxonomy = [
        TaxonomyCategory(id=cat.id, name=cat.name, description=cat.description)
        for cat in result.taxonomy
    ]

    # Convert labeled documents
    labeled_docs = []
    for doc in result.labeled_documents:
        labeled_docs.append(
            LabeledDocument(
                id=doc.id,
                content=doc.content,
                summary=doc.summary,
                explanation=doc.explanation,
                category=doc.category or "unknown",
                confidence=None,  # SDK doesn't expose this currently
                labeled_by=None,
            )
        )

    # Build metadata
    metadata = result.metadata
    classifier_metrics = None
    if metadata.get("classifier_metrics"):
        cm = metadata["classifier_metrics"]
        classifier_metrics = ClassifierMetrics(
            train_accuracy=cm.get("train_accuracy", 0),
            test_accuracy=cm.get("test_accuracy", 0),
            train_f1=cm.get("train_f1", 0),
            test_f1=cm.get("test_f1", 0),
        )

    run_metadata = RunMetadata(
        total_documents=metadata.get("total_documents", len(labeled_docs)),
        sampled_documents=metadata.get("sampled_documents", config.sample_size),
        llm_labeled_count=metadata.get("llm_labeled_count", 0),
        classifier_labeled_count=metadata.get("classifier_labeled_count", 0),
        skipped_document_count=metadata.get("skipped_document_count", 0),
        classifier_metrics=classifier_metrics,
        duration_ms=duration_ms,
        started_at=metadata.get("started_at", datetime.now(timezone.utc).isoformat()),
        completed_at=datetime.now(timezone.utc).isoformat(),
        warnings=metadata.get("warnings", []),
    )

    return DelveResult(
        taxonomy=taxonomy,
        labeled_documents=labeled_docs,
        metadata=run_metadata,
        config=config,
    )


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version=API_VERSION)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version=API_VERSION)


@app.post(
    "/generate/array",
    response_model=DelveResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_from_array(request: GenerateFromArrayRequest):
    """Generate taxonomy from an array of data objects.

    This endpoint accepts an array of objects and generates a taxonomy
    based on the text content in each object.
    """
    try:
        start_time = time.time()

        # Convert to Doc objects
        docs: List[Doc] = []
        for i, item in enumerate(request.data):
            text = item.get(request.text_field)
            if not text or not isinstance(text, str) or not text.strip():
                continue

            doc_id = str(item.get(request.id_field, f"doc_{i}")) if request.id_field else f"doc_{i}"
            docs.append(Doc(id=doc_id, content=text.strip()))

        if not docs:
            raise HTTPException(
                status_code=400,
                detail=f"No valid documents found. Ensure objects have a non-empty '{request.text_field}' field.",
            )

        # Create client and run
        client = create_delve_client(request.config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)
        return convert_result(result, request.config, duration_ms)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/generate/documents",
    response_model=DelveResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_from_documents(request: GenerateFromDocsRequest):
    """Generate taxonomy from pre-formatted documents.

    This endpoint accepts documents that already have id and content fields.
    """
    try:
        start_time = time.time()

        # Convert to Doc objects
        docs: List[Doc] = []
        for doc in request.documents:
            if not doc.content or not doc.content.strip():
                continue
            docs.append(Doc(id=doc.id, content=doc.content.strip()))

        if not docs:
            raise HTTPException(status_code=400, detail="No valid documents provided.")

        # Create client and run
        client = create_delve_client(request.config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)
        return convert_result(result, request.config, duration_ms)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/generate/csv",
    response_model=DelveResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_from_csv(request: GenerateFromCSVRequest):
    """Generate taxonomy from CSV content.

    This endpoint accepts CSV content as a string and generates a taxonomy.
    """
    try:
        start_time = time.time()

        # Parse CSV content
        import csv
        from io import StringIO

        reader = csv.DictReader(
            StringIO(request.csv_content), delimiter=request.delimiter
        )

        docs: List[Doc] = []
        for i, row in enumerate(reader):
            text = row.get(request.text_column)
            if not text or not text.strip():
                continue

            doc_id = row.get(request.id_column, f"doc_{i}") if request.id_column else f"doc_{i}"
            docs.append(Doc(id=str(doc_id), content=text.strip()))

        if not docs:
            raise HTTPException(
                status_code=400,
                detail=f"No valid documents found. Ensure CSV has a non-empty '{request.text_column}' column.",
            )

        # Create client and run
        client = create_delve_client(request.config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)
        return convert_result(result, request.config, duration_ms)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/generate/json",
    response_model=DelveResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_from_json(request: GenerateFromJSONRequest):
    """Generate taxonomy from JSON or JSONL content.

    This endpoint accepts JSON array or JSONL content and generates a taxonomy.
    """
    try:
        import json

        start_time = time.time()

        # Parse JSON content
        content = request.json_content.strip()
        records: List[Dict[str, Any]] = []

        if content.startswith("["):
            # JSON array
            data = json.loads(content)
            if request.json_path:
                # Simple JSONPath support
                records = _evaluate_json_path(data, request.json_path)
            else:
                records = data
        elif content.startswith("{"):
            # Could be JSONL or single object
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        else:
            raise HTTPException(status_code=400, detail="Invalid JSON content")

        # Convert to Doc objects
        docs: List[Doc] = []
        for i, item in enumerate(records):
            text = _get_nested_value(item, request.text_field)
            if not text or not isinstance(text, str) or not text.strip():
                continue

            doc_id = str(_get_nested_value(item, request.id_field) or f"doc_{i}")
            docs.append(Doc(id=doc_id, content=text.strip()))

        if not docs:
            raise HTTPException(
                status_code=400,
                detail=f"No valid documents found. Ensure objects have a non-empty '{request.text_field}' field.",
            )

        # Create client and run
        client = create_delve_client(request.config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)
        return convert_result(result, request.config, duration_ms)

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/generate/file",
    response_model=DelveResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_from_file(
    file: UploadFile = File(...),
    text_column: str = Form(...),
    id_column: str = Form(None),
    model: str = Form("anthropic/claude-sonnet-4-5-20250929"),
    sample_size: int = Form(100),
    batch_size: int = Form(200),
    max_num_clusters: int = Form(5),
    use_case: str = Form(None),
):
    """Generate taxonomy from uploaded file.

    Supports CSV, JSON, and JSONL files.
    """
    try:
        start_time = time.time()

        content = await file.read()
        content_str = content.decode("utf-8")

        config = DelveConfig(
            model=model,
            sample_size=sample_size,
            batch_size=batch_size,
            max_num_clusters=max_num_clusters,
            use_case=use_case,
        )

        # Determine file type and parse
        filename = file.filename or ""
        docs: List[Doc] = []

        if filename.endswith(".csv"):
            import csv
            from io import StringIO

            reader = csv.DictReader(StringIO(content_str))
            for i, row in enumerate(reader):
                text = row.get(text_column)
                if not text or not text.strip():
                    continue
                doc_id = row.get(id_column, f"doc_{i}") if id_column else f"doc_{i}"
                docs.append(Doc(id=str(doc_id), content=text.strip()))

        elif filename.endswith(".json") or filename.endswith(".jsonl"):
            import json

            if content_str.strip().startswith("["):
                records = json.loads(content_str)
            else:
                records = [json.loads(line) for line in content_str.strip().split("\n") if line.strip()]

            for i, item in enumerate(records):
                text = item.get(text_column)
                if not text or not isinstance(text, str) or not text.strip():
                    continue
                doc_id = str(item.get(id_column, f"doc_{i}")) if id_column else f"doc_{i}"
                docs.append(Doc(id=doc_id, content=text.strip()))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use .csv, .json, or .jsonl",
            )

        if not docs:
            raise HTTPException(
                status_code=400,
                detail=f"No valid documents found. Ensure file has a non-empty '{text_column}' column/field.",
            )

        # Create client and run
        client = create_delve_client(config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)
        return convert_result(result, config, duration_ms)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/label",
    response_model=LabelDocumentsResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def label_documents(request: LabelDocumentsRequest):
    """Label documents using an existing taxonomy.

    This endpoint labels documents without generating a new taxonomy.
    Uses the predefined_taxonomy config option.
    """
    try:
        start_time = time.time()

        # Set up config with predefined taxonomy
        config = request.config.model_copy()
        config.predefined_taxonomy = request.taxonomy

        # Convert to Doc objects
        docs: List[Doc] = []
        for doc in request.documents:
            if not doc.content or not doc.content.strip():
                continue
            docs.append(Doc(id=doc.id, content=doc.content.strip()))

        if not docs:
            raise HTTPException(status_code=400, detail="No valid documents provided.")

        # Create client and run
        client = create_delve_client(config)
        result = client.run_with_docs_sync(docs)

        duration_ms = int((time.time() - start_time) * 1000)

        # Convert labeled documents
        labeled_docs = []
        for doc in result.labeled_documents:
            labeled_docs.append(
                LabeledDocument(
                    id=doc.id,
                    content=doc.content,
                    summary=doc.summary,
                    explanation=doc.explanation,
                    category=doc.category or "unknown",
                )
            )

        return LabelDocumentsResult(
            labeled_documents=labeled_docs,
            metadata={
                "total_documents": len(labeled_docs),
                "duration_ms": duration_ms,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_nested_value(obj: Dict[str, Any], path: str) -> Any:
    """Get nested value from dict using dot notation."""
    if not path:
        return None
    parts = path.split(".")
    current = obj
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def _evaluate_json_path(data: Any, path: str) -> List[Dict[str, Any]]:
    """Simple JSONPath evaluator."""
    parts = path.replace("$.", "").replace("$", "").split(".")
    current = data
    for part in parts:
        if part == "[*]" or part == "*":
            if isinstance(current, list):
                continue
            else:
                return []
        elif part.endswith("[*]"):
            key = part[:-3]
            if isinstance(current, dict):
                current = current.get(key, [])
        elif part.endswith("]"):
            # Array index
            import re

            match = re.match(r"(.+)\[(\d+)\]", part)
            if match:
                key, idx = match.groups()
                current = current.get(key, [])
                if isinstance(current, list) and int(idx) < len(current):
                    current = current[int(idx)]
        else:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                current = [item.get(part) if isinstance(item, dict) else None for item in current]

    if isinstance(current, list):
        return [item for item in current if isinstance(item, dict)]
    return []


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
