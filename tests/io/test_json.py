import json
from pathlib import Path, PurePath

import pytest

from routix.io.json import dump_json


class MockSerializable:
    """Mock class with to_dict method for testing."""

    def __init__(self, value: int, name: str):
        self.value = value
        self.name = name

    def to_dict(self) -> dict:
        return {"value": self.value, "name": self.name}


class MockWithoutToDict:
    """Mock class without to_dict method for testing."""

    def __init__(self, value: int):
        self.value = value


def test_dump_json_basic(tmp_path: Path):
    """Test dump_json function with basic types."""
    obj = {"key": "value", "number": 42, "list": [1, 2, 3]}
    file_path = tmp_path / "dump.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == obj


def test_dump_json_with_pure_path(tmp_path: Path):
    """Test dump_json serializes PurePath objects as strings."""
    path1 = Path("/path/one")
    path2 = PurePath("/path/two")
    obj = {"path1": path1, "path2": path2}
    file_path = tmp_path / "paths.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["path1"] == str(path1)
    assert loaded["path2"] == str(path2)


def test_dump_json_with_serializable_object(tmp_path: Path):
    """Test dump_json serializes objects with to_dict method."""
    obj = {
        "config": MockSerializable(value=42, name="test"),
        "items": [
            MockSerializable(value=1, name="a"),
            MockSerializable(value=2, name="b"),
        ],
    }
    file_path = tmp_path / "serializable.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["config"] == {"value": 42, "name": "test"}
    assert loaded["items"] == [{"value": 1, "name": "a"}, {"value": 2, "name": "b"}]


def test_dump_json_with_nested_path_and_serializable(tmp_path: Path):
    """Test dump_json with nested structure containing Path and serializable objects."""
    # Use WindowsPath for cross-platform compatibility
    obj = {
        "output_dir": Path("/output/results"),
        "config": MockSerializable(value=100, name="nested"),
        "metadata": {
            "input_path": PurePath("/input/data"),
            "settings": {"key": "value"},
        },
    }
    file_path = tmp_path / "nested.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # Path conversion result depends on OS (forward/backward slashes)
    assert loaded["output_dir"] == str(Path("/output/results"))
    assert loaded["config"] == {"value": 100, "name": "nested"}
    assert loaded["metadata"]["input_path"] == str(PurePath("/input/data"))
    assert loaded["metadata"]["settings"] == {"key": "value"}


def test_dump_json_raises_on_unserializable_object(tmp_path: Path):
    """Test dump_json raises TypeError for objects without to_dict."""
    obj = {"item": MockWithoutToDict(value=42)}
    file_path = tmp_path / "unserializable.json"

    with pytest.raises(
        TypeError, match="Object of type 'MockWithoutToDict' is not JSON serializable"
    ):
        dump_json(obj, file_path)


def test_dump_json_with_complex_types(tmp_path: Path):
    """Test dump_json with various Python types."""
    obj = {
        "string": "text",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "list": [1, "two", 3.0],
        "nested_dict": {"a": {"b": {"c": 1}}},
    }
    file_path = tmp_path / "complex.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == obj


def test_dump_json_indent_formatting(tmp_path: Path):
    """Test dump_json uses 2-space indentation."""
    obj = {"key": "value", "nested": {"a": 1}}
    file_path = tmp_path / "formatted.json"
    dump_json(obj, file_path)

    content = file_path.read_text(encoding="utf-8")

    # Check 2-space indentation
    assert '  "key"' in content
    assert '    "a"' in content


def test_dump_json_with_tuple(tmp_path: Path):
    """Test dump_json serializes tuples as lists."""
    obj = {"coordinates": (10, 20, 30)}
    file_path = tmp_path / "tuple.json"
    dump_json(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # Tuples are serialized as lists in JSON
    assert loaded["coordinates"] == [10, 20, 30]
