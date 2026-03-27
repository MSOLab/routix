from pathlib import Path

from routix.io.yaml import dump_yaml, load_yaml


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
