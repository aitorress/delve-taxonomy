# Delve Examples

This directory contains working examples demonstrating various use cases of Delve.

## Available Examples

### 1. basic_csv_example.py

Simple CSV file processing with default settings.

```bash
cd examples
python basic_csv_example.py
```

**Demonstrates:**
- Basic Delve initialization
- Processing CSV files
- Accessing taxonomy results
- Viewing labeled documents

### 2. json_example.py

Processing JSON data with JSONPath expressions for nested structures.

```bash
python json_example.py
```

**Demonstrates:**
- JSON/JSONL file support
- JSONPath for nested data extraction
- Custom output directories

### 3. dataframe_example.py

Using Delve with pandas DataFrames for in-memory processing.

```bash
python dataframe_example.py
```

**Demonstrates:**
- Direct DataFrame processing
- Custom use cases
- Creating results DataFrames
- Category distribution analysis

### 4. advanced_usage.py

Advanced features and customization options.

```bash
python advanced_usage.py
```

**Demonstrates:**
- Async API usage
- Custom configuration (models, batch sizes, use cases)
- Programmatic result access
- Large dataset processing
- Statistics and analysis

## Sample Data

The `sample_data.csv` file contains 20 sample customer inquiries for testing. Topics include:
- Technical support issues
- Billing and pricing questions
- Account management
- Feature requests

## Requirements

Before running the examples, ensure you have:

1. Set up the project (from project root):
   ```bash
   # Using uv (recommended)
   uv venv
   uv pip install -e .
   
   # Or using standard pip
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your-api-key
   ```

## Running Examples

You can run examples in two ways:

**Option 1: Using `uv run` (no activation needed)**
```bash
cd examples
uv run python basic_csv_example.py
```

**Option 2: With activated virtual environment**
```bash
cd examples
source ../.venv/bin/activate  # or: source ../venv/bin/activate
python basic_csv_example.py
```

## Output

Each example creates its own output directory with results in multiple formats:
- `taxonomy.json` - Machine-readable taxonomy
- `labeled_documents.json` - Categorized documents
- `labeled_data.csv` - Spreadsheet format
- `report.md` - Human-readable summary

## Modifying Examples

Feel free to modify these examples:
- Change the sample data in `sample_data.csv`
- Adjust configuration parameters (sample_size, batch_size, etc.)
- Try different models or use cases
- Add your own data sources

## CLI Examples

You can also use the CLI to run taxonomy generation:

**Using `uv run` (no activation needed):**
```bash
# Basic CSV
uv run delve run sample_data.csv --text-column text

# With custom configuration
uv run delve run sample_data.csv \
  --text-column text \
  --sample-size 50 \
  --output-dir ./cli_results
```

**Or with activated virtual environment:**
```bash
source ../.venv/bin/activate  # From examples directory
delve run sample_data.csv --text-column text
```

## Next Steps

After running these examples, try:
1. Using your own data files
2. Experimenting with different sample sizes
3. Customizing use cases for your domain
4. Integrating Delve into your applications
