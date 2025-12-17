# Changelog

All notable changes to Delve will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-01-16

### Fixed

- **Classifier class weight bug**: Fixed incorrect class weight mapping when training classifier with sparse category indices. Previously, when some taxonomy categories had no labeled examples (e.g., documents labeled as "Other" were skipped), the class weights were incorrectly mapped using sequential indices instead of actual class indices, causing `ValueError: The classes, [X], are not in class_weight`.

---

## [0.1.4] - 2025-01-16

### Added

- **New Console System**: Unified output management with `Console` class
- **Verbosity Levels**: Five levels of output control
  - `SILENT` (SDK default) - No output, ideal for library consumers
  - `QUIET` (`-q`) - Errors only
  - `NORMAL` (CLI default) - Spinners and completion checkmarks
  - `VERBOSE` (`-v`) - Progress bars with throughput-based ETA
  - `DEBUG` (`-vv`) - Full debug output including warnings
- **Progress Bars**: Real-time progress tracking with honest ETA based on observed throughput
- **Rich Integration**: Beautiful terminal output using the `rich` library

### Changed

- **CLI Flags**: Replaced `--verbose/--quiet` with `-q/-v/-vv` pattern (Unix standard)
- **SDK Default**: Now silent by default (library best practice)

### Fixed

- Removed debug print statements from exception handlers
- Warnings now only show in DEBUG mode (not cluttering normal output)
- **Early API key validation**: Both Anthropic and OpenAI keys are validated immediately at startup, before any processing begins. Users no longer wait 5+ minutes only to fail on a missing key

### Usage

```bash
# CLI
delve run data.csv --text-column text        # Normal (spinners)
delve run data.csv --text-column text -q     # Quiet (errors only)
delve run data.csv --text-column text -v     # Verbose (progress bars)
delve run data.csv --text-column text -vv    # Debug (everything)
```

```python
# SDK
from delve import Delve
from delve.console import Verbosity

delve = Delve()  # Silent by default
delve = Delve(verbosity=Verbosity.NORMAL)    # With output
delve = Delve(verbosity=Verbosity.VERBOSE)   # With progress bars
```

---

## [0.1.0] - 2024-01-15

### Initial Release

Delve v0.1.0 is the first production-ready release, transforming the taxonomy_generator project into a fully-featured SDK and CLI for AI-powered taxonomy generation.

### Added

#### Core Features
- **SDK API**: `Delve` class providing programmatic access to taxonomy generation
- **CLI Interface**: `delve` command-line tool built with Click
- **Multiple Data Sources**:
  - CSV files with configurable text and ID columns
  - JSON/JSONL files with JSONPath support for nested data
  - LangSmith projects with time-based filtering
  - Pandas DataFrames for in-memory processing
- **Adapter Pattern**: Pluggable data source architecture for easy extensibility
- **Multiple Output Formats**:
  - `taxonomy.json` - Machine-readable taxonomy with metadata
  - `labeled_documents.json` - Documents with assigned categories
  - `labeled_data.csv` - Spreadsheet-friendly format
  - `taxonomy_reference.csv` - Category lookup table
  - `report.md` - Human-readable summary with statistics
  - `metadata.json` - Run configuration and metadata

#### Processing Pipeline
- **Automated Workflow**: Non-interactive pipeline for production use
- **Smart Sampling**: Automatic sampling of large datasets for efficiency
- **Iterative Clustering**: Minibatch-based taxonomy generation
- **Quality Review**: Built-in LLM validation of taxonomy quality
- **Document Labeling**: Automatic categorization with explanations
- **Progress Tracking**: Real-time feedback during processing

#### Configuration
- Configurable LLM models (main and fast)
- Adjustable sample sizes and batch sizes
- Custom use case descriptions
- Flexible output directory and formats
- Verbose/quiet modes

#### Developer Experience
- Async and sync APIs
- Type hints throughout codebase
- Comprehensive documentation
- Working examples for all use cases
- Clear error messages and validation

### Changed

**Breaking Changes from Previous Version**:

- **Package Rename**: `react-agent` → `delve`
- **Mode**: Interactive (LangGraph Studio) → Non-interactive (SDK/CLI)
- **Interface**: Studio-based → Programmatic and CLI
- **State Structure**: Removed interactive fields (`messages`, `user_feedback`, `UserFeedback` class)
- **Configuration**: Removed `max_runs`, added `output_formats`, `output_dir`, `verbosity`, `use_case`
- **Graph Flow**: Removed human-in-the-loop nodes (`request_taxonomy_approval`, `handle_user_feedback`)

#### Architecture Changes
- Renamed core module from `src/react_agent/` to `src/delve/`
- Refactored nodes into `core/` directory
- Introduced `adapters/` for data source abstraction
- Introduced `exporters/` for output format generation
- Simplified graph: removed interrupts and conditional feedback routing

### Fixed

- **Missing Dependency**: Added `langsmith>=0.1.0` to dependencies (was used but not declared)
- **Import Paths**: Updated all imports from `react_agent` to `delve`

### Technical Details

#### Dependencies Added
- `click>=8.1.0` - CLI framework
- `pandas>=2.0.0` - Data manipulation
- `jsonpath-ng>=1.6.0` - JSON path expressions
- `rich>=13.0.0` - Enhanced CLI output
- `langsmith>=0.1.0` - LangSmith integration (previously missing)

#### Graph Changes
```
Old Flow (Interactive):
get_runs → summarize → get_minibatches → generate_taxonomy
→ update_taxonomy (loop) → review_taxonomy → request_taxonomy_approval
→ handle_user_feedback (INTERRUPT) → label_documents → END

New Flow (Automated):
load_data → summarize → get_minibatches → generate_taxonomy
→ update_taxonomy (loop) → review_taxonomy → label_documents
→ save_results → END
```

#### Project Structure
```
src/delve/
├── __init__.py              # Public API exports
├── client.py               # SDK client
├── result.py               # Result objects
├── configuration.py        # Configuration
├── state.py                # State definitions
├── graph.py                # LangGraph workflow
├── prompts.py              # LLM prompts
├── utils.py                # Utilities
├── routing.py              # Conditional routing
├── core/                   # Processing nodes
│   ├── data_loader.py
│   ├── summarizer.py
│   ├── batch_generator.py
│   ├── taxonomy_generator.py
│   ├── taxonomy_updater.py
│   ├── taxonomy_reviewer.py
│   ├── document_labeler.py
│   └── results_saver.py
├── adapters/               # Data source adapters
│   ├── base.py
│   ├── csv_adapter.py
│   ├── json_adapter.py
│   ├── langsmith_adapter.py
│   └── dataframe_adapter.py
├── exporters/              # Output generators
│   ├── base.py
│   ├── json_exporter.py
│   ├── csv_exporter.py
│   ├── markdown_exporter.py
│   └── metadata_exporter.py
└── cli/                    # CLI implementation
    ├── main.py
    └── utils.py
```

### Documentation

- **README.md**: Comprehensive documentation with installation, usage, and examples
- **examples/**: Working example scripts for all use cases
  - `basic_csv_example.py` - Simple CSV processing
  - `json_example.py` - JSON with JSONPath
  - `dataframe_example.py` - Pandas integration
  - `advanced_usage.py` - Advanced features
  - `sample_data.csv` - Test data
  - `README.md` - Examples documentation

### Known Limitations

- No hierarchical taxonomies (planned for v0.3.0)
- No confidence scores for categories (planned for v0.2.0)
- No custom prompt templates (planned for v0.3.0)
- No web UI (planned for v0.5.0)

### Migration Guide

If upgrading from the previous `react-agent` version:

1. **Update imports**:
   ```python
   # Old
   from react_agent import ...

   # New
   from delve import Delve
   ```

2. **Use new SDK/CLI interface**:
   ```python
   # Old (interactive)
   # Used with LangGraph Studio

   # New (programmatic)
   delve = Delve()
   result = delve.run_sync("data.csv", text_column="text")
   ```

3. **Note**: This release breaks backward compatibility. The interactive Studio-based workflow is no longer supported. For human-in-the-loop workflows, wait for v0.2.0 which will add optional iterative mode.

### Contributors

- [Your name]

### Acknowledgments

Built with LangChain and LangGraph. Powered by Anthropic's Claude models.

---

## Future Releases

### [0.2.0] - Planned
- Optional iterative mode with human feedback
- Confidence scores for categories
- Category merging suggestions

### [0.3.0] - Planned
- Hierarchical taxonomies
- Custom prompt templates
- Fine-tuned model support

### [0.4.0] - Planned
- S3 and database adapters
- REST API server
- Batch processing improvements

### [0.5.0] - Planned
- Web UI
- Visualization tools
- Annotation interfaces
