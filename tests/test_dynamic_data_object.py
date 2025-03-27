import os
import tempfile
import unittest
from pathlib import PurePath

from clad.dynamic_data_object import DynamicDataObject


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


if __name__ == "__main__":
    unittest.main()
