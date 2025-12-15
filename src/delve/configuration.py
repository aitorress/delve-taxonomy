"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, Optional, List, Union, Dict

from langchain_core.runnables import RunnableConfig, ensure_config


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the Delve taxonomy generator."""

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="anthropic/claude-3-5-sonnet-20241022",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    fast_llm: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="anthropic/claude-3-haiku-20240307",
        metadata={
            "description": "A faster, lighter model for tasks like summarization. "
            "Should be in the form: provider/model-name."
        },
    )

    sample_size: int = field(
        default=100,
        metadata={
            "description": "Number of documents to sample for processing."
        },
    )

    batch_size: int = field(
        default=200,
        metadata={
            "description": "Size of minibatches for document processing."
        },
    )

    output_formats: List[str] = field(
        default_factory=lambda: ["json", "csv", "markdown"],
        metadata={
            "description": "List of output formats to generate (json, csv, markdown)."
        },
    )

    output_dir: str = field(
        default="./results",
        metadata={
            "description": "Directory where output files will be saved."
        },
    )

    verbose: bool = field(
        default=True,
        metadata={
            "description": "Enable verbose logging and progress updates."
        },
    )

    use_case: str = field(
        default="Generate taxonomy for categorizing document content",
        metadata={
            "description": "Description of the taxonomy use case."
        },
    )

    predefined_taxonomy: Optional[Union[str, List[Dict[str, str]]]] = field(
        default=None,
        metadata={
            "description": "Pre-defined taxonomy to use instead of discovering one. "
            "Can be a file path (JSON/CSV) or a list of category dicts with 'id', 'name', 'description'."
        },
    )

    embedding_model: str = field(
        default="text-embedding-3-large",
        metadata={
            "description": "OpenAI embedding model to use for classifier training. "
            "Used when sample_size < total documents to train efficient classifier."
        },
    )

    classifier_confidence_threshold: float = field(
        default=0.0,
        metadata={
            "description": "Minimum confidence threshold for classifier predictions. "
            "Documents below this threshold will be labeled by LLM. Set to 0 to disable LLM fallback."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})

    def to_dict(self) -> dict:
        """Convert configuration to dictionary for SDK usage."""
        return {
            "model": self.model,
            "fast_llm": self.fast_llm,
            "sample_size": self.sample_size,
            "batch_size": self.batch_size,
            "output_formats": self.output_formats,
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "use_case": self.use_case,
            "predefined_taxonomy": self.predefined_taxonomy,
            "embedding_model": self.embedding_model,
            "classifier_confidence_threshold": self.classifier_confidence_threshold,
        }
