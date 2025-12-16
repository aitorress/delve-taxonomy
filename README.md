# Delve: AI-Powered Taxonomy Generation

Delve is a production-ready SDK and CLI for automatically generating taxonomies from your data using state-of-the-art language models.

📚 **[Read the full documentation →](https://delve.mintlify.app)**

## Quick Start

```bash
# Install
pip install delve-taxonomy

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run (with progress spinners)
delve run data.csv --text-column text

# With progress bars and ETA
delve run data.csv --text-column text -v
```

Or use the Python SDK:

```python
from delve import Delve, Verbosity

# Silent by default (library best practice)
delve = Delve()
result = delve.run_sync("data.csv", text_column="text")

# With progress output
delve = Delve(verbosity=Verbosity.NORMAL)

# Access results
for category in result.taxonomy:
    print(f"- {category.name}: {category.description}")
```

## Features

- **Automated Taxonomy Generation** - No manual category creation using Claude 3.5 Sonnet
- **Multiple Data Sources** - CSV, JSON/JSONL, LangSmith runs, pandas DataFrames
- **Smart Categorization** - Iterative refinement with minibatch clustering
- **Flexible Exports** - JSON, CSV, and Markdown reports

## Requirements

- Python 3.9+
- Anthropic API key

## Documentation

- 📖 [Full Documentation](https://delve.mintlify.app)
- 🚀 [Quickstart Guide](https://delve.mintlify.app/quickstart)
- 💻 [CLI Reference](https://delve.mintlify.app/cli-reference)
- 🐍 [SDK Reference](https://delve.mintlify.app/sdk-reference)
- 📚 [Examples](https://delve.mintlify.app/examples)

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

See the [full documentation](https://delve.mintlify.app) for more details on contributing and development.
