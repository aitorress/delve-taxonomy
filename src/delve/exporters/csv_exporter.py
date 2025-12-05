"""CSV exporter for taxonomy and labeled documents."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from delve.exporters.base import Exporter

if TYPE_CHECKING:
    from delve.result import DelveResult


class CSVExporter(Exporter):
    """Export results as CSV files."""

    async def export(self, result: DelveResult, output_dir: str) -> Path:
        """Export labeled documents and taxonomy as CSV.

        Creates two files:
        - labeled_data.csv: Documents with their categories
        - taxonomy_reference.csv: Category lookup table

        Args:
            result: DelveResult to export
            output_dir: Directory for output files

        Returns:
            Path: Path to the main labeled_data.csv file
        """
        dir_path = self.ensure_output_dir(output_dir)

        # Export labeled documents
        path = dir_path / "labeled_data.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(["id", "category", "summary", "content"])

            # Data rows
            for doc in result.labeled_documents:
                writer.writerow([
                    doc.id,
                    doc.category or "Unknown",
                    doc.summary or "",
                    doc.content,
                ])

        # Export taxonomy reference
        taxonomy_path = dir_path / "taxonomy_reference.csv"
        with open(taxonomy_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "description"])
            for cat in result.taxonomy:
                writer.writerow([cat.id, cat.name, cat.description])

        return path
