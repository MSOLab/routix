import re
from pathlib import Path
from typing import Any, Literal

from .yaml import dump_yaml, load_yaml

Zone = Literal["final", "progress", "report"]
Scope = Literal["run", "scenario", "instance"]
LogRole = Literal[
    "main",
    "multi_scenario_runner",
    "multi_instance_runner",
    "single_instance_runner",
    "subroutine_controller",
    "algorithm",
]

_DEFAULT_SCHEMA_PATH = Path(__file__).parent / "_default_artifact_layout.yaml"
_FREE_PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class ArtifactLayout:
    """Schema manager for an experiment's output directory.

    Resolves `(scope, kind, scenario_name?, instance_name?, ...)` into concrete
    `Path` values using a yaml schema. Instance-scope artifacts are routed to
    one of three zones: `final`, `progress`, or `report`.
    """

    def __init__(
        self,
        *,
        run_root: Path,
        run_id: str,
        schema_path: Path | None = None,
    ) -> None:
        self._run_root = Path(run_root)
        self._run_id = run_id
        self._schema_path = Path(schema_path) if schema_path else _DEFAULT_SCHEMA_PATH
        schema = load_yaml(self._schema_path)
        self._schema_version: int = schema.get("schema_version", 1)
        self._scopes: list[dict[str, Any]] = list(schema.get("scopes", []))
        self._zones: dict[str, str] = dict(
            schema.get("zones", {}).get(
                "instance", {"final": "", "progress": "progress", "report": "report"}
            )
        )
        self._logs: dict[str, dict[str, str]] = {}
        for entry in schema.get("logs", []):
            self._logs[entry["role"]] = {
                "scope": entry["scope"],
                "file_template": entry["file_template"],
            }
        self._artifacts: dict[str, dict[str, Any]] = {}
        for entry in schema.get("artifacts", []):
            kind = entry["kind"]
            scope = entry["scope"]
            zone = entry.get("zone")
            self._validate_zone_against_scope(kind=kind, scope=scope, zone=zone)
            stored: dict[str, Any] = {
                "scope": scope,
                "file_template": entry["file_template"],
            }
            if scope == "instance":
                stored["zone"] = zone
            self._artifacts[kind] = stored
        self._scenarios_seen: set[str] = set()

    # ---- scope path -------------------------------------------------------

    def run_dir(self) -> Path:
        self._run_root.mkdir(parents=True, exist_ok=True)
        return self._run_root

    def scenario_dir(self, scenario_name: str) -> Path:
        """Register and return the scenario directory.

        Each call registers `scenario_name`; calling twice with the same name
        raises `ValueError` to prevent silent overwrite of experiment results
        (see doc § 7.3 stage-2 defense).
        """
        if scenario_name in self._scenarios_seen:
            raise ValueError(
                f"scenario name {scenario_name!r} already registered with this "
                "layout. Each scenario must have a unique name to prevent "
                "silent overwrite of experiment results."
            )
        self._scenarios_seen.add(scenario_name)
        return self._scenario_path(scenario_name)

    def instance_dir(self, scenario_name: str, instance_name: str) -> Path:
        path = self._instance_path(scenario_name, instance_name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ---- zone path (instance scope only) ----------------------------------

    def zone_dir(
        self, zone: Zone, *, scenario_name: str, instance_name: str
    ) -> Path:
        path = self._zone_path(zone, scenario_name=scenario_name, instance_name=instance_name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ---- log --------------------------------------------------------------

    def log_path(
        self,
        role: LogRole,
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
    ) -> Path:
        if role not in self._logs:
            raise KeyError(f"unknown log role: {role!r}")
        entry = self._logs[role]
        file_name = self._render_file_name(
            entry["file_template"],
            scenario_name=scenario_name,
            instance_name=instance_name,
        )
        return self._scope_dir(
            entry["scope"],
            scenario_name=scenario_name,
            instance_name=instance_name,
            label=f"log role {role!r}",
        ) / file_name

    # ---- artifact ---------------------------------------------------------

    def artifact_path(
        self,
        kind: str,
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
        **placeholders: str,
    ) -> Path:
        if kind not in self._artifacts:
            raise KeyError(f"unknown artifact kind: {kind!r}")
        entry = self._artifacts[kind]
        scope: str = entry["scope"]
        file_name = self._render_file_name(
            entry["file_template"],
            scenario_name=scenario_name,
            instance_name=instance_name,
            **placeholders,
        )
        if scope == "instance":
            if scenario_name is None or instance_name is None:
                raise ValueError(
                    f"artifact kind {kind!r} requires scenario_name and "
                    "instance_name"
                )
            target_zone: Zone = entry["zone"]
            return (
                self.zone_dir(
                    target_zone,
                    scenario_name=scenario_name,
                    instance_name=instance_name,
                )
                / file_name
            )
        return self._scope_dir(
            scope,
            scenario_name=scenario_name,
            instance_name=instance_name,
            label=f"artifact kind {kind!r}",
        ) / file_name

    # ---- subclass / overlay extension -------------------------------------

    def register_kind(
        self,
        kind: str,
        *,
        scope: Scope,
        zone: Zone | None = None,
        file_template: str,
    ) -> None:
        """Register a new artifact kind.

        Zone rule (matches yaml schema, fail-fast):
        - scope="instance": zone is REQUIRED. Passing None raises ValueError.
        - scope="run"/"scenario": zone is FORBIDDEN. Passing non-None raises
          ValueError.

        Rationale: zone classifies SSOT contract (final vs progress vs
        report). Forcing each kind to declare zone explicitly prevents new
        kinds from silently landing in `final` (the most protected zone).
        """
        if kind in self._artifacts:
            raise ValueError(
                f"artifact kind {kind!r} already registered; "
                "cannot redefine via register_kind"
            )
        self._validate_zone_against_scope(kind=kind, scope=scope, zone=zone)
        entry: dict[str, Any] = {"scope": scope, "file_template": file_template}
        if scope == "instance":
            entry["zone"] = zone
        self._artifacts[kind] = entry

    # ---- discovery --------------------------------------------------------

    def find_artifacts(
        self,
        kind: str,
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
    ) -> list[Path]:
        if kind not in self._artifacts:
            raise KeyError(f"unknown artifact kind: {kind!r}")
        entry = self._artifacts[kind]
        scope: str = entry["scope"]
        ctx = self._build_context(
            scenario_name=scenario_name, instance_name=instance_name
        )
        pattern = entry["file_template"].format_map(_SafeDict(ctx))
        pattern = _FREE_PLACEHOLDER_RE.sub("*", pattern)
        if scope == "instance":
            if scenario_name is None or instance_name is None:
                raise ValueError(
                    f"artifact kind {kind!r} requires scenario_name and "
                    "instance_name for find_artifacts"
                )
            target_zone: Zone = entry["zone"]
            search_dir = self._zone_path(
                target_zone,
                scenario_name=scenario_name,
                instance_name=instance_name,
            )
        elif scope == "scenario":
            if scenario_name is None:
                raise ValueError(
                    f"artifact kind {kind!r} requires scenario_name for find_artifacts"
                )
            search_dir = self._run_root / scenario_name
        else:
            search_dir = self._run_root
        if not search_dir.exists():
            return []
        return sorted(search_dir.glob(pattern))

    # ---- serialize --------------------------------------------------------

    def stamp(self) -> Path:
        """Write the current schema (default + register_kind additions) to
        `<run_dir>/<run_id>_artifact_layout.yaml` and return its path."""
        out_path = self.run_dir() / f"{self._run_id}_artifact_layout.yaml"
        payload: dict[str, Any] = {
            "schema_version": self._schema_version,
            "scopes": self._scopes,
            "zones": {"instance": dict(self._zones)},
            "logs": [
                {
                    "scope": entry["scope"],
                    "role": role,
                    "file_template": entry["file_template"],
                }
                for role, entry in self._logs.items()
            ],
            "artifacts": [
                self._artifact_entry_for_dump(kind, entry)
                for kind, entry in self._artifacts.items()
            ],
        }
        dump_yaml(payload, out_path)
        return out_path

    # ---- internals --------------------------------------------------------

    def _scenario_path(self, scenario_name: str) -> Path:
        path = self._run_root / scenario_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _instance_path(self, scenario_name: str, instance_name: str) -> Path:
        return self._run_root / scenario_name / instance_name

    def _zone_path(
        self, zone: Zone, *, scenario_name: str, instance_name: str
    ) -> Path:
        if zone not in self._zones:
            raise ValueError(
                f"unknown zone {zone!r}; expected one of {sorted(self._zones)}"
            )
        base = self._instance_path(scenario_name, instance_name)
        subdir = self._zones[zone]
        return base / subdir if subdir else base

    def _scope_dir(
        self,
        scope: str,
        *,
        scenario_name: str | None,
        instance_name: str | None,
        label: str,
    ) -> Path:
        if scope == "run":
            return self.run_dir()
        if scope == "scenario":
            if scenario_name is None:
                raise ValueError(f"{label} requires scenario_name")
            return self._scenario_path(scenario_name)
        if scope == "instance":
            if scenario_name is None or instance_name is None:
                raise ValueError(
                    f"{label} requires scenario_name and instance_name"
                )
            return self.instance_dir(scenario_name, instance_name)
        raise ValueError(f"unknown scope {scope!r} for {label}")

    def _build_context(
        self,
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
        **placeholders: str,
    ) -> dict[str, str]:
        ctx: dict[str, str] = {"run_id": self._run_id}
        if scenario_name is not None:
            ctx["scenario_name"] = scenario_name
        if instance_name is not None:
            ctx["instance_name"] = instance_name
        ctx.update(placeholders)
        return ctx

    def _render_file_name(
        self,
        file_template: str,
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
        **placeholders: str,
    ) -> str:
        ctx = self._build_context(
            scenario_name=scenario_name,
            instance_name=instance_name,
            **placeholders,
        )
        rendered = file_template.format_map(_SafeDict(ctx))
        missing = _FREE_PLACEHOLDER_RE.findall(rendered)
        if missing:
            raise KeyError(
                f"missing placeholders {missing} for template {file_template!r}"
            )
        return rendered

    @staticmethod
    def _artifact_entry_for_dump(
        kind: str, entry: dict[str, Any]
    ) -> dict[str, Any]:
        out: dict[str, Any] = {"scope": entry["scope"]}
        # zone is present iff scope=="instance" (validated at load /
        # register_kind time). Preserve the same invariant on dump.
        if entry["scope"] == "instance":
            out["zone"] = entry["zone"]
        out["kind"] = kind
        out["file_template"] = entry["file_template"]
        return out

    @staticmethod
    def _validate_zone_against_scope(
        *, kind: str, scope: str, zone: str | None
    ) -> None:
        """Enforce: scope=="instance" requires zone; scope=="run"/"scenario"
        forbids zone. See doc § 3.1 zone rule."""
        if scope == "instance":
            if zone is None:
                raise ValueError(
                    f"artifact kind {kind!r} has scope='instance' but no "
                    "zone. zone is required for instance-scope kinds and "
                    "must be one of 'final' / 'progress' / 'report'."
                )
            if zone not in ("final", "progress", "report"):
                raise ValueError(
                    f"artifact kind {kind!r} has unknown zone {zone!r}; "
                    "expected 'final' / 'progress' / 'report'."
                )
        elif scope in ("run", "scenario"):
            if zone is not None:
                raise ValueError(
                    f"artifact kind {kind!r} has scope={scope!r} which does "
                    f"not support zone, but zone={zone!r} was given. "
                    "Remove the zone field."
                )
        else:
            raise ValueError(
                f"artifact kind {kind!r} has unknown scope {scope!r}; "
                "expected 'run' / 'scenario' / 'instance'."
            )
