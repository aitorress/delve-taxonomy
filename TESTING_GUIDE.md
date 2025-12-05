# Delve Testing Guide

This comprehensive testing guide helps you verify all functionality after the migration. Follow each section step-by-step, running commands in your terminal and checking outputs.

## Important: Activate Your Virtual Environment

**Before running any commands in this guide, activate your virtual environment:**

```bash
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"
source .venv/bin/activate
```

You'll know it's activated when you see `(venv)` or `.venv` in your terminal prompt. Once activated, you can use `delve` commands directly.

**If you open a new terminal, remember to activate again!**

## Table of Contents

1. [Setup & Installation](#1-setup--installation)
2. [Quick Smoke Test](#2-quick-smoke-test)
3. [CSV Data Source Testing](#3-csv-data-source-testing)
4. [JSON Data Source Testing](#4-json-data-source-testing)
5. [DataFrame (SDK) Testing](#5-dataframe-sdk-testing)
6. [SDK Usage Patterns](#6-sdk-usage-patterns)
7. [CLI Advanced Options](#7-cli-advanced-options)
8. [Output File Verification](#8-output-file-verification)
9. [Example Scripts Testing](#9-example-scripts-testing)
10. [Edge Cases & Error Handling](#10-edge-cases--error-handling)
11. [Real-World Scenarios](#11-real-world-scenarios)
12. [Migration Verification](#12-migration-verification)

---

## Quick Start (5-Minute Smoke Test)

Want to verify everything works quickly? Run these commands:

```bash
# Navigate to project directory and activate environment
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"
source .venv/bin/activate

# Verify installation
delve --version

# Navigate to examples
cd examples

# Run quick test
delve run sample_data.csv --text-column text --sample-size 5 --output-dir ./quick_test

# Verify outputs
ls quick_test/
cat quick_test/taxonomy.json | head -20
```

**Note:** If you get "command not found: delve", make sure:
1. You've run the setup (see Section 0 above)
2. You've activated the virtual environment (`source .venv/bin/activate`)

If all these work, you're ready for comprehensive testing!

---

## Prerequisites

Before starting, ensure you have:

- [ ] Python 3.9+ installed
- [ ] Virtual environment set up (see setup instructions below)
- [ ] Project installed: `pip install -e .`
- [ ] Anthropic API key set: `export ANTHROPIC_API_KEY=your-key-here`
- [ ] Terminal access
- [ ] Project directory: `/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator`

---

## 0. Environment Setup (First Time Only)

**Important:** On macOS (and many Linux systems), Python environments are externally managed. This project uses `uv` (a fast Python package installer) for dependency management.

### Using uv (Recommended)

**Step 1: Install uv (if not already installed)**

If you don't have `uv` installed, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your terminal or run:

```bash
source $HOME/.cargo/env
```

**Step 2: Set up the project**

Navigate to the project directory and use the setup script:

```bash
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"
./setup_venv.sh
```

Or set up manually:

```bash
# Navigate to project directory
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"

# Create virtual environment
uv venv

# Install package and dependencies
uv pip install -e .
```

### Verify Installation

After setup, activate your virtual environment and verify everything works:

```bash
source .venv/bin/activate
delve --version
```

**Expected Output:**
```
delve, version 0.1.0
```

- [ ] uv installed
- [ ] Virtual environment created
- [ ] Package installed successfully
- [ ] Virtual environment activated
- [ ] CLI command works

### Using Delve

After setup, activate your virtual environment and use Delve:

```bash
source .venv/bin/activate
delve --version
delve run data.csv --text-column text
```

**For this testing guide, make sure your virtual environment is activated!**

---

## 1. Setup & Installation

### 1.1 Verify Package Installation

Open a terminal and navigate to the project directory:

```bash
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"
```

**Important:** If you haven't set up the environment yet, follow Section 0 above first!

Activate your virtual environment and check if the package is installed:

```bash
source .venv/bin/activate
pip list | grep delve
```

**Expected:** Should show `delve` package in the list

- [ ] Virtual environment activated
- [ ] Package appears in pip list

### 1.2 Verify CLI Command

Test the CLI command:

```bash
delve --version
```

**Expected Output:**
```
delve, version 0.1.0
```

- [ ] Version command works

### 1.3 Verify CLI Help

Test help commands:

```bash
delve --help
```

**Expected:** Should show CLI help with commands

- [ ] Main help works

```bash
delve run --help
```

**Expected:** Should show detailed help for `run` command with all options

- [ ] Run command help works

### 1.4 Verify SDK Import

Open a Python shell:

```bash
python
```

Then run:

```python
from delve import Delve
from delve import DelveResult, TaxonomyCategory, Doc, Configuration
print("✓ All imports successful!")
exit()
```

**Expected:** No errors, imports work

- [ ] SDK imports successfully

### 1.5 Verify Environment Variable

Check if API key is set:

```bash
echo $ANTHROPIC_API_KEY
```

**Expected:** Should show your API key (or be empty if not set)

- [ ] API key environment variable checked

---

## 2. Quick Smoke Test

This is a 5-minute test to verify basic functionality works.

**Important:** Make sure your virtual environment is activated:
```bash
source .venv/bin/activate
```

### 2.1 Test Basic CSV Processing

Navigate to examples directory:

```bash
cd examples
```

Run a quick test with sample data:

```bash
delve run sample_data.csv --text-column text --sample-size 5 --output-dir ./smoke_test_results
```

**Expected:**
- Command runs without errors
- Progress messages appear (if verbose)
- Output directory `smoke_test_results` is created

- [ ] Command completes successfully

### 2.2 Verify Output Files Created

Check if output files exist:

```bash
ls -la smoke_test_results/
```

**Expected Files:**
- `taxonomy.json`
- `labeled_documents.json`
- `labeled_data.csv`
- `taxonomy_reference.csv`
- `report.md`
- `metadata.json`

- [ ] All output files exist

### 2.3 Quick Content Check

Check taxonomy.json:

```bash
cat smoke_test_results/taxonomy.json | head -20
```

**Expected:** Valid JSON with taxonomy structure

- [ ] Taxonomy JSON is valid

Check CSV:

```bash
head -5 smoke_test_results/labeled_data.csv
```

**Expected:** CSV with headers and data rows

- [ ] CSV file has content

---

## 3. CSV Data Source Testing

**Make sure your virtual environment is activated:**
```bash
source .venv/bin/activate
```

Return to examples directory if not already there:

```bash
cd examples
```

### 3.1 Basic CSV with Default Settings

```bash
delve run sample_data.csv --text-column text
```

**Expected:**
- Runs to completion
- Creates `./results` directory (default)
- Shows progress messages

**Verify:**
- [ ] Command completes
- [ ] Output directory created
- [ ] Progress messages shown

Check the results:

```bash
ls -lh results/
```

- [ ] Files are generated

### 3.2 CSV with Custom ID Column

First, check what columns exist in sample_data.csv:

```bash
head -1 sample_data.csv
```

Now run with explicit ID column:

```bash
delve run sample_data.csv --text-column text --id-column id --output-dir ./results_custom_id
```

**Expected:** Should use `id` column for document IDs

**Verify in output:**

```bash
head -3 results_custom_id/labeled_data.csv
```

Check that IDs match the original CSV:

```bash
cut -d',' -f1 sample_data.csv | head -5
cut -d',' -f1 results_custom_id/labeled_data.csv | head -5
```

- [ ] Custom ID column works
- [ ] IDs match original data

### 3.3 CSV with Custom Output Directory

```bash
delve run sample_data.csv --text-column text --output-dir ./my_custom_results
```

**Verify:**

```bash
ls -la my_custom_results/
```

- [ ] Custom directory created
- [ ] Files saved to correct location

### 3.4 CSV with Custom Sample Size

```bash
delve run sample_data.csv --text-column text --sample-size 10 --output-dir ./results_sample10
```

**Expected:** Only 10 documents sampled for taxonomy generation

**Verify:**

Check how many documents were used for taxonomy:

```bash
cat results_sample10/taxonomy.json | grep -o '"document_ids":\[' | wc -l
```

Check total documents labeled:

```bash
wc -l results_sample10/labeled_data.csv
```

- [ ] Sample size respected
- [ ] All documents still labeled (sample_size affects taxonomy, not labeling)

### 3.5 CSV with Multiple Output Formats

Test selecting specific formats:

```bash
delve run sample_data.csv --text-column text \
  --output-format json \
  --output-format csv \
  --output-dir ./results_json_csv_only
```

**Verify only requested formats exist:**

```bash
ls results_json_csv_only/
```

**Expected:** Should have JSON and CSV files, but check if markdown is excluded

- [ ] Only requested formats generated (or all if markdown is always included)

### 3.6 CSV with Quiet Mode

Test quiet output:

```bash
delve run sample_data.csv --text-column text --quiet --output-dir ./results_quiet
```

**Expected:** Minimal output, no progress messages

- [ ] Quiet mode shows minimal output

Compare with verbose (default):

```bash
delve run sample_data.csv --text-column text --verbose --output-dir ./results_verbose
```

- [ ] Verbose mode shows progress

---

## 4. JSON Data Source Testing

**Make sure your virtual environment is activated:**
```bash
source .venv/bin/activate
```

Stay in the examples directory or create test files:

```bash
cd examples
```

### 4.1 Simple JSON Array

Create a test JSON file:

```bash
cat > test_simple.json << 'EOF'
[
  {"id": "1", "text": "How do I reset my password?"},
  {"id": "2", "text": "What are your pricing plans?"},
  {"id": "3", "text": "My app keeps crashing on startup"},
  {"id": "4", "text": "Do you offer enterprise support?"},
  {"id": "5", "text": "I'm getting a 404 error when accessing my dashboard"}
]
EOF
```

Run with JSON source:

```bash
delve run test_simple.json --source-type json --text-column text --output-dir ./results_json
```

**Expected:** Should load JSON and extract text from `text` field

**Verify:**

```bash
cat results_json/taxonomy.json | head -30
```

- [ ] JSON file loaded correctly
- [ ] Text extracted from JSON
- [ ] Taxonomy generated

### 4.2 JSON with JSONPath (Nested Structure)

Create nested JSON:

```bash
cat > test_nested.json << 'EOF'
{
  "conversations": [
    {
      "id": "conv1",
      "messages": [
        {"role": "user", "content": "How do I reset my password?"}
      ]
    },
    {
      "id": "conv2",
      "messages": [
        {"role": "user", "content": "What are your pricing plans?"}
      ]
    },
    {
      "id": "conv3",
      "messages": [
        {"role": "user", "content": "My app keeps crashing on startup"}
      ]
    },
    {
      "id": "conv4",
      "messages": [
        {"role": "user", "content": "Do you offer enterprise support?"}
      ]
    }
  ]
}
EOF
```

Run with JSONPath:

```bash
delve run test_nested.json --json-path "$.conversations[*].messages[0].content" --output-dir ./results_jsonpath
```

**Expected:** Should extract content from nested structure

**Verify:**

Check if documents were created:

```bash
cat results_jsonpath/labeled_data.csv | head -5
```

Check the content matches:

```bash
cat results_jsonpath/labeled_data.csv | cut -d',' -f2
```

- [ ] JSONPath expression works
- [ ] Nested content extracted correctly
- [ ] Documents created from nested data

### 4.3 JSONL File (Newline-Delimited JSON)

Create a JSONL file:

```bash
cat > test.jsonl << 'EOF'
{"id": "1", "text": "How do I reset my password?"}
{"id": "2", "text": "What are your pricing plans?"}
{"id": "3", "text": "My app keeps crashing on startup"}
{"id": "4", "text": "Do you offer enterprise support?"}
{"id": "5", "text": "I'm getting a 404 error"}
EOF
```

Run JSONL:

```bash
delve run test.jsonl --source-type jsonl --text-column text --output-dir ./results_jsonl
```

**Expected:** Each line treated as separate document

**Verify:**

```bash
wc -l test.jsonl
wc -l results_jsonl/labeled_data.csv
```

Should have similar number of documents (CSV will have header + data)

- [ ] JSONL processed correctly
- [ ] Each line treated as document

### 4.4 Cleanup Test Files

```bash
rm test_simple.json test_nested.json test.jsonl
```

- [ ] Test files cleaned up

---

## 5. DataFrame (SDK) Testing

**Make sure your virtual environment is activated:**
```bash
source .venv/bin/activate
```

This section requires Python scripting. Create a test file:

### 5.1 Create DataFrame Test Script

```bash
cat > test_dataframe.py << 'EOF'
"""Test DataFrame functionality with Delve."""

import pandas as pd
from delve import Delve

# Create sample DataFrame
df = pd.DataFrame({
    "id": ["doc1", "doc2", "doc3", "doc4", "doc5"],
    "text": [
        "How do I reset my password?",
        "What are your pricing plans?",
        "My app keeps crashing on startup",
        "Do you offer enterprise support?",
        "I'm getting a 404 error when accessing my dashboard"
    ],
    "metadata": ["support", "sales", "support", "sales", "support"]
})

print("Sample DataFrame:")
print(df)
print()

# Initialize Delve
delve = Delve(
    use_case="Categorize customer inquiries",
    sample_size=50,
    output_dir="./results_dataframe"
)

# Run taxonomy generation
print("Running taxonomy generation...")
result = delve.run_sync(
    df,
    text_column="text",
    id_column="id"
)

# Display results
print(f"\n✓ Generated {len(result.taxonomy)} categories")
for i, category in enumerate(result.taxonomy, 1):
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"\n{i}. {category.name}")
    print(f"   Description: {category.description}")
    print(f"   Documents: {len(category_docs)}")

# Create results DataFrame
results_df = pd.DataFrame([
    {
        "id": doc.id,
        "original_text": doc.content,
        "category": doc.category,
        "explanation": doc.explanation
    }
    for doc in result.labeled_documents
])

print("\n\nResults DataFrame:")
print(results_df)

print("\n\nCategory Distribution:")
print(results_df["category"].value_counts())

print(f"\n✓ Results saved to: ./results_dataframe/")
EOF
```

Run the script:

```bash
python test_dataframe.py
```

**Expected:**
- DataFrame processed successfully
- No temporary CSV files created (in-memory processing)
- Results accessible programmatically

**Verify:**

- [ ] Script runs without errors
- [ ] Taxonomy generated
- [ ] Results accessible from `result` object
- [ ] Results DataFrame created

### 5.2 Verify DataFrame Result Access

Create another test to verify all result properties:

```bash
cat > test_result_access.py << 'EOF'
"""Test accessing all result properties."""

import pandas as pd
from delve import Delve

# Create sample DataFrame
df = pd.DataFrame({
    "id": ["1", "2", "3"],
    "text": ["Question 1", "Question 2", "Question 3"]
})

delve = Delve(sample_size=50, output_dir="./results_access_test")
result = delve.run_sync(df, text_column="text", id_column="id")

# Test taxonomy access
print("=== Taxonomy Access ===")
for category in result.taxonomy:
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"Category: {category.name}")
    print(f"  ID: {category.id}")
    print(f"  Description: {category.description}")
    print(f"  Document count: {len(category_docs)}")
    print()

# Test labeled documents access
print("=== Labeled Documents Access ===")
for doc in result.labeled_documents:
    print(f"ID: {doc.id}")
    print(f"  Category: {doc.category}")
    print(f"  Content: {doc.content[:50]}...")
    print(f"  Explanation: {doc.explanation[:50] if doc.explanation else 'N/A'}...")
    print()

# Test metadata access
print("=== Metadata Access ===")
print(f"Number of documents: {result.metadata.get('num_documents')}")
print(f"Number of categories: {result.metadata.get('num_categories')}")
print()

# Test filtering documents by category
if result.taxonomy:
    first_category = result.taxonomy[0].name
    filtered_docs = [d for d in result.labeled_documents if d.category == first_category]
    print(f"=== Documents in '{first_category}' ===")
    print(f"Count: {len(filtered_docs)}")
    for doc in filtered_docs:
        print(f"  - {doc.id}: {doc.content[:40]}...")

print("\n✓ All result properties accessible!")
EOF
```

Run it:

```bash
python test_result_access.py
```

**Verify:**

- [ ] Can access `result.taxonomy`
- [ ] Can access `result.labeled_documents`
- [ ] Can access `result.metadata`
- [ ] Can filter documents by category
- [ ] All properties have expected data

### 5.3 Cleanup

```bash
rm test_dataframe.py test_result_access.py
```

- [ ] Test scripts cleaned up

---

## 6. SDK Usage Patterns

**Make sure your virtual environment is activated:**
```bash
source .venv/bin/activate
```

### 6.1 Basic SDK - Sync API

Create test script:

```bash
cat > test_sdk_sync.py << 'EOF'
"""Test SDK sync API."""

from delve import Delve

delve = Delve()
result = delve.run_sync(
    "sample_data.csv",
    text_column="text",
    output_dir="./results_sdk_sync"
)

print(f"Generated {len(result.taxonomy)} categories")
for category in result.taxonomy:
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"  - {category.name}: {len(category_docs)} documents")
EOF
```

Run:

```bash
python test_sdk_sync.py
```

**Verify:**

- [ ] Sync API works
- [ ] Results returned correctly
- [ ] Can access taxonomy

### 6.2 Basic SDK - Async API

Create test script:

```bash
cat > test_sdk_async.py << 'EOF'
"""Test SDK async API."""

import asyncio
from delve import Delve

async def main():
    delve = Delve(output_dir="./results_sdk_async")
    result = await delve.run("sample_data.csv", text_column="text")
    print(f"Generated {len(result.taxonomy)} categories")
    for category in result.taxonomy:
        # Get documents for this category
        category_docs = [
            doc for doc in result.labeled_documents
            if doc.category == category.name
        ]
        print(f"  - {category.name}: {len(category_docs)} documents")

asyncio.run(main())
EOF
```

Run:

```bash
python test_sdk_async.py
```

**Verify:**

- [ ] Async API works
- [ ] Results same as sync version

### 6.3 Custom Configuration

Create test script:

```bash
cat > test_sdk_config.py << 'EOF'
"""Test SDK with custom configuration."""

from delve import Delve

delve = Delve(
    model="anthropic/claude-3-5-sonnet-20241022",
    fast_llm="anthropic/claude-3-haiku-20240307",
    sample_size=10,
    batch_size=50,
    use_case="Categorize customer feedback into product areas",
    output_dir="./results_custom_config",
    output_formats=["json", "markdown"],
    verbose=True
)

result = delve.run_sync("sample_data.csv", text_column="text")

print(f"\nConfiguration used:")
print(f"  Model: {delve.config.model}")
print(f"  Sample size: {delve.config.sample_size}")
print(f"  Use case: {delve.config.use_case}")
print(f"\nResults: {len(result.taxonomy)} categories")
EOF
```

Run:

```bash
python test_sdk_config.py
```

**Verify:**

- [ ] All config options work
- [ ] Custom settings applied correctly
- [ ] Output formats match config

### 6.4 Programmatic Result Access

Create test script:

```bash
cat > test_result_filtering.py << 'EOF'
"""Test programmatic result access and filtering."""

from delve import Delve

delve = Delve(sample_size=50, output_dir="./results_filtering")
result = delve.run_sync("sample_data.csv", text_column="text")

# Access taxonomy
print("=== Taxonomy ===")
for category in result.taxonomy:
    # Get documents for this category
    category_docs = [
        doc for doc in result.labeled_documents
        if doc.category == category.name
    ]
    print(f"{category.name}: {len(category_docs)} documents")
    print(f"  Description: {category.description}")
    print()

# Access labeled documents
print("=== Sample Labeled Documents ===")
for doc in result.labeled_documents[:3]:
    print(f"{doc.id}: {doc.category}")
    print(f"  Explanation: {doc.explanation[:60]}...")
    print()

# Filter documents by category
if result.taxonomy:
    first_category = result.taxonomy[0].name
    tech_docs = [
        doc for doc in result.labeled_documents
        if doc.category == first_category
    ]
    print(f"=== Documents in '{first_category}' ===")
    print(f"Total: {len(tech_docs)}")
    for doc in tech_docs[:2]:
        print(f"  - {doc.id}: {doc.content[:50]}...")
EOF
```

Run:

```bash
python test_sdk_config.py
```

**Verify:**

- [ ] Taxonomy iteration works
- [ ] Document access works
- [ ] Filtering by category works

### 6.5 Cleanup

```bash
rm test_sdk_sync.py test_sdk_async.py test_sdk_config.py test_result_filtering.py
```

- [ ] Test scripts cleaned up

---

## 7. CLI Advanced Options

### 7.1 Custom Model

```bash
delve run sample_data.csv --text-column text \
  --model anthropic/claude-3-5-sonnet-20241022 \
  --output-dir ./results_custom_model
```

**Verify:** Check metadata.json for model used:

```bash
cat results_custom_model/metadata.json | grep model
```

- [ ] Custom model setting works

### 7.2 Custom Use Case

```bash
delve run sample_data.csv --text-column text \
  --use-case "Categorize customer support tickets by urgency and type" \
  --output-dir ./results_custom_usecase
```

**Verify:** Check if taxonomy reflects the use case:

```bash
cat results_custom_usecase/report.md | head -30
```

- [ ] Use case influences taxonomy generation

### 7.3 Verbose vs Quiet Mode

Test verbose (default):

```bash
delve run sample_data.csv --text-column text --verbose --output-dir ./results_verbose
```

**Expected:** Progress messages shown

- [ ] Verbose shows progress

Test quiet:

```bash
delve run sample_data.csv --text-column text --quiet --output-dir ./results_quiet2
```

**Expected:** Minimal output

- [ ] Quiet shows minimal output

### 7.4 Custom Batch Size

```bash
delve run sample_data.csv --text-column text \
  --batch-size 10 \
  --output-dir ./results_custom_batch
```

**Verify:** Should process in smaller batches (check progress messages)

- [ ] Custom batch size works

### 7.5 All Options Combined

```bash
delve run sample_data.csv \
  --text-column text \
  --id-column id \
  --model anthropic/claude-3-5-sonnet-20241022 \
  --sample-size 15 \
  --batch-size 5 \
  --use-case "Test all options combined" \
  --output-format json \
  --output-format csv \
  --output-dir ./results_all_options \
  --verbose
```

**Expected:** All options should work together

- [ ] All options work together

---

## 8. Output File Verification

This section verifies the quality and structure of output files.

### 8.1 Check JSON Output Structure

Use one of the previous results directories, e.g.:

```bash
cat results/taxonomy.json | python -m json.tool | head -50
```

**Verify structure:**

```bash
cat > verify_json_structure.sh << 'EOF'
#!/bin/bash
echo "=== Checking taxonomy.json structure ==="

# Check if file exists and is valid JSON
if python -m json.tool results/taxonomy.json > /dev/null 2>&1; then
    echo "✓ Valid JSON"
else
    echo "✗ Invalid JSON"
    exit 1
fi

# Check for taxonomy array
if grep -q '"taxonomy"' results/taxonomy.json; then
    echo "✓ Contains 'taxonomy' field"
else
    echo "✗ Missing 'taxonomy' field"
fi

# Check for metadata
if grep -q '"metadata"' results/taxonomy.json; then
    echo "✓ Contains 'metadata' field"
else
    echo "✗ Missing 'metadata' field"
fi

echo ""
echo "=== Sample taxonomy categories ==="
python -c "import json; data=json.load(open('results/taxonomy.json')); print(f'Number of categories: {len(data.get(\"categories\", []))}'); [print(f\"  - {c.get('name', 'N/A')}: {c.get('description', 'N/A')[:50]}\") for c in data.get('categories', [])[:5]]"
EOF

chmod +x verify_json_structure.sh
./verify_json_structure.sh
```

**Checklist:**

- [ ] File exists and is valid JSON
- [ ] Contains `taxonomy` array
- [ ] Each category has: `id`, `name`, `description`
- [ ] Contains `metadata` section
- [ ] All document IDs referenced exist

### 8.2 Check CSV Outputs

**labeled_data.csv:**

```bash
echo "=== labeled_data.csv ==="
head -5 results/labeled_data.csv
echo ""
echo "Column count:"
head -1 results/labeled_data.csv | tr ',' '\n' | nl
echo ""
echo "Total rows (including header):"
wc -l results/labeled_data.csv
```

**Verify:**

- [ ] File exists
- [ ] Has columns: `id`, `content`, `category`, `explanation`
- [ ] All documents included
- [ ] Categories assigned correctly
- [ ] Explanations present

**taxonomy_reference.csv:**

```bash
echo "=== taxonomy_reference.csv ==="
head -10 results/taxonomy_reference.csv
```

**Verify:**

- [ ] File exists
- [ ] Has category information
- [ ] Can be used as lookup table

### 8.3 Check Markdown Report

```bash
echo "=== report.md preview ==="
head -50 results/report.md
```

**Verify content includes:**

- [ ] Taxonomy overview section
- [ ] Category descriptions
- [ ] Statistics (document counts, etc.)
- [ ] Sample documents per category
- [ ] Human-readable format

```bash
# Check for key sections
grep -E "^(#|##)" results/report.md | head -10
```

### 8.4 Check Metadata File

```bash
echo "=== metadata.json ==="
cat results/metadata.json | python -m json.tool
```

**Verify includes:**

- [ ] Configuration used
- [ ] Timestamps
- [ ] Model information
- [ ] Document counts
- [ ] Sample size and batch size

### 8.5 Output Consistency Check

Check that data is consistent across files:

```bash
cat > verify_consistency.sh << 'EOF'
#!/bin/bash

echo "=== Consistency Check ==="

# Count documents in CSV
csv_docs=$(tail -n +2 results/labeled_data.csv | wc -l)
echo "Documents in labeled_data.csv: $csv_docs"

# Count documents in JSON
json_docs=$(python -c "import json; data=json.load(open('results/labeled_documents.json')); print(len(data))" 2>/dev/null || echo "0")
echo "Documents in labeled_documents.json: $json_docs"

# Count categories
categories=$(python -c "import json; data=json.load(open('results/taxonomy.json')); print(len(data.get('taxonomy', [])))" 2>/dev/null || echo "0")
echo "Categories in taxonomy.json: $categories"

# Check if counts are consistent
if [ "$csv_docs" -eq "$json_docs" ]; then
    echo "✓ Document counts match between CSV and JSON"
else
    echo "✗ Document counts don't match"
fi

# Check category names are consistent
echo ""
echo "Category names in taxonomy.json:"
python -c "import json; data=json.load(open('results/taxonomy.json')); [print(f\"  - {c.get('name')}\") for c in data.get('taxonomy', [])]"

echo ""
echo "Unique categories in labeled_data.csv:"
tail -n +2 results/labeled_data.csv | cut -d',' -f3 | sort | uniq
EOF

chmod +x verify_consistency.sh
./verify_consistency.sh
```

**Verify:**

- [ ] Same document IDs across all output files
- [ ] Category names consistent across formats
- [ ] Document counts match between files
- [ ] Metadata matches actual run configuration

### 8.6 Cleanup Verification Scripts

```bash
rm verify_json_structure.sh verify_consistency.sh
```

- [ ] Verification scripts cleaned up

---

## 9. Example Scripts Testing

Navigate to examples directory:

```bash
cd examples
```

### 9.1 Basic CSV Example

```bash
python basic_csv_example.py
```

**Expected:**
- Script runs without errors
- Creates output directory (`./results`)
- Prints taxonomy categories
- Shows sample labeled documents

**Verify:**

- [ ] Script completes successfully
- [ ] Output directory created
- [ ] Results printed correctly
- [ ] No errors in output

### 9.2 JSON Example

```bash
python json_example.py
```

**Expected:**
- Creates sample JSON file
- Runs taxonomy generation
- Shows results

**Verify:**

- [ ] Script completes successfully
- [ ] JSON file created
- [ ] JSONPath extraction works
- [ ] Results shown

### 9.3 DataFrame Example

```bash
python dataframe_example.py
```

**Expected:**
- Creates DataFrame in-memory
- Processes without file I/O
- Shows category distribution

**Verify:**

- [ ] Script completes successfully
- [ ] DataFrame processed correctly
- [ ] Category distribution shown
- [ ] Results DataFrame created

### 9.4 Advanced Usage Example

```bash
python advanced_usage.py
```

**Expected:**
- Runs all advanced examples
- Async example works
- Large dataset example works
- Statistics shown

**Verify:**

- [ ] All examples in file run
- [ ] Async example works
- [ ] Large dataset example works
- [ ] Programmatic access works
- [ ] Statistics calculated correctly

---

## 10. Edge Cases & Error Handling

### 10.1 Missing Required Parameters

Test CSV without text-column:

```bash
delve run sample_data.csv
```

**Expected:** Error message about missing `--text-column`

- [ ] Clear error message shown
- [ ] Suggests missing parameter

### 10.2 Invalid File Path

```bash
delve run nonexistent_file.csv --text-column text
```

**Expected:** Error about file not found

- [ ] Clear error about file not found

### 10.3 Empty File

Create empty CSV:

```bash
echo "id,text" > empty.csv
```

```bash
delve run empty.csv --text-column text --output-dir ./results_empty
```

**Expected:** Either handles gracefully or shows clear error

- [ ] Handles empty file appropriately

### 10.4 Single Document

Create single document CSV:

```bash
cat > single_doc.csv << 'EOF'
id,text
doc1,This is a single document test
EOF
```

```bash
delve run single_doc.csv --text-column text --output-dir ./results_single
```

**Expected:** Works (may create one category)

- [ ] Single document processed successfully

### 10.5 Very Small Dataset

Create 3-document CSV:

```bash
cat > small_dataset.csv << 'EOF'
id,text
doc1,Question about password reset
doc2,Inquiry about pricing
doc3,Technical support request
EOF
```

```bash
delve run small_dataset.csv --text-column text --output-dir ./results_small
```

**Expected:** Works with small dataset

- [ ] Small dataset processed
- [ ] Taxonomy makes sense for 3 documents

### 10.6 Cleanup Edge Case Files

```bash
rm empty.csv single_doc.csv small_dataset.csv
```

- [ ] Edge case test files cleaned up

---

## 11. Real-World Scenarios

### 11.1 Customer Support Tickets

Create a realistic support tickets CSV:

```bash
cat > support_tickets.csv << 'EOF'
id,text
ticket1,I cannot log into my account. I've tried resetting my password multiple times.
ticket2,The mobile app crashes every time I try to upload a photo.
ticket3,How much does the premium plan cost per month?
ticket4,I need to cancel my subscription and get a refund.
ticket5,The website is loading very slowly today. Is there an outage?
ticket6,Can I upgrade from basic to premium plan?
ticket7,I'm getting error 500 when trying to access my dashboard.
ticket8,Do you offer phone support for enterprise customers?
ticket9,How do I export my data from the platform?
ticket10,My payment failed. How can I update my credit card?
EOF
```

Run with appropriate use case:

```bash
delve run support_tickets.csv \
  --text-column text \
  --use-case "Categorize customer support tickets into: Technical Issues, Billing Questions, Account Management, Product Inquiries" \
  --output-dir ./results_support
```

**Verify taxonomy quality:**

```bash
cat results_support/report.md
```

**Check categories make sense:**

- [ ] Categories match support themes
- [ ] Tickets categorized appropriately
- [ ] Category descriptions are clear

### 11.2 Product Feedback

Create product feedback JSON:

```bash
cat > product_feedback.json << 'EOF'
{
  "feedback": [
    {
      "id": "fb1",
      "comment": "The new dark mode is amazing! Great work on the UI improvements.",
      "product": "mobile_app"
    },
    {
      "id": "fb2",
      "comment": "I wish there was a way to batch delete multiple items at once.",
      "product": "web_app"
    },
    {
      "id": "fb3",
      "comment": "The search functionality is too slow. It takes 5 seconds to return results.",
      "product": "web_app"
    },
    {
      "id": "fb4",
      "comment": "Love the new notification settings! Much more customizable now.",
      "product": "mobile_app"
    },
    {
      "id": "fb5",
      "comment": "Can you add keyboard shortcuts for power users?",
      "product": "web_app"
    }
  ]
}
EOF
```

Run with JSONPath:

```bash
delve run product_feedback.json \
  --json-path "$.feedback[*].comment" \
  --use-case "Categorize product feedback into: Feature Requests, Bug Reports, Positive Feedback, UI/UX Improvements" \
  --output-dir ./results_feedback
```

**Verify:**

- [ ] Feedback categorized appropriately
- [ ] Categories reflect product areas
- [ ] JSONPath extraction works

### 11.3 Large Dataset with Sampling

Create larger dataset (or use existing sample_data.csv):

```bash
delve run sample_data.csv \
  --text-column text \
  --sample-size 10 \
  --use-case "Test sampling functionality with larger dataset" \
  --output-dir ./results_large_sample
```

**Verify:**

- [ ] Only 10 documents sampled for taxonomy
- [ ] All 20 documents (from sample_data.csv) still labeled
- [ ] Sampling works correctly

Check counts:

```bash
echo "Total documents in CSV:"
wc -l sample_data.csv

echo "Documents used for taxonomy (should be ~10):"
cat results_large_sample/metadata.json | python -c "import json, sys; print(json.load(sys.stdin).get('sample_size', 'N/A'))"

echo "Total documents labeled:"
tail -n +2 results_large_sample/labeled_data.csv | wc -l
```

- [ ] Sampling verified

### 11.4 Cleanup Real-World Test Files

```bash
rm support_tickets.csv product_feedback.json
```

- [ ] Real-world test files cleaned up

---

## 12. Migration Verification

### 12.1 Check for Old Code References

Search for old package name:

```bash
cd "/Users/antorres/Documents/Codebases/AI Projects/taxonomy_generator"
grep -r "react_agent" src/ tests/ examples/ --exclude-dir=__pycache__
```

**Expected:** No results (or only in comments/docs)

- [ ] No `react_agent` references in code

### 12.2 Check Import Statements

Verify all imports use `delve`:

```bash
grep -r "^from react_agent" src/ tests/ examples/ 2>/dev/null
grep -r "^import react_agent" src/ tests/ examples/ 2>/dev/null
```

**Expected:** No results

- [ ] All imports use `delve` package

### 12.3 Verify New Features Work

**Multiple Data Sources:**

- [ ] CSV works
- [ ] JSON works
- [ ] DataFrame works
- [ ] LangSmith adapter exists (may not test without API key)

**Multiple Output Formats:**

- [ ] JSON output works
- [ ] CSV output works
- [ ] Markdown output works

**CLI Works Independently:**

- [ ] CLI commands work
- [ ] No dependency on Studio

**SDK Works Programmatically:**

- [ ] Can import and use SDK
- [ ] Both sync and async APIs work

### 12.4 Check for Interactive Code Remnants

Search for interactive/interrupt keywords:

```bash
grep -r "interrupt\|Interrupt\|INTERRUPT" src/ --exclude-dir=__pycache__
grep -r "user_feedback\|UserFeedback" src/ --exclude-dir=__pycache__
grep -r "request_taxonomy_approval" src/ --exclude-dir=__pycache__
```

**Expected:** No results (removed in migration)

- [ ] No interactive/interrupt code remains

### 12.5 Verify Graph is Non-Interactive

Check graph file:

```bash
grep -A 5 "compile\|interrupt" src/delve/graph.py
```

**Expected:** Graph compiles without interrupts

- [ ] Graph is non-interactive

---

## Testing Summary

### Quick Reference Checklist

**Essential Tests (Must Pass):**
- [ ] CLI works: `delve --version`
- [ ] SDK imports: `from delve import Delve`
- [ ] Basic CSV works: `delve run sample_data.csv --text-column text`
- [ ] Example scripts run: All 4 examples complete
- [ ] Output files generated: All 6 file types created

**Data Sources:**
- [ ] CSV processing works
- [ ] JSON processing works
- [ ] JSONPath extraction works
- [ ] DataFrame processing works

**Output Formats:**
- [ ] JSON output valid
- [ ] CSV output valid
- [ ] Markdown report generated

**SDK Features:**
- [ ] Sync API works
- [ ] Async API works
- [ ] Custom configuration works
- [ ] Result objects accessible

**Error Handling:**
- [ ] Missing parameters show errors
- [ ] Invalid files show errors
- [ ] Edge cases handled

---

## Notes & Troubleshooting

### Common Issues

1. **API Key Not Set**
   - Error: Authentication failures
   - Fix: `export ANTHROPIC_API_KEY=your-key`

2. **Import Errors**
   - Error: `ModuleNotFoundError: No module named 'delve'`
   - Fix: `pip install -e .` from project root

3. **File Not Found**
   - Error: CSV/JSON file not found
   - Fix: Check you're in the right directory (`cd examples`)

4. **Permission Errors**
   - Error: Cannot write to output directory
   - Fix: Check directory permissions or use different output-dir

### Tips

- Start with the Quick Smoke Test (Section 2) to verify basics
- Test one data source type at a time
- Keep output directories separate for each test
- Clean up test files when done to avoid confusion

### Test Results Log

Document any issues you find:

```
Date: ___________

Issues Found:
1. 
2. 
3. 

Working Correctly:
- 
- 
- 

Notes:
- 
- 
- 
```

---

## Next Steps After Testing

Once all tests pass:

1. ✅ All functionality verified
2. ✅ Ready for production use
3. ✅ Examples can be shared with users
4. ✅ Documentation confirmed accurate

If issues found:
1. Document issues clearly
2. Fix critical bugs first
3. Re-test after fixes
4. Update documentation if needed

---

**Happy Testing! 🚀**

