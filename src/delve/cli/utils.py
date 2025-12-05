"""CLI utility functions."""

import sys
import logging
from pathlib import Path
from typing import Optional

import click


def setup_logging(verbose: bool):
    """Configure logging based on verbosity.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_file(path: str) -> bool:
    """Validate file exists and is readable.

    Args:
        path: File path to validate

    Returns:
        True if valid

    Raises:
        click.BadParameter: If file is invalid
    """
    file_path = Path(path)
    if not file_path.exists():
        raise click.BadParameter(f"File not found: {path}")
    if not file_path.is_file():
        raise click.BadParameter(f"Not a file: {path}")
    if not file_path.stat().st_size > 0:
        raise click.BadParameter(f"File is empty: {path}")
    return True


def detect_source_type(source: str) -> str:
    """Auto-detect data source type.

    Args:
        source: Data source string

    Returns:
        Detected source type

    Raises:
        click.BadParameter: If source type cannot be determined
    """
    if source.startswith("langsmith://"):
        return "langsmith"
    elif source.endswith(".csv"):
        return "csv"
    elif source.endswith(".json"):
        return "json"
    elif source.endswith(".jsonl"):
        return "jsonl"
    else:
        raise click.BadParameter(
            f"Cannot detect source type for: {source}. "
            f"Use --source-type to specify explicitly."
        )


def format_size(num_docs: int) -> str:
    """Format document count for display.

    Args:
        num_docs: Number of documents

    Returns:
        Formatted string
    """
    if num_docs == 1:
        return "1 document"
    return f"{num_docs:,} documents"


def print_summary(result, output_dir: str):
    """Print results summary.

    Args:
        result: DelveResult object
        output_dir: Output directory path
    """
    click.secho("\n✓ Taxonomy generation complete!", fg="green", bold=True)

    click.echo(f"\n📊 Generated {len(result.taxonomy)} categories from {format_size(len(result.labeled_documents))}")

    # Show first 5 categories
    click.echo("\n📋 Categories:")
    for cat in result.taxonomy[:5]:
        click.echo(f"  • {cat.name}: {cat.description}")
    if len(result.taxonomy) > 5:
        click.echo(f"  ... and {len(result.taxonomy) - 5} more")

    # Show output location
    click.echo(f"\n📁 Results saved to: {click.style(output_dir, fg='cyan', bold=True)}")
