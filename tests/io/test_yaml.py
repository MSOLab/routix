from pathlib import Path

import pytest

from routix.io.yaml import (
    dump_yaml,
    load_yaml,
    object_to_yaml,
    pyyaml_key_to_tuple,
    tuple_to_pyyaml_key,
    yaml_to_object,
)


class MockSerializable:
    """Mock class with to_dict method for testing."""

    def __init__(self, value: int, name: str):
        self.value = value
        self.name = name

    def to_dict(self) -> dict:
        return {"value": self.value, "name": self.name}


def test_object_to_yaml_basic(tmp_path: Path):
    """Test basic object to YAML serialization."""
    obj = {"name": "Alice", "age": 30, "items": [1, 2, 3]}
    file_path = tmp_path / "basic.yaml"
    with pytest.warns(DeprecationWarning):
        object_to_yaml(obj, file_path)

    loaded = yaml_to_object(file_path)
    assert loaded == obj


def test_object_to_yaml_with_path_object(tmp_path: Path):
    """Test that Path objects are saved as strings."""
    path_value = Path("/some/path/to/file")
    obj = {"path": path_value, "value": 42}
    file_path = tmp_path / "path.yaml"
    with pytest.warns(DeprecationWarning):
        object_to_yaml(obj, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert str(path_value) in content

    # Path object is saved as a YAML string and loaded back as a Python string
    loaded = yaml_to_object(file_path)
    assert loaded["value"] == 42
    assert loaded["path"] == str(path_value)


def test_object_to_yaml_with_to_dict_method(tmp_path: Path):
    """Test object with to_dict method serialization."""
    obj = MockSerializable(value=10, name="test")
    file_path = tmp_path / "serializable.yaml"
    with pytest.warns(DeprecationWarning):
        object_to_yaml(obj, file_path)

    loaded = yaml_to_object(file_path)
    assert loaded == {"value": 10, "name": "test"}


def test_yaml_to_object_roundtrip(tmp_path: Path):
    """Test YAML load roundtrip."""
    obj = {"nested": {"data": [1, 2, 3]}, "string": "hello"}
    file_path = tmp_path / "roundtrip.yaml"
    with pytest.warns(DeprecationWarning):
        object_to_yaml(obj, file_path)
    loaded = yaml_to_object(file_path)

    assert loaded == obj


def test_tuple_to_pyyaml_key_simple():
    """Test simple tuple key conversion."""
    d = {("a", "b"): 1, "c": 2}
    with pytest.warns(DeprecationWarning):
        result = tuple_to_pyyaml_key(d)

    assert "!!python/tuple [a, b]" in result
    assert result["!!python/tuple [a, b]"] == 1
    assert result["c"] == 2


def test_tuple_to_pyyaml_key_with_spaces():
    """Test tuple key conversion with spaces in elements."""
    d = {(" a ", " b "): 1}
    with pytest.warns(DeprecationWarning):
        result = tuple_to_pyyaml_key(d)

    # Spaces should be stripped
    assert "!!python/tuple [a, b]" in result


def test_pyyaml_key_to_tuple_simple():
    """Test simple pyyaml key to tuple conversion."""
    d = {"!!python/tuple [a, b]": 1, "c": 2}
    with pytest.warns(DeprecationWarning):
        result = pyyaml_key_to_tuple(d)

    assert result[("a", "b")] == 1
    assert result["c"] == 2


def test_tuple_key_roundtrip():
    """Test tuple key conversion roundtrip."""
    original = {("x", "y"): 10, ("z",): 20, "normal": 30}
    with pytest.warns(DeprecationWarning):
        yaml_formatted = tuple_to_pyyaml_key(original)
    with pytest.warns(DeprecationWarning):
        back = pyyaml_key_to_tuple(yaml_formatted)

    assert back == original


def test_dump_yaml_basic(tmp_path: Path):
    """Test dump_yaml function."""
    obj = {"key": "value", "number": 42}
    file_path = tmp_path / "dump_yaml.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert loaded == obj


def test_dump_yaml_with_tuple_key(tmp_path: Path):
    """Test dump_yaml with tuple keys."""
    obj = {("a", "b"): 1, ("c", "d"): 2}
    file_path = tmp_path / "tuple_key.yaml"
    dump_yaml(obj, file_path)

    # Load and check tuple keys are normalized
    loaded = load_yaml(file_path)
    assert loaded[("a", "b")] == 1
    assert loaded[("c", "d")] == 2


def test_dump_yaml_with_path_object_converts_to_str(tmp_path: Path):
    """Test dump_yaml serializes Path objects as strings."""
    path1 = Path("/path/one")
    path2 = Path("/path/two")
    obj = {"path1": path1, "path2": path2}
    file_path = tmp_path / "paths.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert loaded["path1"] == str(path1)
    assert loaded["path2"] == str(path2)


def test_dump_yaml_sort_keys(tmp_path: Path):
    """Test dump_yaml with sort_keys option."""
    obj = {"z": 1, "a": 2, "m": 3}
    file_path = tmp_path / "sorted.yaml"
    dump_yaml(obj, file_path, sort_keys=True)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Keys should be in order a, m, z
    pos_a = content.find("a:")
    pos_m = content.find("m:")
    pos_z = content.find("z:")
    assert pos_a < pos_m < pos_z


def test_load_yaml_returns_dict(tmp_path: Path):
    """Test load_yaml returns a dict for dict data."""
    obj = {"key": "value"}
    file_path = tmp_path / "dict.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert isinstance(loaded, dict)
    assert loaded["key"] == "value"


def test_load_yaml_returns_list(tmp_path: Path):
    """Test load_yaml returns a list for list data."""
    obj = [1, 2, 3]
    file_path = tmp_path / "list.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert isinstance(loaded, list)
    assert loaded == [1, 2, 3]


def test_load_yaml_returns_string(tmp_path: Path):
    """Test load_yaml returns a string for string data."""
    obj = "just a string"
    file_path = tmp_path / "string.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert loaded == "just a string"


def test_load_yaml_normalizes_tuple_keys_in_nested(tmp_path: Path):
    """Test load_yaml normalizes tuple keys in nested dicts."""
    obj = {"outer": {("inner", "key"): "value"}}
    file_path = tmp_path / "nested_tuple.yaml"
    dump_yaml(obj, file_path)

    loaded = load_yaml(file_path)
    assert "outer" in loaded
    assert ("inner", "key") in loaded["outer"]
    assert loaded["outer"][("inner", "key")] == "value"
