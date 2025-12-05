"""Pandas DataFrame adapter for loading documents from in-memory data."""

from __future__ import annotations

import uuid
from typing import List, Optional

import pandas as pd

from delve.adapters.base import DataSource, DataSourceConfig
from delve.state import Doc


class DataFrameAdapter(DataSource):
    """Adapter for loading data from pandas DataFrames.

    Useful for programmatic SDK usage with in-memory data.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        text_column: str,
        id_column: Optional[str] = None,
    ):
        """Initialize DataFrame adapter.

        Args:
            df: Pandas DataFrame containing the data
            text_column: Name of the column containing text content
            id_column: Optional column name for document IDs (generates UUIDs if not provided)
        """
        config = DataSourceConfig(
            source_type="dataframe",
            source_path=None,  # In-memory, no path
            additional_params={
                "text_column": text_column,
                "id_column": id_column,
            },
        )
        super().__init__(config)
        self.df = df
        self.text_column = text_column
        self.id_column = id_column

    def validate(self) -> bool:
        """Validate that the DataFrame has required columns.

        Returns:
            True if valid

        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        if self.df is None or self.df.empty:
            raise ValueError("DataFrame is empty or None")

        if self.text_column not in self.df.columns:
            raise ValueError(
                f"Text column '{self.text_column}' not found in DataFrame. "
                f"Available columns: {', '.join(self.df.columns)}"
            )

        if self.id_column and self.id_column not in self.df.columns:
            raise ValueError(
                f"ID column '{self.id_column}' not found in DataFrame. "
                f"Available columns: {', '.join(self.df.columns)}"
            )

        return True

    async def load(self) -> List[Doc]:
        """Load documents from DataFrame.

        Returns:
            List of Doc objects

        Raises:
            ValueError: If DataFrame cannot be processed
        """
        # Validate first
        self.validate()

        # Convert to Doc objects
        documents = []
        for idx, row in self.df.iterrows():
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
            raise ValueError("No valid documents found in DataFrame")

        return documents
