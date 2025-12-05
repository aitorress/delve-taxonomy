"""Command-line interface for Delve."""

import sys
from typing import Optional

import click

from delve import Delve, __version__
from delve.cli.utils import setup_logging, validate_file, detect_source_type, print_summary


@click.group()
@click.version_option(version=__version__)
def cli():
    """Delve - AI-powered taxonomy generation for your data.

    Generate taxonomies and automatically categorize your documents
    using state-of-the-art language models.

    \b
    Examples:
      # Basic CSV usage
      delve run data.csv --text-column conversation

      # JSON with JSONPath
      delve run data.json --json-path "$.messages[*].content"

      # LangSmith source
      delve run langsmith://my-project --langsmith-key $KEY --days 7
    """
    pass


@cli.command()
@click.argument("data_source", type=str)
@click.option(
    "--text-column",
    type=str,
    help="Column containing text data (for CSV/tabular)",
)
@click.option(
    "--id-column",
    type=str,
    help="Column containing document IDs (optional)",
)
@click.option(
    "--json-path",
    type=str,
    help="JSONPath expression for nested JSON (e.g., '$.messages[*].content')",
)
@click.option(
    "--source-type",
    type=click.Choice(["csv", "json", "jsonl", "langsmith", "auto"]),
    default="auto",
    help="Force specific data source type",
)
@click.option(
    "--model",
    default="anthropic/claude-3-5-sonnet-20241022",
    help="Main LLM model for reasoning",
)
@click.option(
    "--fast-llm",
    default="anthropic/claude-3-haiku-20240307",
    help="Fast LLM for summarization",
)
@click.option(
    "--sample-size",
    type=int,
    default=100,
    help="Number of documents to sample for taxonomy generation",
)
@click.option(
    "--batch-size",
    type=int,
    default=200,
    help="Batch size for processing",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="./results",
    help="Output directory for results",
)
@click.option(
    "--output-format",
    multiple=True,
    type=click.Choice(["json", "csv", "markdown"]),
    default=["json", "csv", "markdown"],
    help="Output formats (can specify multiple)",
)
@click.option(
    "--use-case",
    type=str,
    help="Description of taxonomy use case",
)
@click.option(
    "--langsmith-key",
    type=str,
    envvar="LANGSMITH_API_KEY",
    help="LangSmith API key (for langsmith:// sources)",
)
@click.option(
    "--days",
    type=int,
    default=7,
    help="Days to look back (for LangSmith sources)",
)
@click.option(
    "--verbose/--quiet",
    default=True,
    help="Enable/disable progress output",
)
def run(
    data_source: str,
    text_column: Optional[str],
    id_column: Optional[str],
    json_path: Optional[str],
    source_type: str,
    model: str,
    fast_llm: str,
    sample_size: int,
    batch_size: int,
    output_dir: str,
    output_format: tuple,
    use_case: Optional[str],
    langsmith_key: Optional[str],
    days: int,
    verbose: bool,
):
    """Run taxonomy generation on DATA_SOURCE.

    DATA_SOURCE can be:
      - Path to CSV file (e.g., data.csv)
      - Path to JSON/JSONL file (e.g., data.json)
      - LangSmith URI (e.g., langsmith://project-name)

    \b
    Examples:

      \b
      # Basic CSV usage
      delve run data.csv --text-column conversation

      \b
      # JSON with nested path
      delve run data.json --json-path "$.messages[*].content"

      \b
      # LangSmith source
      delve run langsmith://my-project --langsmith-key $KEY --days 7

      \b
      # Custom configuration
      delve run data.csv --text-column text --sample-size 200 \\
        --model anthropic/claude-opus-4 --output-dir ./output
    """
    setup_logging(verbose)

    # Auto-detect source type if needed
    if source_type == "auto":
        try:
            source_type = detect_source_type(data_source)
        except click.BadParameter as e:
            click.echo(f"Error: {e.message}", err=True)
            sys.exit(1)

    # Validate file-based sources
    if source_type in ("csv", "json", "jsonl"):
        try:
            validate_file(data_source)
        except click.BadParameter as e:
            click.echo(f"Error: {e.message}", err=True)
            sys.exit(1)

    # Validate required parameters
    if source_type == "csv" and not text_column:
        click.echo("Error: --text-column is required for CSV files", err=True)
        sys.exit(1)

    if source_type == "langsmith" and not langsmith_key:
        click.echo(
            "Error: --langsmith-key is required for LangSmith sources. "
            "Set LANGSMITH_API_KEY environment variable or use --langsmith-key option.",
            err=True,
        )
        sys.exit(1)

    # Create Delve client
    delve = Delve(
        model=model,
        fast_llm=fast_llm,
        sample_size=sample_size,
        batch_size=batch_size,
        use_case=use_case,
        output_dir=output_dir,
        output_formats=list(output_format),
        verbose=verbose,
    )

    # Prepare adapter kwargs
    adapter_kwargs = {}
    if source_type == "langsmith":
        adapter_kwargs["api_key"] = langsmith_key
        adapter_kwargs["days"] = days
    elif source_type == "json" and json_path:
        adapter_kwargs["json_path"] = json_path

    # Run taxonomy generation
    try:
        if verbose:
            click.echo(f"🚀 Starting taxonomy generation...")
            click.echo(f"   Source: {data_source}")
            click.echo(f"   Model: {model}")
            click.echo(f"   Sample size: {sample_size}")
            click.echo()

        result = delve.run_sync(
            data_source,
            text_column=text_column,
            id_column=id_column,
            source_type=source_type,
            **adapter_kwargs,
        )

        # Print summary
        print_summary(result, output_dir)

    except ValueError as e:
        # User-friendly errors (like missing API key, validation errors)
        error_msg = str(e)
        click.echo(f"\n❌ Error: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        # Check for common error patterns and provide helpful messages
        if "api_key" in error_lower or "authentication" in error_lower or "auth_token" in error_lower:
            click.echo("\n❌ Authentication Error", err=True)
            click.echo("\nThe API key is missing or invalid.", err=True)
            click.echo("\nPlease set your Anthropic API key:", err=True)
            click.echo("  export ANTHROPIC_API_KEY=your-api-key-here", err=True)
            click.echo("\nYou can get an API key from: https://console.anthropic.com/", err=True)
        elif "could not resolve" in error_lower and "authentication" in error_lower:
            click.echo("\n❌ API Key Not Found", err=True)
            click.echo("\nThe ANTHROPIC_API_KEY environment variable is not set.", err=True)
            click.echo("\nPlease set your API key:", err=True)
            click.echo("  export ANTHROPIC_API_KEY=your-api-key-here", err=True)
            click.echo("\nGet your API key: https://console.anthropic.com/", err=True)
        else:
            click.echo(f"\n❌ Error: {error_msg}", err=True)
        
        if verbose:
            import traceback
            click.echo("\nFull error details:", err=True)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
