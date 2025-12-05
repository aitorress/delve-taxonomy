# Delve: AI-Powered Taxonomy Generation

Delve is a production-ready SDK and CLI for automatically generating taxonomies from your data using state-of-the-art language models. It analyzes your documents, identifies patterns, and creates a structured taxonomy with automatic categorization.

## Features

- **Multiple Data Sources**: CSV, JSON/JSONL, LangSmith runs, pandas DataFrames
- **Automated Taxonomy Generation**: Iterative minibatch-based clustering using Claude 3.5 Sonnet
- **Multiple Output Formats**: JSON, CSV, and Markdown reports
- **Both SDK and CLI**: Use programmatically or from command line
- **Smart Sampling**: Automatically samples large datasets for efficient processing
- **Quality Review**: Built-in LLM-based taxonomy validation
- **Progress Tracking**: Real-time feedback during processing

## Installation

### From PyPI (when published)

```bash
pip install delve
```

### From Source

This project uses [`uv`](https://github.com/astral-sh/uv) for fast and reliable dependency management.

**Option 1: Using uv (Recommended)**

First, install `uv` if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then set up the project:

```bash
git clone <repository-url>
cd taxonomy_generator
uv venv
uv pip install -e .
```

**Option 2: Using standard pip**

```bash
git clone <repository-url>
cd taxonomy_generator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Using Delve

**With uv (no activation needed):**
```bash
uv run delve --version
uv run delve run data.csv --text-column text
```

**With activated virtual environment:**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
delve --version
delve run data.csv --text-column text
```

### Requirements

- Python 3.9+
- Anthropic API key (set as `ANTHROPIC_API_KEY` environment variable)
- Optional: LangSmith API key for LangSmith data sources

## Quick Start

### CLI Usage

```bash
# Basic CSV usage
delve run data.csv --text-column conversation

# JSON with JSONPath
delve run data.json --json-path "$.messages[*].content"

# LangSmith source
delve run langsmith://my-project \
  --langsmith-key $LANGSMITH_API_KEY \
  --days 7

# Custom configuration
delve run data.csv \
  --text-column text \
  --model anthropic/claude-3-5-sonnet-20241022 \
  --sample-size 200 \
  --output-dir ./my_results
```

### SDK Usage

```python
from delve import Delve

# Initialize client
delve = Delve(
    model="anthropic/claude-3-5-sonnet-20241022",
    sample_size=100,
    output_dir="./results"
)

# Run on CSV file
result = delve.run_sync(
    "data.csv",
    text_column="conversation"
)

# Access results
print(f"Generated {len(result.taxonomy)} categories")
for category in result.taxonomy:
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"  - {category.name}: {category.description}")
    print(f"    Documents: {len(category_docs)}")

# Access labeled documents
for doc in result.labeled_documents:
    print(f"Doc {doc.id}: {doc.category}")
```

### Using with pandas DataFrame

```python
import pandas as pd
from delve import Delve

# Load your data
df = pd.read_csv("data.csv")

# Run taxonomy generation
delve = Delve(sample_size=150)
result = delve.run_sync(
    df,
    text_column="text",
    id_column="id"
)

# Results are available immediately
print(result.taxonomy)
```

### Using with JSON data

```python
from delve import Delve

delve = Delve()

# Simple JSON with text field
result = delve.run_sync(
    "data.json",
    text_field="content"
)

# Nested JSON with JSONPath
result = delve.run_sync(
    "data.json",
    json_path="$.messages[*].content"
)
```

## Configuration Options

### SDK Configuration

```python
Delve(
    model="anthropic/claude-3-5-sonnet-20241022",  # Main reasoning model
    fast_llm="anthropic/claude-3-haiku-20240307",  # Fast summarization model
    sample_size=100,                                # Docs to sample for taxonomy
    batch_size=200,                                 # Minibatch size
    use_case="Categorize customer support tickets", # Custom use case
    output_dir="./results",                         # Output directory
    output_formats=["json", "csv", "markdown"],     # Output formats
    verbose=True                                    # Progress logging
)
```

### CLI Options

```bash
delve run DATA_SOURCE [OPTIONS]

Options:
  --text-column TEXT              Column containing text data (CSV/tabular)
  --id-column TEXT                Column for document IDs (optional)
  --json-path TEXT                JSONPath expression for nested JSON
  --source-type [csv|json|jsonl|langsmith|auto]
  --model TEXT                    Main LLM model (default: claude-3-5-sonnet)
  --fast-llm TEXT                 Fast LLM (default: claude-3-haiku)
  --sample-size INTEGER           Sample size (default: 100)
  --batch-size INTEGER            Batch size (default: 200)
  --output-dir PATH               Output directory (default: ./results)
  --output-format [json|csv|markdown]  Multiple formats supported
  --use-case TEXT                 Description of taxonomy use case
  --langsmith-key TEXT            LangSmith API key
  --days INTEGER                  Days to look back (LangSmith)
  --verbose / --quiet             Enable/disable progress output
```

## Output Files

Delve generates multiple output files in your specified output directory:

```
results/
├── taxonomy.json              # Machine-readable taxonomy with metadata
├── labeled_documents.json     # All documents with assigned categories
├── labeled_data.csv          # Spreadsheet format with categories
├── taxonomy_reference.csv    # Category lookup table
├── report.md                 # Human-readable summary with statistics
└── metadata.json             # Run configuration and metadata
```

### taxonomy.json

```json
{
  "taxonomy": [
    {
      "id": "1",
      "name": "Technical Support",
      "description": "Questions about technical issues and troubleshooting"
    }
  ],
  "metadata": {
    "num_documents": 100,
    "num_categories": 5,
    "model": "anthropic/claude-3-5-sonnet-20241022"
  }
}
```

### labeled_data.csv

```csv
id,content,category,explanation
doc1,"How do I reset my password?","Technical Support","User asking about account recovery"
doc2,"What are your pricing plans?","Sales Inquiry","Question about product pricing"
```

### report.md

Human-readable Markdown report with:
- Taxonomy overview
- Category descriptions
- Document distribution statistics
- Sample documents per category

## Data Source Examples

### CSV Files

```bash
# CSV with text column
delve run conversations.csv --text-column message

# CSV with custom ID column
delve run data.csv --text-column text --id-column conversation_id
```

### JSON/JSONL Files

```bash
# Simple JSON array
delve run data.json --source-type json

# Nested JSON with JSONPath
delve run messages.json --json-path "$.conversations[*].text"

# JSONL (newline-delimited JSON)
delve run data.jsonl --source-type jsonl
```

### LangSmith Projects

```bash
# Recent runs from project
delve run langsmith://my-project \
  --langsmith-key $LANGSMITH_API_KEY \
  --days 7

# With custom filters
delve run langsmith://my-project \
  --langsmith-key $LANGSMITH_API_KEY \
  --days 14 \
  --sample-size 200
```

## How It Works

Delve uses a sophisticated multi-stage pipeline powered by LangGraph:

1. **Data Loading**: Adapters load data from various sources (CSV, JSON, LangSmith, DataFrame)
2. **Summarization**: Fast LLM generates concise summaries of each document
3. **Minibatch Generation**: Documents are grouped into minibatches for efficient processing
4. **Iterative Clustering**: Each minibatch is analyzed to generate category candidates
5. **Taxonomy Update**: Categories are merged, refined, and consolidated
6. **Quality Review**: LLM validates taxonomy quality and completeness
7. **Document Labeling**: All documents are categorized with explanations
8. **Export**: Results saved in multiple formats (JSON, CSV, Markdown)

## Advanced Usage

### Async API

```python
import asyncio
from delve import Delve

async def main():
    delve = Delve()
    result = await delve.run(
        "data.csv",
        text_column="text"
    )
    print(result.taxonomy)

asyncio.run(main())
```

### Custom Use Cases

```python
delve = Delve(
    use_case="Categorize customer feedback into product areas and sentiment"
)
result = delve.run_sync("feedback.csv", text_column="comment")
```

### Processing Large Datasets

```python
# Sample 300 documents from large dataset
delve = Delve(sample_size=300, batch_size=50)
result = delve.run_sync("large_dataset.csv", text_column="text")
```

### Programmatic Access to Results

```python
result = delve.run_sync("data.csv", text_column="text")

# Access taxonomy
for category in result.taxonomy:
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"{category.name}: {len(category_docs)} documents")
    print(f"  Description: {category.description}")

# Access labeled documents
for doc in result.labeled_documents:
    print(f"{doc.id}: {doc.category}")
    print(f"  Explanation: {doc.explanation}")

# Get documents by category
tech_support = [
    doc for doc in result.labeled_documents
    if doc.category == "Technical Support"
]
```

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for Claude models
- `LANGSMITH_API_KEY`: Optional, for LangSmith data sources
- `LITELLM_LOG`: Set to `DEBUG` for detailed LLM logging

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/delve

# Format code
ruff format src/
```

## Roadmap

Future enhancements planned:

- **v0.2.0**: Optional iterative mode with human feedback, confidence scores
- **v0.3.0**: Hierarchical taxonomies, custom prompts, fine-tuned models
- **v0.4.0**: S3/database adapters, REST API server
- **v0.5.0**: Web UI, visualization tools, annotation interfaces

## Architecture

Built on:
- **LangGraph**: State-based workflow orchestration
- **LangChain**: LLM abstraction and prompt management
- **Claude 3.5 Sonnet**: Advanced reasoning for taxonomy generation
- **Claude 3 Haiku**: Fast document summarization
- **Click**: CLI framework
- **Pandas**: Data manipulation

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Your license here]

## Citation

If you use Delve in your research, please cite:

```bibtex
@software{delve2024,
  title={Delve: AI-Powered Taxonomy Generation},
  author={[Your name]},
  year={2024},
  url={[Repository URL]}
}
```

## Support

- Documentation: [Link to docs]
- Issues: [GitHub Issues]
- Discussions: [GitHub Discussions]

## Acknowledgments

Built with LangChain and LangGraph by Anthropic.
