from pathlib import Path, PurePath
from typing import Any

import yaml

YAML_STR_TAG = yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG
YAML_SEQ_TAG = yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG


class PrettyKeyDumper(yaml.SafeDumper):
    """
    - Represent tuple as standard YAML sequence
    - Force flow style [a, b]
    """


def _represent_tuple_as_flow_seq(dumper: PrettyKeyDumper, data: tuple):
    return dumper.represent_sequence(YAML_SEQ_TAG, list(data), flow_style=True)


PrettyKeyDumper.add_representer(tuple, _represent_tuple_as_flow_seq)


def _represent_path_as_str(dumper: PrettyKeyDumper, data: PurePath):
    return dumper.represent_scalar(YAML_STR_TAG, str(data))


PrettyKeyDumper.add_multi_representer(PurePath, _represent_path_as_str)


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


def load_yaml(path: PurePath, encoding: str = "utf-8") -> Any:
    with open(path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=PrettyKeyLoader)
