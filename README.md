# Delve: AI-Powered Taxonomy Generation

Delve is a production-ready SDK and CLI for automatically generating taxonomies from your data using state-of-the-art language models.

📚 **[Read the full documentation →](https://wildcampstudio.mintlify.app)**

## Quick Start

### Installation

```bash
pip install delve-taxonomy

# Set API keys
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"  # Required for classifier embeddings
```

### CLI

```bash
# Basic usage (shows progress spinners)
delve run data.csv --text-column text

# With progress bars and ETA
delve run data.csv --text-column text -v

# Quiet mode (errors only)
delve run data.csv --text-column text -q

# JSON with nested data
delve run data.json --json-path "$.messages[*].content"
```

### Python SDK

```python
from delve import Delve, Verbosity

# Initialize client (silent by default - library best practice)
delve = Delve()

# Or with progress output
delve = Delve(verbosity=Verbosity.NORMAL)

# Run taxonomy generation
result = delve.run_sync("data.csv", text_column="text")

# Access results
print(f"Generated {len(result.taxonomy)} categories")
for category in result.taxonomy:
    print(f"  - {category.name}: {category.description}")

# Access labeled documents
for doc in result.labeled_documents[:5]:
    print(f"  [{doc.category}] {doc.content[:50]}...")
```

### JavaScript/TypeScript

For JS/TS projects, deploy the API and use the client:

```typescript
import { Delve } from '@delve/client';

const delve = new Delve({ apiUrl: 'https://your-delve-api.com' });

const result = await delve.generate({
  documents: [
    { content: 'Fix the login bug' },
    { content: 'Add dark mode support' },
  ],
  config: { max_num_clusters: 5 },
});

console.log(result.taxonomy);
```

## Features

- **Automated Taxonomy Generation** - No manual category creation using Claude 3.5 Sonnet
- **Multiple Data Sources** - CSV, JSON/JSONL, LangSmith runs, pandas DataFrames
- **Smart Categorization** - Iterative refinement with minibatch clustering
- **Flexible Exports** - JSON, CSV, and Markdown reports
- **REST API** - Deploy as a service for JavaScript/TypeScript integration

## Deployment

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/delve-taxonomy)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Docker

```bash
# Build and run
docker build -t delve-api .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  delve-api

# Or use docker-compose
docker-compose up
```

### Manual

```bash
# Start the API server
pip install delve-taxonomy
delve serve --host 0.0.0.0 --port 8000
```

Once deployed, install the JavaScript client:

```bash
npm install @delve/client
```

## Requirements

- Python 3.9+
- Anthropic API key (for taxonomy generation)
- OpenAI API key (for classifier embeddings when sample_size > 0)

## Documentation

- 📖 [Full Documentation](https://wildcampstudio.mintlify.app)
- 🚀 [Quickstart Guide](https://wildcampstudio.mintlify.app/quickstart)
- 💻 [CLI Reference](https://wildcampstudio.mintlify.app/cli-reference)
- 🐍 [SDK Reference](https://wildcampstudio.mintlify.app/sdk-reference)
- 📚 [Examples](https://wildcampstudio.mintlify.app/examples)

## Development

```bash
# Install dependencies
uv sync

# Run tests
pytest tests/

# Run linting
ruff check src/

# Format code
ruff format src/
```

### Documentation Development

To work on the documentation locally, you'll need Node.js 20.17+ (for Mintlify):

```bash
# If using nvm, the project includes .nvmrc
nvm use

# Install Mintlify CLI (if not already installed)
npm install -g mintlify

# Run the docs server
cd docs
mintlify dev
```

See the [full documentation](https://wildcampstudio.mintlify.app) for more details on contributing and development.
