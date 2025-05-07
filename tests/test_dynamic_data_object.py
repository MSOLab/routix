import os
import tempfile
import unittest
from pathlib import PurePath

from clad import DynamicDataObject


class TestDynamicDataObject(unittest.TestCase):
    def test_valid_initialization(self):
        data = DynamicDataObject({"name": "Alice", "age": 25})
        self.assertEqual(data.name, "Alice")
        self.assertEqual(data.age, 25)

    def test_invalid_key(self):
        with self.assertRaises(ValueError):
            _ = DynamicDataObject({"123notvalid": "fail"})

    def test_reserved_key(self):
        # 'from_obj' is a reserved class attribute.
        with self.assertRaises(ValueError):
            _ = DynamicDataObject({"from_obj": "conflict"})

    def test_from_obj_with_dict(self):
        obj = {"name": "Bob", "details": {"age": 30, "job": "Engineer"}}
        data = DynamicDataObject.from_obj(obj)
        self.assertEqual(data.name, "Bob")
        # details should be converted to a DynamicDataObject
        self.assertIsInstance(data.details, DynamicDataObject)
        self.assertEqual(data.details.age, 30)

    def test_from_obj_with_list(self):
        obj = ["a", {"b": "value"}]
        result = DynamicDataObject.from_obj(obj)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], "a")
        self.assertIsInstance(result[1], DynamicDataObject)
        self.assertEqual(result[1].b, "value")

    def test_to_obj(self):
        obj = {
            "name": "Charlie",
            "details": {"age": 40, "hobbies": ["golf", "reading"]},
        }
        data = DynamicDataObject.from_obj(obj)
        plain_obj = data.to_obj()
        # Check that the plain object has the expected nested structure
        self.assertEqual(plain_obj["name"], "Charlie")
        self.assertIsInstance(plain_obj["details"], dict)
        self.assertEqual(plain_obj["details"]["age"], 40)
        self.assertEqual(plain_obj["details"]["hobbies"], ["golf", "reading"])

    def test_repr(self):
        data = DynamicDataObject({"name": "Diana"})
        rep = repr(data)
        self.assertTrue(rep.startswith("DynamicDataObject("))
        self.assertIn("'name': 'Diana'", rep)

    def test_json_serialization_deserialization(self):
        obj = {"name": "Eve", "numbers": [1, 2, 3], "details": {"status": "active"}}
        data = DynamicDataObject.from_obj(obj)
        # Serialize to a temporary JSON file
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w+", suffix=".json"
        ) as tmp:
            tmp_file_path = PurePath(tmp.name)
            data.to_json(tmp_file_path)

        # Deserialize from the JSON file
        data_loaded = DynamicDataObject.from_json(tmp_file_path)
        self.assertEqual(data_loaded.name, "Eve")
        self.assertEqual(data_loaded.numbers, [1, 2, 3])
        self.assertIsInstance(data_loaded.details, DynamicDataObject)
        self.assertEqual(data_loaded.details.status, "active")
        os.remove(tmp_file_path)

    def test_nested_dict_conversion(self):
        obj = {"a": 1, "b": {"ba": 2, "bb": 3}}
        data = DynamicDataObject.from_obj(obj)

        # Check top-level attributes
        self.assertEqual(data.a, 1)
        self.assertIsInstance(data.b, DynamicDataObject)

        # Check nested attributes
        self.assertEqual(data.b.ba, 2)
        self.assertEqual(data.b.bb, 3)

    def test_list_of_dict_conversion(self):
        obj = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
        data = DynamicDataObject.from_obj(obj)

        # Check that the result is a list
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        # Check each item in the list
        self.assertIsInstance(data[0], DynamicDataObject)
        self.assertEqual(data[0].id, 1)
        self.assertEqual(data[0].value, "a")

        self.assertIsInstance(data[1], DynamicDataObject)
        self.assertEqual(data[1].id, 2)
        self.assertEqual(data[1].value, "b")

    def test_list_of_dict_in_dict_conversion(self):
        obj = {"items": [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]}
        data = DynamicDataObject.from_obj(obj)

        # Check that the result is a DynamicDataObject
        self.assertIsInstance(data, DynamicDataObject)
        self.assertIsInstance(data.items, list)
        self.assertEqual(len(data.items), 2)

        # Check each item in the list
        self.assertIsInstance(data.items[0], DynamicDataObject)
        self.assertEqual(data.items[0].id, 1)
        self.assertEqual(data.items[0].value, "a")

        self.assertIsInstance(data.items[1], DynamicDataObject)
        self.assertEqual(data.items[1].id, 2)
        self.assertEqual(data.items[1].value, "b")

    def test_dict_in_list_in_dict_in_list_conversion(self):
        obj = [
            {"id": 1, "value": "a", "details": [{"key": "k1", "val": "v1"}]},
            {"id": 2, "value": "b", "details": [{"key": "k2", "val": "v2"}]},
        ]
        data = DynamicDataObject.from_obj(obj)
        # Check that the result is a list
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        # Check each item in the list
        self.assertIsInstance(data[0], DynamicDataObject)
        self.assertEqual(data[0].id, 1)
        self.assertEqual(data[0].value, "a")
        self.assertIsInstance(data[0].details, list)
        self.assertEqual(len(data[0].details), 1)
        self.assertIsInstance(data[0].details[0], DynamicDataObject)
        self.assertEqual(data[0].details[0].key, "k1")
        self.assertEqual(data[0].details[0].val, "v1")
        self.assertEqual(data[1].id, 2)
        self.assertEqual(data[1].value, "b")
        # Check that the result is a DynamicDataObject
        self.assertIsInstance(data[1].details, list)
        self.assertEqual(len(data[1].details), 1)
        self.assertIsInstance(data[1].details[0], DynamicDataObject)
        self.assertEqual(data[1].details[0].key, "k2")
        self.assertEqual(data[1].details[0].val, "v2")


if __name__ == "__main__":
    unittest.main()
