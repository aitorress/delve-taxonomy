"""Tests for data_loader module."""

import json
import pytest
import tempfile
from pathlib import Path

from delve.core.data_loader import _load_predefined_taxonomy
from delve.state import Doc


class TestLoadPredefinedTaxonomy:
    """Test the _load_predefined_taxonomy function."""

    def test_load_from_list(self):
        """Test loading taxonomy from a Python list."""
        taxonomy = [
            {"id": "1", "name": "Category A", "description": "Description A"},
            {"id": "2", "name": "Category B", "description": "Description B"},
        ]
        result = _load_predefined_taxonomy(taxonomy)
        assert result == taxonomy
        assert len(result) == 2

    def test_load_from_list_missing_fields(self):
        """Test that loading fails with missing required fields."""
        taxonomy = [
            {"id": "1", "name": "Category A"},  # Missing description
        ]
        with pytest.raises(ValueError, match="must have 'id', 'name', and 'description'"):
            _load_predefined_taxonomy(taxonomy)

    def test_load_from_json_file(self):
        """Test loading taxonomy from a JSON file."""
        taxonomy_data = [
            {"id": "1", "name": "Category A", "description": "Description A"},
            {"id": "2", "name": "Category B", "description": "Description B"},
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(taxonomy_data, f)
            temp_path = f.name

        try:
            result = _load_predefined_taxonomy(temp_path)
            assert len(result) == 2
            assert result[0]["name"] == "Category A"
        finally:
            Path(temp_path).unlink()

    def test_load_from_json_nested_taxonomy_key(self):
        """Test loading from JSON with nested 'taxonomy' key."""
        data = {
            "taxonomy": [
                {"id": "1", "name": "Category A", "description": "Description A"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            result = _load_predefined_taxonomy(temp_path)
            assert len(result) == 1
            assert result[0]["name"] == "Category A"
        finally:
            Path(temp_path).unlink()

    def test_load_from_json_nested_clusters_key(self):
        """Test loading from JSON with nested 'clusters' key."""
        data = {
            "clusters": [
                {"id": "1", "name": "Category A", "description": "Description A"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            result = _load_predefined_taxonomy(temp_path)
            assert len(result) == 1
            assert result[0]["name"] == "Category A"
        finally:
            Path(temp_path).unlink()

    def test_load_from_csv_file(self):
        """Test loading taxonomy from a CSV file."""
        csv_content = """id,name,description
1,Category A,Description A
2,Category B,Description B"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = _load_predefined_taxonomy(temp_path)
            assert len(result) == 2
            assert result[0]["name"] == "Category A"
            assert result[1]["id"] == "2"
        finally:
            Path(temp_path).unlink()

    def test_load_from_csv_missing_columns(self):
        """Test that CSV loading fails with missing required columns."""
        csv_content = """id,name
1,Category A"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="CSV must have columns"):
                _load_predefined_taxonomy(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test that loading fails when file doesn't exist."""
        with pytest.raises(ValueError, match="Taxonomy file not found"):
            _load_predefined_taxonomy("/nonexistent/path/to/file.json")

    def test_unsupported_file_format(self):
        """Test that loading fails with unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                _load_predefined_taxonomy(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_invalid_input_type(self):
        """Test that loading fails with invalid input type."""
        with pytest.raises(ValueError, match="Invalid taxonomy format"):
            _load_predefined_taxonomy(123)  # type: ignore
