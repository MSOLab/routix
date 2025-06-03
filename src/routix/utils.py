from pathlib import Path


def object_to_yaml(obj: object, file_path: Path, encoding="utf-8") -> None:
    import yaml  # Import here to avoid dependency issues

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding=encoding) as writer:
        yaml.safe_dump(obj, writer, default_flow_style=False)


def object_to_json(obj: object, file_path: Path, encoding="utf-8") -> None:
    import json  # Import here to avoid dependency issues

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding=encoding) as writer:
        json.dump(obj, writer, indent=2, ensure_ascii=False)
