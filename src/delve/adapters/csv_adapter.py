"""CSV file adapter for loading documents."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional

import pandas as pd

from delve.adapters.base import DataSource, DataSourceConfig
from delve.state import Doc


class CSVAdapter(DataSource):
    """Adapter for loading data from CSV files.

    Reads CSV files and converts rows to Doc objects using a specified
    text column for content.
    """

    def __init__(
        self,
        file_path: str,
        text_column: str,
        id_column: Optional[str] = None,
        encoding: str = "utf-8",
    ):
        """Initialize CSV adapter.

        Args:
            file_path: Path to the CSV file
            text_column: Name of the column containing text content
            id_column: Optional column name for document IDs (generates UUIDs if not provided)
            encoding: File encoding (default: utf-8)
        """
        config = DataSourceConfig(
            source_type="csv",
            source_path=file_path,
            additional_params={
                "text_column": text_column,
                "id_column": id_column,
                "encoding": encoding,
            },
        )
        super().__init__(config)
        self.file_path = Path(file_path)
        self.text_column = text_column
        self.id_column = id_column
        self.encoding = encoding

    def validate(self) -> bool:
        """Validate that the CSV file exists and has required columns.

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

        # Try to read just the header to validate columns
        try:
            df = pd.read_csv(self.file_path, nrows=0, encoding=self.encoding)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        if self.text_column not in df.columns:
            raise ValueError(
                f"Text column '{self.text_column}' not found in CSV. "
                f"Available columns: {', '.join(df.columns)}"
            )

        if self.id_column and self.id_column not in df.columns:
            raise ValueError(
                f"ID column '{self.id_column}' not found in CSV. "
                f"Available columns: {', '.join(df.columns)}"
            )

        return True

    async def load(self) -> List[Doc]:
        """Load documents from CSV file.

        Returns:
            List of Doc objects

        Raises:
            Exception: If file cannot be read or parsed
        """
        # Validate first
        self.validate()

        # Read CSV file
        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)
        except Exception as e:
            raise Exception(f"Failed to read CSV file: {e}")

        # Convert to Doc objects
        documents = []
        for idx, row in df.iterrows():
            # Get ID from column or generate UUID
            if self.id_column:
                doc_id = str(row[self.id_column])
            else:
                doc_id = str(uuid.uuid4())

            # Get text content
            content = str(row[self.text_column])

            # Skip empty content
            if not content or content.strip() == "" or content == "nan":
                continue

            doc = Doc(id=doc_id, content=content)
            documents.append(doc)

        if not documents:
            raise ValueError(f"No valid documents found in CSV file: {self.file_path}")

        return documents
