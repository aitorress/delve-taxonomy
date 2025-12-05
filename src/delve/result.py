"""Result objects for taxonomy generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from delve.state import Doc, State
    from delve.configuration import Configuration
else:
    from delve.state import State


@dataclass
class TaxonomyCategory:
    """A single taxonomy category."""

    id: str
    name: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


@dataclass
class DelveResult:
    """Results from taxonomy generation."""

    taxonomy: List[TaxonomyCategory]
    labeled_documents: List[Doc]
    metadata: Dict[str, Any]
    config: Configuration
    export_paths: Dict[str, Path] = field(default_factory=dict)

    @classmethod
    def from_state(cls, state: Union[State, Dict[str, Any]], config: Configuration) -> DelveResult:
        """Create result from graph state.

        Args:
            state: The final state from graph execution (State dataclass or dict)
            config: Configuration used for the run

        Returns:
            DelveResult instance
        """
        # Handle both dict (from LangGraph) and State object
        if isinstance(state, dict):
            clusters = state.get("clusters", [])
            documents_raw = state.get("documents", [])
            status = state.get("status", [])
        else:
            # State object
            clusters = state.clusters if state.clusters else []
            documents_raw = state.documents if state.documents else []
            status = state.status if state.status else []
        
        # Extract final taxonomy from clusters
        # clusters is a list of lists of dicts, get the last list (most recent taxonomy)
        final_clusters = []
        if clusters and len(clusters) > 0:
            final_clusters = clusters[-1]
        
        taxonomy = [
            TaxonomyCategory(
                id=str(c.get("id", "")),
                name=c.get("name", ""),
                description=c.get("description", ""),
            )
            for c in final_clusters
            if isinstance(c, dict)
        ]

        # Convert documents to Doc objects if they're dicts
        from delve.state import Doc
        documents = []
        for doc in documents_raw:
            if isinstance(doc, dict):
                documents.append(Doc(
                    id=doc.get("id", ""),
                    content=doc.get("content", ""),
                    summary=doc.get("summary"),
                    explanation=doc.get("explanation"),
                    category=doc.get("category"),
                ))
            else:
                # Already a Doc object
                documents.append(doc)

        # Create metadata
        metadata = {
            "num_documents": len(documents),
            "num_categories": len(taxonomy),
            "sample_size": config.sample_size,
            "batch_size": config.batch_size,
            "model": config.model,
            "status_log": status if status else [],
        }

        return cls(
            taxonomy=taxonomy,
            labeled_documents=documents,
            metadata=metadata,
            config=config,
        )

    async def export(self) -> Dict[str, Path]:
        """Export results in configured formats.

        Returns:
            Dict mapping format name to output file path
        """
        from delve.exporters import get_exporters

        output_paths = {}
        exporters = get_exporters()

        for format_name in self.config.output_formats:
            if format_name in exporters:
                exporter = exporters[format_name]
                path = await exporter.export(self, self.config.output_dir)
                output_paths[format_name] = path

        # Always export metadata
        if "metadata" in exporters:
            metadata_path = await exporters["metadata"].export(self, self.config.output_dir)
            output_paths["metadata"] = metadata_path

        self.export_paths = output_paths
        return output_paths

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "taxonomy": [cat.to_dict() for cat in self.taxonomy],
            "labeled_documents": [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "category": doc.category,
                    "summary": doc.summary,
                    "explanation": doc.explanation,
                }
                for doc in self.labeled_documents
            ],
            "metadata": self.metadata,
        }
