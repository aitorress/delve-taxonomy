"""Base class for result exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from delve.result import DelveResult


class Exporter(ABC):
    """Abstract base class for result exporters.

    All exporters must implement the export method to save
    results in their specific format.
    """

    @abstractmethod
    async def export(self, result: DelveResult, output_dir: str) -> Path:
        """Export results to file.

        Args:
            result: DelveResult to export
            output_dir: Directory for output file

        Returns:
            Path: Path to created file

        Raises:
            Exception: If export fails
        """
        pass

    def ensure_output_dir(self, output_dir: str) -> Path:
        """Ensure output directory exists.

        Args:
            output_dir: Directory path

        Returns:
            Path: Path object for the directory
        """
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
