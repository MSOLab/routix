from logging import warning
from pathlib import Path, PurePath
from typing import Any

import yaml


def object_to_yaml(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    """Saves a Python object to a YAML file, ensuring Path objects are saved as strings.

    Args:
        obj (Any): The Python object to save.
            If it has a `to_dict` method, that will be used to convert it to a dictionary.
        path (Path): The file path where the YAML will be saved.
        encoding (str, optional): The encoding to use for the file. Defaults to "utf-8".
    """

    # Add a representer to handle pathlib.Path objects gracefully
    def path_representer(dumper: yaml.Dumper, data: Path) -> yaml.ScalarNode:
        return dumper.represent_scalar("!str", str(data))

    yaml.add_representer(Path, path_representer)

    # If the object has a to_dict method, use it to get a clean dictionary
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        data_to_dump = obj.to_dict()
    else:
        data_to_dump = obj

    with open(path, "w", encoding=encoding) as f:
        yaml.dump(data_to_dump, f, default_flow_style=False, sort_keys=False)

    # It's good practice to remove the representer if it's not needed globally
    yaml.Dumper.yaml_representers.pop(Path, None)


def yaml_to_object(path: PurePath, encoding: str = "utf-8") -> Any:
    """Loads a Python object from a YAML file.

    Args:
        path (PurePath): The file path from which to load the YAML.
        encoding (str, optional): The encoding to use for the file. Defaults to "utf-8".

    Returns:
        Any: The Python object loaded from the YAML file.
    """
    with open(path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def tuple_to_pyyaml_key(d: dict) -> dict:
    """
    Converts tuple-format dictionary keys to the format '!!python/tuple [j0,i0,i0_1]'.

    Reference: solution_manager.py row 66
    """
    warning(
        "DEPRECATED: tuple_to_pyyaml_key will be removed in a future version. Use "
        "dump_yaml() instead - it automatically handles tuple keys via PrettyKeyDumper."
    )
    new_dict = {}
    for k, v in d.items():
        if isinstance(k, tuple):
            # Join internal elements with commas and strip
            items = ", ".join(str(item).strip() for item in k)
            new_dict[f"!!python/tuple [{items}]"] = v
        else:
            new_dict[k] = v
    return new_dict


def pyyaml_key_to_tuple(d: dict) -> dict:
    """
    Converts keys in the format '!!python/tuple [j0,i0,i0_1]' to tuples.

    Reference: solution_manager.py row 66
    """
    import re

    warning(
        "DEPRECATED: pyyaml_key_to_tuple will be removed in a future version. Use "
        "load_yaml() instead - it automatically normalizes tuple keys via PrettyKeyLoader."
    )
    tuple_key_pattern = re.compile(r"^!!python/tuple \[(.*)\]$")
    new_dict = {}
    for k, v in d.items():
        m = tuple_key_pattern.match(k)
        if m:
            # Split internal elements by comma and strip
            items = [item.strip() for item in m.group(1).split(",")]
            new_dict[tuple(items)] = v
        else:
            new_dict[k] = v
    return new_dict


class PrettyKeyDumper(yaml.SafeDumper):
    """
    - Represent tuple as standard YAML sequence
    - Force flow style [a, b]
    """


def _represent_tuple_as_flow_seq(dumper: PrettyKeyDumper, data: tuple):
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq", list(data), flow_style=True
    )


PrettyKeyDumper.add_representer(tuple, _represent_tuple_as_flow_seq)


def dump_yaml(
    data: Any, path: Path, *, sort_keys: bool = False, encoding: str = "utf-8"
) -> None:
    """
    Pretty YAML dump (supports tuple key)
    """
    with open(path, "w", encoding=encoding) as f:
        yaml.dump(
            data,
            f,
            Dumper=PrettyKeyDumper,
            sort_keys=sort_keys,
            allow_unicode=True,
            default_flow_style=False,
            width=10_000,
        )


class PrettyKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.nodes.MappingNode):
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )

        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=True)

            if isinstance(key, list):
                key = tuple(key)

            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping


def load_yaml(path: Path, encoding: str = "utf-8") -> Any:
    with open(path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=PrettyKeyLoader)
