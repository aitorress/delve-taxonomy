# Delve: Production SDK/CLI Implementation Plan

## Overview

Transform the `taxonomy_generator` project into **Delve** - a production-ready SDK/CLI for AI-powered taxonomy generation that supports multiple data sources (CSV, JSON, LangSmith, DataFrames) and outputs (JSON, CSV, Markdown).

**Key Changes:**
- Package rename: `react-agent` → `delve`
- Mode: Interactive → Non-interactive (automated)
- Interface: LangGraph Studio → SDK + CLI
- Data sources: LangSmith only → CSV, JSON, LangSmith, DataFrames
- Compatibility: Breaking backward compatibility for clean design

## Project Structure

```
delve/
├── src/delve/                      # Renamed from react_agent
│   ├── __init__.py                 # Public API exports (Delve, DelveResult)
│   ├── client.py                   # NEW: Main Delve SDK class
│   ├── result.py                   # NEW: Result objects
│   ├── configuration.py            # Modified: Add output_dir, output_formats
│   ├── state.py                    # Modified: Remove interactive fields
│   ├── graph.py                    # Modified: Non-interactive graph
│   ├── prompts.py                  # Keep (remove FEEDBACK_PROMPT)
│   ├── utils.py                    # Modified: Remove LangSmith-specific code
│   │
│   ├── core/                       # Refactored processing nodes
│   │   ├── data_loader.py          # NEW: Generic data loading node
│   │   ├── summarizer.py           # From summary_generator.py
│   │   ├── batch_generator.py      # From minibatches_generator.py
│   │   ├── taxonomy_generator.py   # Keep with modifications
│   │   ├── taxonomy_updater.py     # Keep with modifications
│   │   ├── taxonomy_reviewer.py    # Keep as-is
│   │   ├── document_labeler.py     # From doc_labeler.py
│   │   └── results_saver.py        # NEW: Save results node
│   │
│   ├── adapters/                   # NEW: Data source adapters
│   │   ├── base.py                 # DataSource abstract class
│   │   ├── csv_adapter.py          # CSV file support
│   │   ├── json_adapter.py         # JSON/JSONL support
│   │   ├── langsmith_adapter.py    # From runs_retriever.py
│   │   └── dataframe_adapter.py    # Pandas DataFrame support
│   │
│   ├── exporters/                  # NEW: Output generation
│   │   ├── base.py                 # Exporter abstract class
│   │   ├── json_exporter.py        # JSON output
│   │   ├── csv_exporter.py         # CSV output
│   │   ├── markdown_exporter.py    # Markdown report
│   │   └── metadata_exporter.py    # Metadata JSON
│   │
│   └── cli/                        # NEW: CLI implementation
│       ├── main.py                 # CLI entry point (Click)
│       └── utils.py                # CLI helpers
│
└── pyproject.toml                  # Updated: Rename, add CLI entry, fix deps
```

**Files to Delete:**
- `src/react_agent/nodes/taxonomy_approval.py` (interactive node)
- `src/react_agent/routing.py` (interactive routing)
- `langgraph.json` (LangGraph Studio config)
- `static/` directory (Studio assets)

## Graph Transformation

**Current Flow:**
```
get_runs → summarize → get_minibatches → generate_taxonomy
→ update_taxonomy (loop) → review_taxonomy → request_taxonomy_approval
→ handle_user_feedback (INTERRUPT) → label_documents → END
```

**New Non-Interactive Flow:**
```
load_data → summarize → get_minibatches → generate_taxonomy
→ update_taxonomy (loop) → review_taxonomy → label_documents
→ save_results → END
```

**Changes:**
1. ✅ **Keep**: `review_taxonomy` (LLM quality check, not human approval)
2. ❌ **Remove**: `request_taxonomy_approval`, `handle_user_feedback`
3. ❌ **Remove**: Interrupt configuration (`interrupt_before=["handle_user_feedback"]`)
4. 🔄 **Replace**: `get_runs` → `load_data` (adapter-based)
5. ➕ **Add**: `save_results` (multi-format export)

## API Design

### SDK Usage

```python
from delve import Delve

# Initialize with configuration
delve = Delve(
    model="anthropic/claude-3-5-sonnet-20241022",
    sample_size=100,
    output_dir="./results"
)

# Run on CSV
result = delve.run_sync(
    "data.csv",
    text_column="conversation"
)

# Access results
print(f"Generated {len(result.taxonomy)} categories")
for category in result.taxonomy:
    print(f"  - {category.name}: {category.description}")
```

### CLI Usage

```bash
# Basic CSV
delve run data.csv --text-column conversation

# JSON with JSONPath
delve run data.json --json-path "$.messages[*].content"

# LangSmith
delve run langsmith://my-project \
  --langsmith-key $LANGSMITH_API_KEY \
  --days 7

# Custom configuration
delve run data.csv \
  --text-column text \
  --model claude-3-5-sonnet-20241022 \
  --sample-size 200 \
  --output-dir ./output
```

## Implementation Phases

### Phase 1: Foundation (Days 1-2)

**1.1 Project Rename & Setup**
- Create `src/delve/` directory
- Update `pyproject.toml`:
  - Package name: `delve`
  - Version: `0.1.0`
  - **FIX**: Add missing `langsmith>=0.1.0` dependency
  - Add: `click`, `pandas`, `jsonpath-ng`, `rich`
  - Add CLI entry point: `delve = "delve.cli.main:cli"`
- Test: `pip install -e .`

**1.2 Core State & Configuration**
- Modify `state.py`:
  - Remove: `UserFeedback` class, `messages` field, `user_feedback` field
  - Keep: `Doc`, `InputState`, `OutputState`, `State` structure
- Modify `configuration.py`:
  - Remove: `max_runs` (LangSmith-specific)
  - Add: `output_formats`, `output_dir`, `verbose`, `use_case`
  - Add: `to_dict()` method for SDK usage

**1.3 Result Objects**
- Create `result.py`:
  - `TaxonomyCategory` dataclass
  - `DelveResult` dataclass with `from_state()` method
  - `to_dict()`, `export()` methods

**Critical Files:**
- `pyproject.toml`
- `src/react_agent/state.py`
- `src/react_agent/configuration.py`

### Phase 2: Data Adapters (Days 3-4)

**2.1 Adapter Architecture**
- Create `adapters/base.py`:
  - `DataSourceConfig` dataclass
  - `DataSource` abstract class with `load()` and `validate()` methods
- Create `adapters/csv_adapter.py`:
  - Read CSV with pandas
  - Support `text_column` and optional `id_column`
  - Generate UUIDs if no ID column

**2.2 Additional Adapters**
- Create `adapters/json_adapter.py`:
  - Support JSON and JSONL formats
  - JSONPath expressions for nested data
- Refactor `runs_retriever.py` → `adapters/langsmith_adapter.py`:
  - Keep `run_to_doc()` transformation logic
  - Implement `DataSource` interface
- Create `adapters/dataframe_adapter.py`:
  - In-memory DataFrame support for SDK

**2.3 Adapter Factory**
- Create `adapters/__init__.py`:
  - `create_adapter()` factory with auto-detection
  - Based on file extension, URI scheme, or explicit type

**Critical Files:**
- `src/react_agent/nodes/runs_retriever.py` (to refactor)
- `src/react_agent/utils.py` (contains run_to_doc)

### Phase 3: Core Processing (Days 5-6)

**3.1 Refactor Nodes**
- Create `core/` directory
- Refactor existing nodes:
  - `core/data_loader.py` - Generic node using adapters
  - `core/summarizer.py` - From `summary_generator.py`
  - `core/batch_generator.py` - From `minibatches_generator.py`
  - `core/taxonomy_generator.py` - Minimal changes
  - `core/taxonomy_updater.py` - Minimal changes
  - `core/taxonomy_reviewer.py` - Keep as-is
  - `core/document_labeler.py` - From `doc_labeler.py`

**3.2 Update Utilities**
- Modify `utils.py`:
  - Keep: `to_xml()`, `format_docs()`, `parse_taxa()`, `load_chat_model()`
  - Move: `run_to_doc()` to LangSmith adapter
  - Remove: `process_runs()` (adapter-specific now)
- Modify `prompts.py`:
  - Remove: `FEEDBACK_PROMPT` only

### Phase 4: Graph Reconstruction (Days 7-8)

**4.1 Build Non-Interactive Graph**
- Modify `graph.py`:
  - Replace `get_runs` with `load_data` node
  - Remove `request_taxonomy_approval` node
  - Remove `handle_user_feedback` node
  - Remove `interrupt_before=["handle_user_feedback"]`
  - Remove feedback conditional edges (lines 57-64)
  - Update imports (remove routing)

**4.2 Add Results Saving**
- Create `core/results_saver.py`:
  - Node that calls all configured exporters
  - Saves to `output_dir`
- Add `save_results` node to graph
- Wire: `label_documents` → `save_results` → `END`

**Critical Files:**
- `src/react_agent/graph.py`

### Phase 5: Output Generation (Days 9-10)

**5.1 Implement Exporters**
- Create `exporters/base.py` - Abstract `Exporter` class
- Create `exporters/json_exporter.py`:
  - `taxonomy.json` - Taxonomy with metadata
  - `labeled_documents.json` - Documents with categories
- Create `exporters/csv_exporter.py`:
  - `labeled_data.csv` - Spreadsheet format
  - `taxonomy_reference.csv` - Category reference
- Create `exporters/markdown_exporter.py`:
  - `report.md` - Human-readable summary with statistics
- Create `exporters/metadata_exporter.py`:
  - `metadata.json` - Run configuration and stats

**5.2 Exporter Registry**
- Create `exporters/__init__.py`:
  - `get_exporters()` function returning registry
  - Wire into `save_results` node

### Phase 6: SDK API (Days 11-12)

**6.1 SDK Client**
- Create `client.py`:
  - `Delve` class with `__init__` accepting config parameters
  - `async run()` method - main entry point
  - `run_sync()` wrapper for simple usage
  - Orchestrates: adapter creation → graph execution → result export

**6.2 Public API**
- Update `__init__.py`:
  - Export: `Delve`, `DelveResult`, `TaxonomyCategory`, `Configuration`, `Doc`
  - Set `__version__ = "0.1.0"`

**6.3 Integration Tests**
- Test CSV workflow end-to-end
- Test JSON workflow end-to-end
- Test with mock LangSmith data
- Test DataFrame workflow

### Phase 7: CLI (Days 13-14)

**7.1 CLI Foundation**
- Create `cli/main.py` using Click:
  - `cli()` group with version
  - `run` command with all options
  - Arguments: `data_source`
  - Options: `--text-column`, `--json-path`, `--model`, `--sample-size`, `--output-dir`, etc.

**7.2 CLI Enhancements**
- Create `cli/utils.py`:
  - `setup_logging()`, `print_progress()`, `validate_file()`
  - `detect_source_type()` for auto-detection
- Add progress reporting
- Add colored output
- Test all CLI options

### Phase 8: Documentation & Polish (Days 15-16)

**8.1 Documentation**
- Comprehensive README.md:
  - Installation (pip install, from source)
  - Quick start (SDK and CLI)
  - Configuration reference
  - Examples
- Add docstrings to all public APIs
- Create CHANGELOG.md for v0.1.0
- Create `examples/` directory with working scripts

**8.2 Testing & Quality**
- Achieve >80% test coverage
- Run linting: `ruff check .`
- Run type checking: `mypy src/delve`
- Integration tests for all workflows
- Test installation from wheel

**8.3 Release Prep**
- Tag version 0.1.0
- Build: `python -m build`
- Test install: `pip install dist/delve-0.1.0-py3-none-any.whl`
- Create GitHub release

### Phase 9: Cleanup (Day 17)

**9.1 Remove Old Code**
- Delete `src/react_agent/` directory
- Delete `langgraph.json`, `static/`
- Update `.gitignore`

**9.2 Final Verification**
- Full test suite passes
- CLI works on sample data
- SDK works in notebooks
- Documentation accurate

## Key Technical Decisions

### 1. Keep LangGraph ✅
**Why:** LangChain ambassador project, built-in observability, proven architecture
**Trade-off:** Adds dependency but provides significant value

### 2. Break Backward Compatibility ✅
**Why:** Fundamental shift from interactive to automated, clean design
**Trade-off:** Cannot upgrade existing deployments, but no external users yet

### 3. Adapter Pattern ✅
**Why:** Extensible, testable, clean separation of concerns
**Trade-off:** More initial code, but easy to add new sources later

### 4. Remove Human-in-the-Loop ✅
**Why:** Non-interactive requirement, simplifies graph
**Trade-off:** No manual refinement (can add back as optional feature)

### 5. Multiple Output Formats ✅
**Why:** Convenience - machines (JSON), spreadsheets (CSV), humans (Markdown)
**Trade-off:** Minimal - file generation is trivial compared to LLM cost

### 6. Click for CLI ✅
**Why:** Mature, well-documented, feature-rich
**Alternatives:** Typer (less mature), argparse (verbose)

## Critical Missing Dependencies

**IMPORTANT:** Current `pyproject.toml` is missing:
- `langsmith>=0.1.0` - Used in runs_retriever.py but not declared!
- `click>=8.1.0` - Needed for CLI
- `pandas>=2.0.0` - Needed for CSV/DataFrame support
- `jsonpath-ng>=1.6.0` - Needed for JSON path expressions
- `rich>=13.0.0` - Better CLI output

## Success Criteria

**Functional Requirements:**
- ✅ Works with CSV, JSON/JSONL, LangSmith, DataFrames
- ✅ Generates JSON, CSV, Markdown outputs
- ✅ CLI: `delve run data.csv --text-column text`
- ✅ SDK: `Delve().run_sync("data.csv", text_column="text")`
- ✅ Non-interactive (no human approval)
- ✅ Installable via pip

**Quality Requirements:**
- >80% test coverage
- All linting passes (ruff)
- Type hints on public API
- Complete documentation
- Working examples

**Performance:**
- Process 100 documents in <5 minutes
- Handle 1000+ documents without crashing
- Progress updates in CLI

## Output File Structure

```
results/
├── taxonomy.json              # Machine-readable taxonomy
├── labeled_documents.json     # Documents with categories
├── labeled_data.csv           # Spreadsheet format
├── taxonomy_reference.csv     # Category lookup table
├── report.md                  # Human-readable summary
└── metadata.json              # Run configuration and stats
```

## Future Enhancements (Post v0.1.0)

- **v0.2.0**: Optional iterative mode with feedback, confidence scores
- **v0.3.0**: Hierarchical taxonomies, custom prompts, fine-tuned models
- **v0.4.0**: S3/database adapters, REST API server
- **v0.5.0**: Web UI, visualization, annotation tools

## Critical Files Reference

1. **`src/react_agent/graph.py`**
   - Core orchestration - remove interactive nodes, add load_data and save_results

2. **`src/react_agent/nodes/runs_retriever.py`**
   - LangSmith integration - refactor into adapter pattern

3. **`src/react_agent/state.py`**
   - Data structures - remove interactive fields

4. **`src/react_agent/configuration.py`**
   - Configuration - add SDK-friendly parameters

5. **`pyproject.toml`**
   - Packaging - rename, add CLI entry, fix dependencies
