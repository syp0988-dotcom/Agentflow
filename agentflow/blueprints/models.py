"""Core data models for the Blueprint system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FileSpec:
    """A single file to be created/modified as part of a blueprint.

    ``content_template`` is a Jinja2 template string (inline in the YAML),
    while ``template_ref`` points to an external ``.j2`` file in the
    blueprint's ``templates/`` directory.  At most one of the two is set.
    """

    path: str
    """Relative path from project root, e.g. ``app/main.py``.
    May contain Jinja2 expressions like ``{{ package_name }}/main.py``."""

    content_template: str = ""
    """Inline Jinja2 template for this file's content."""

    template_ref: str | None = None
    """Path (relative to the blueprint YAML directory) to an external template."""

    type: str = "create"
    """``"create"`` — fresh file, ``"modify"`` — edit existing, ``"reference"`` — informational."""

    description: str = ""
    """Human-readable description of this file's purpose."""

    condition: str | None = None
    """Variable name; file is only included when the variable is truthy.
    E.g. ``"auth_enabled"`` means skip this file unless ``auth_enabled`` is set."""

    encoding: str = "utf-8"
    """File encoding."""


@dataclass
class VariableDef:
    """Blueprint variable definition."""

    name: str
    description: str = ""
    default: Any = None
    required: bool = False
    choices: list[Any] | None = None


@dataclass
class Blueprint:
    """A complete project blueprint loaded from a YAML file."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"

    # ── Matching ──────────────────────────────────────────────────────
    keywords: list[str] = field(default_factory=list)
    """Keywords that boost this blueprint's match score."""

    frameworks: list[str] = field(default_factory=list)
    """Explicit framework names mentioned by the user (e.g. ``["fastapi"]``)."""

    goal_types: list[str] = field(default_factory=lambda: ["project"])
    """Goal types this blueprint applies to."""

    exclude_keywords: list[str] = field(default_factory=list)
    """Keywords that disqualify this blueprint (e.g. ``["flask"]`` for a FastAPI blueprint)."""

    # ── Variables ─────────────────────────────────────────────────────
    variables: list[VariableDef] = field(default_factory=list)
    """Variables required/recommended by this blueprint."""

    # ── Dependencies ──────────────────────────────────────────────────
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    """Package dependencies keyed by package manager.
    E.g. ``{"pip": ["fastapi>=0.110.0"], "npm": ["react"]}``."""

    # ── Files ─────────────────────────────────────────────────────────
    files: list[FileSpec] = field(default_factory=list)
    """All files (templates) that make up this blueprint."""

    # ── Metadata ──────────────────────────────────────────────────────
    source_path: str = ""
    """Path to the YAML file this blueprint was loaded from."""

    @classmethod
    def from_yaml(cls, path: str | Path) -> Blueprint:
        """Load a Blueprint from a YAML file.

        This method performs a raw load of the core metadata and file specs.
        Variable interpolation of ``path`` fields happens later during
        :meth:`BlueprintLoader.render`.
        """
        import yaml

        raw_path = Path(path)
        with open(raw_path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        def _parse_variables(vlist: list[dict[str, Any]] | None) -> list[VariableDef]:
            if not vlist:
                return []
            result: list[VariableDef] = []
            for v in vlist:
                result.append(VariableDef(
                    name=v["name"],
                    description=v.get("description", ""),
                    default=v.get("default"),
                    required=v.get("required", False),
                    choices=v.get("choices"),
                ))
            return result

        def _parse_files(flist: list[dict[str, Any]] | None) -> list[FileSpec]:
            if not flist:
                return []
            result: list[FileSpec] = []
            for f in flist:
                content = f.get("content", "")
                if content is None:
                    content = ""
                result.append(FileSpec(
                    path=f["path"],
                    content_template=content,
                    template_ref=f.get("template_ref"),
                    type=f.get("type", "create"),
                    description=f.get("description", ""),
                    condition=f.get("condition"),
                    encoding=f.get("encoding", "utf-8"),
                ))
            return result

        match_cfg = data.get("match", {})
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            keywords=match_cfg.get("keywords", []),
            frameworks=match_cfg.get("frameworks", []),
            goal_types=match_cfg.get("goal_types", ["project"]),
            exclude_keywords=match_cfg.get("exclude_keywords", []),
            variables=_parse_variables(data.get("variables")),
            dependencies=data.get("dependencies", {}),
            files=_parse_files(data.get("files")),
            source_path=str(raw_path.resolve()),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (for logging / debugging)."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "frameworks": self.frameworks,
            "file_count": len(self.files),
            "source": self.source_path,
        }
