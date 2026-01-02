# Delve Taxonomy REST API

FastAPI-based REST API for the Delve Taxonomy SDK. This API exposes taxonomy generation and document labeling functionality via HTTP endpoints.

## Installation

```bash
# Install dependencies
pip install delve-taxonomy
pip install -r api/requirements.txt

# Or install all at once
pip install delve-taxonomy fastapi uvicorn python-multipart
```

## Quick Start

```bash
# Set API keys
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"  # For classifier embeddings

# Start the server
cd /path/to/delve-taxonomy
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check |
| POST | `/generate/array` | Generate from array of objects |
| POST | `/generate/documents` | Generate from Document objects |
| POST | `/generate/csv` | Generate from CSV content |
| POST | `/generate/json` | Generate from JSON/JSONL content |
| POST | `/generate/file` | Generate from file upload |
| POST | `/label` | Label documents with existing taxonomy |

## Example Usage

### Generate from Array

```bash
curl -X POST "http://localhost:8000/generate/array" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"text": "How do I reset my password?"},
      {"text": "Billing question about invoice"},
      {"text": "Bug: app crashes on startup"}
    ],
    "text_field": "text",
    "config": {
      "max_num_clusters": 5,
      "use_case": "Customer support categorization"
    }
  }'
```

### Generate from File Upload

```bash
curl -X POST "http://localhost:8000/generate/file" \
  -F "file=@data.csv" \
  -F "text_column=message" \
  -F "max_num_clusters=5"
```

### Label Documents with Existing Taxonomy

```bash
curl -X POST "http://localhost:8000/label" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"id": "1", "content": "Need help with subscription"}
    ],
    "taxonomy": [
      {"id": "1", "name": "Support", "description": "Customer support"},
      {"id": "2", "name": "Billing", "description": "Payment questions"}
    ]
  }'
```

## Configuration Options

All generation endpoints accept a `config` object:

```json
{
  "model": "anthropic/claude-sonnet-4-5-20250929",
  "fast_llm": "anthropic/claude-haiku-4-5-20251001",
  "sample_size": 100,
  "batch_size": 200,
  "use_case": "Your use case description",
  "max_num_clusters": 5,
  "embedding_model": "text-embedding-3-large",
  "classifier_confidence_threshold": 0.0,
  "predefined_taxonomy": null
}
```

## Response Format

```json
{
  "taxonomy": [
    {
      "id": "1",
      "name": "Account Issues",
      "description": "Questions about login and account access"
    }
  ],
  "labeled_documents": [
    {
      "id": "doc_1",
      "content": "How do I reset my password?",
      "category": "1",
      "explanation": "User asking about account access"
    }
  ],
  "metadata": {
    "total_documents": 100,
    "duration_ms": 45000,
    "llm_labeled_count": 100,
    "classifier_labeled_count": 0
  },
  "config": {}
}
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install delve-taxonomy fastapi uvicorn python-multipart

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CORS Configuration

Edit `api/main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## License

MIT
