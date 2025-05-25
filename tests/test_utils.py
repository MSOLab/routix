import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.routix.constants import SubroutineFlowKeys
from src.routix.dynamic_data_object import DynamicDataObject
from src.routix.utils import parse_step, safe_save_yaml


class TestParseStep:
    """Tests for the parse_step function"""

    def test_parse_step_explicit_format(self):
        """Test explicit format: { "method": "foo", "params": { "x": 1 } }"""
        step_data = {
            SubroutineFlowKeys.METHOD: "test_method",
            SubroutineFlowKeys.KWARGS: {"param1": "value1", "param2": 42},
        }
        step = DynamicDataObject(step_data)

        method_name, kwargs_dict = parse_step(step)

        assert method_name == "test_method"
        assert kwargs_dict == {"param1": "value1", "param2": 42}

    def test_parse_step_implicit_format(self):
        """Test implicit format: { "method": "foo", "x": 1 }"""
        step_data = {
            SubroutineFlowKeys.METHOD: "test_method",
            "param1": "value1",
            "param2": 42,
        }
        step = DynamicDataObject(step_data)

        method_name, kwargs_dict = parse_step(step)

        assert method_name == "test_method"
        assert kwargs_dict == {"param1": "value1", "param2": 42}

    def test_parse_step_empty_params_explicit(self):
        """Test empty parameters with explicit format"""
        step_data = {
            SubroutineFlowKeys.METHOD: "test_method",
            SubroutineFlowKeys.KWARGS: {},
        }
        step = DynamicDataObject(step_data)

        method_name, kwargs_dict = parse_step(step)

        assert method_name == "test_method"
        assert kwargs_dict == {}

    def test_parse_step_empty_params_implicit(self):
        """Test empty parameters with implicit format"""
        step_data = {SubroutineFlowKeys.METHOD: "test_method"}
        step = DynamicDataObject(step_data)

        method_name, kwargs_dict = parse_step(step)

        assert method_name == "test_method"
        assert kwargs_dict == {}

    def test_parse_step_missing_method_raises_error(self):
        """Test that ValueError is raised when method key is missing"""
        step_data = {"param1": "value1"}
        step = DynamicDataObject(step_data)

        with pytest.raises(ValueError, match="Method name not found in step data"):
            parse_step(step)

    def test_parse_step_mixed_params(self):
        """Test when both params key and other keys are present - params takes priority"""
        step_data = {
            SubroutineFlowKeys.METHOD: "test_method",
            SubroutineFlowKeys.KWARGS: {"param1": "from_params"},
            "param1": "from_direct",
            "param2": "direct_only",
        }
        step = DynamicDataObject(step_data)

        method_name, kwargs_dict = parse_step(step)

        assert method_name == "test_method"
        assert kwargs_dict == {"param1": "from_params"}  # params key takes priority


class TestSafeSaveYaml:
    """Tests for the safe_save_yaml function"""

    def setup_method(self):
        """Set up temporary directory before each test"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up temporary directory after each test"""
        self.temp_dir.cleanup()

    def test_save_dynamic_data_object(self):
        """Test saving DynamicDataObject"""
        data = DynamicDataObject({"name": "test", "value": 42})
        file_path = self.temp_path / "test_ddo.yaml"

        with patch.object(data, "to_yaml") as mock_save:
            with patch("builtins.print"):  # suppress print output
                safe_save_yaml(data, file_path)

            mock_save.assert_called_once_with(file_path, encoding="utf-8")

    def test_save_list_of_dynamic_data_objects(self):
        """Test saving list[DynamicDataObject]"""
        data_list = [
            DynamicDataObject({"id": 1, "name": "item1"}),
            DynamicDataObject({"id": 2, "name": "item2"}),
        ]
        file_path = self.temp_path / "test_list.yaml"

        with patch("builtins.print"):  # suppress print output
            safe_save_yaml(data_list, file_path)

        # check saved file
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        expected = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        assert loaded_data == expected

    def test_save_mixed_list(self):
        """Test saving mixed type list"""
        data_list = [
            DynamicDataObject({"id": 1, "name": "item1"}),
            {"id": 2, "name": "item2"},  # regular dict
            "string_item",
        ]
        file_path = self.temp_path / "test_mixed.yaml"

        with patch("builtins.print"):  # suppress print output
            safe_save_yaml(data_list, file_path)

        # check saved file
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        expected = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"},
            "string_item",
        ]
        assert loaded_data == expected

    def test_save_dict_data(self):
        """Test saving regular dict (converted to DynamicDataObject)"""
        data = {"name": "test", "nested": {"value": 42}}
        file_path = self.temp_path / "test_dict.yaml"

        with patch("builtins.print"):  # suppress print output
            safe_save_yaml(data, file_path)

        # check saved file
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data

    def test_save_creates_parent_directories(self):
        """Test automatic creation of parent directories"""
        data = DynamicDataObject({"test": "data"})
        nested_path = self.temp_path / "nested" / "deep" / "file.yaml"

        with patch.object(data, "to_yaml"):
            with patch("builtins.print"):  # suppress print output
                safe_save_yaml(data, nested_path)

        # check that parent directory was created
        assert nested_path.parent.exists()

    def test_save_recursive_conversion(self):
        """Test recursive conversion (when from_obj returns a list)"""
        data = [{"id": 1}, {"id": 2}]  # regular dict list
        file_path = self.temp_path / "recursive.yaml"

        with patch("builtins.print"):  # suppress print output
            safe_save_yaml(data, file_path)

        # check saved file
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data

    def test_save_empty_list(self):
        """Test saving empty list"""
        data = []
        file_path = self.temp_path / "empty.yaml"

        with patch("builtins.print"):  # suppress print output
            safe_save_yaml(data, file_path)

        # check saved file
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == []

    def test_save_with_custom_encoding(self):
        """Test custom encoding"""
        data = DynamicDataObject({"english": "test"})
        file_path = self.temp_path / "encoding.yaml"

        with patch.object(data, "to_yaml") as mock_save:
            with patch("builtins.print"):  # suppress print output
                safe_save_yaml(data, file_path, encoding="utf-16")

            mock_save.assert_called_once_with(file_path, encoding="utf-16")
