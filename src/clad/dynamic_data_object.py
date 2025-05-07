import json
from pathlib import PurePath
from typing import Any, Self, Sequence


class DynamicDataObject:
    """
    A flexible container that allows dynamic assignment of attributes from nested dictionaries and lists.

    This class is designed to:
    - Wrap arbitrary nested dict/list-based structures into Python objects with dot-access (`obj.key`)
    - Convert back to plain dict/list structures with `.to_obj()`
    - Serialize/deserialize from JSON
    - Be initialized robustly: must be created with a dictionary using `__init__()`,
      and any nested or list structures should use the classmethods `from_obj()` or `from_json()`

    Examples:
    >>> obj = DynamicDataObject({'x': 1, 'y': {'z': 2}})
    >>> obj.y.z
    2
    >>> obj.to_obj()
    {'x': 1, 'y': {'z': 2}}
    """  # noqa: E501

    def __init__(self, param_dict: dict[str, Any]):
        if not isinstance(param_dict, dict):
            raise TypeError(
                "DynamicDataObject must be initialized with a dictionary"
                f", but got {type(param_dict).__name__}"
            )

        for key, value in param_dict.items():
            # Validate that key is a valid identifier
            if not isinstance(key, str) or not key.isidentifier():
                raise ValueError(
                    f"Invalid key: {key}. Keys must be valid string identifiers."
                )
            # Prevent conflicts with existing class attributes/methods
            if key in self.__class__.__dict__:
                raise ValueError(
                    f"Key '{key}' is reserved and cannot be used as an attribute."
                )
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self.to_obj())})"

    @classmethod
    def from_sequence(cls, sequence: Sequence[Any]) -> list[Self]:
        return [cls.from_obj(item) for item in sequence]

    @classmethod
    def from_dict(cls, dict_of_obj: dict[str, Any]) -> Self:
        return cls(
            {
                key: DynamicDataObject.from_obj(value)
                for key, value in dict_of_obj.items()
            }
        )

    @classmethod
    def from_obj(cls, obj: Any) -> Any:
        """Recursively converts dictionaries and lists into DynamicDataObject instances.

        Args:
            obj (Any): dictionary or list or any other object

        Raises:
            TypeError: If the object is of type bytes.

        Returns:
            Any: a class instance
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj  # Return basic types as-is
        elif isinstance(obj, bytes):
            raise TypeError("bytes type is not supported. Please decode or convert it.")
        elif isinstance(obj, Sequence):  # and not isinstance(obj, (str, bytes)):
            return cls.from_sequence(obj)
        elif isinstance(obj, list):
            return cls.from_sequence(obj)
        elif isinstance(obj, dict):
            return cls.from_dict(obj)
        return obj

    def to_obj(self) -> Any:
        """Recursively converts the DynamicDataObject and any nested DynamicDataObject
        instances back into plain dictionaries and lists.

        Returns:
            Any: a plain object that can be serialized directly to JSON.
        """

        def _convert(value: Any) -> Any:
            if isinstance(value, DynamicDataObject):
                return value.to_obj()
            elif isinstance(value, list):
                return [_convert(item) for item in value]
            elif isinstance(value, dict):
                return {key: _convert(val) for key, val in value.items()}
            return value

        return _convert(self.__dict__)

    @classmethod
    def from_json(cls, file_path: PurePath, encoding="utf-8") -> Any:
        """Deserializes a JSON file into a DynamicDataObject instance.

        Args:
            file_path (PurePath)

        Raises:
            RuntimeError: If an error occurs while reading the file.
            ValueError: If an error occurs while parsing the JSON data.

        Returns:
            Any: a class instance created from the JSON data in the file.
        """
        try:
            with open(file_path, "r", encoding=encoding) as file:
                json_data = json.load(file)
            return cls.from_obj(json_data)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Error reading from file {file_path}: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON from file {file_path}: {e}")

    def to_json(self, file_path: PurePath) -> None:
        """Serializes the object's data to a JSON file at the specified file path.

        Args:
            file_path (PurePath)
        """
        try:
            with open(file_path, "w", encoding="utf-8") as writer:
                json.dump(self.to_obj(), writer, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Error writing to file {file_path}: {e}")


def main():
    from pprint import pprint

    # Create an DynamicDataObject instance
    data = DynamicDataObject.from_obj(
        {
            "name": "John Doe",
            "age": 30,
            "job": {"title": "Software Engineer", "company": "Tech Corp"},
            "skills": ["Python", "JSON", "API Design"],
        }
    )
    pprint(data)


if __name__ == "__main__":
    main()
