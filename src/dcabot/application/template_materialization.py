"""Materialize bound templates into validated configs, with file persistence.

Materialization merges binding overrides onto the profile config and runs the
full ``Config.parse``, so cross-field rules (grid, minima) hold. The file
store keeps templates as canonical JSON documents with atomic writes and
hash-verified reads; import/export move bytes, never live objects.
"""

from dataclasses import dataclass
import hashlib
import json
import os
import re
from pathlib import Path

from dcabot.application.historical_profiles import load_historical_profile_config
from dcabot.application.strategy_template import (
    StrategyTemplate,
    StrategyTemplateError,
    new_strategy_template,
)
from dcabot.application.template_profile_binding import TemplateBinding
from dcabot.domain.config import Config


_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_MAX_IMPORT_BYTES = 65_536


class TemplateMaterializationError(ValueError):
    """Raised when a binding cannot materialize or a template cannot persist."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class MaterializedConfig:
    """Validated merged config plus its canonical hash; still not a run."""

    profile_id: str
    binding_id: str
    config: dict[str, object]
    config_hash: str


def materialize_binding(binding: TemplateBinding, root: Path) -> MaterializedConfig:
    """Merge binding overrides onto the profile config and validate fully."""

    if not isinstance(binding, TemplateBinding) or binding.status != "BOUND":
        raise TemplateMaterializationError(
            "TEMPLATE_MATERIALIZE_BINDING_INVALID", "Binding kaydı geçersiz."
        )
    if not isinstance(root, Path):
        raise TemplateMaterializationError(
            "TEMPLATE_MATERIALIZE_ROOT_INVALID", "Config kökü geçersiz."
        )
    try:
        _, raw_config = load_historical_profile_config(root, binding.profile_id)
    except (OSError, ValueError) as error:
        raise TemplateMaterializationError(
            "TEMPLATE_MATERIALIZE_CONFIG_INVALID",
            "Profile config yüklenemedi.",
        ) from error
    merged: dict[str, object] = dict(raw_config)
    for key, value in binding.params:
        merged[key] = value
    try:
        Config.parse(merged)
    except ValueError as error:
        raise TemplateMaterializationError(
            "TEMPLATE_MATERIALIZE_CONFIG_INVALID",
            f"Birleşmiş config geçersiz: {error}.",
        ) from error
    canonical = json.dumps(
        merged,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return MaterializedConfig(
        profile_id=binding.profile_id,
        binding_id=binding.binding_id,
        config=merged,
        config_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def diff_templates(
    old: StrategyTemplate, new: StrategyTemplate
) -> tuple[tuple[str, object, object], ...]:
    """Diff two template payloads canonically; None marks a missing side."""

    if not isinstance(old, StrategyTemplate) or not isinstance(new, StrategyTemplate):
        raise TemplateMaterializationError(
            "TEMPLATE_DIFF_INVALID", "Diff için iki template gerekir."
        )
    old_payload = json.loads(old.payload_json)
    new_payload = json.loads(new.payload_json)
    rows: list[tuple[str, object, object]] = []
    for key in sorted(set(old_payload) | set(new_payload)):
        before = old_payload.get(key)
        after = new_payload.get(key)
        if before != after:
            rows.append((key, before, after))
    return tuple(rows)


class TemplateFileStore:
    """Atomic canonical-JSON template files under one directory."""

    def __init__(self, directory: Path) -> None:
        if not isinstance(directory, Path):
            raise TemplateMaterializationError(
                "TEMPLATE_STORE_INVALID", "Store dizini geçersiz."
            )
        self._directory = directory

    def save(self, template: StrategyTemplate) -> Path:
        """Validate and atomically persist one template; returns its path."""

        if not isinstance(template, StrategyTemplate):
            raise TemplateMaterializationError(
                "TEMPLATE_STORE_INVALID", "Template kaydı geçersiz."
            )
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._path(template.template_id)
        document = json.dumps(
            {
                "declared_capabilities": list(template.declared_capabilities),
                "payload": json.loads(template.payload_json),
                "payload_sha256": template.payload_sha256,
                "schema_version": template.schema_version,
                "template_id": template.template_id,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(document, encoding="utf-8")
        os.replace(tmp_path, path)
        return path

    def load(self, template_id: str) -> StrategyTemplate:
        """Load and hash-verify one template by ID."""

        path = self._path(template_id)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise TemplateMaterializationError(
                "TEMPLATE_NOT_FOUND", "Template bulunamadı."
            ) from error
        try:
            template = new_strategy_template(
                template_id=document["template_id"],
                schema_version=document["schema_version"],
                payload=document["payload"],
                declared_capabilities=tuple(document["declared_capabilities"]),
            )
        except (KeyError, TypeError, StrategyTemplateError) as error:
            raise TemplateMaterializationError(
                "TEMPLATE_CORRUPT", "Template dosyası doğrulanamadı."
            ) from error
        if template.template_id != template_id or (
            document.get("payload_sha256") not in (None, template.payload_sha256)
        ):
            raise TemplateMaterializationError(
                "TEMPLATE_CORRUPT", "Template kimliği/hash eşleşmiyor."
            )
        return template

    def list_ids(self) -> tuple[str, ...]:
        """List stored template IDs in canonical order."""

        if not self._directory.is_dir():
            return ()
        ids = [
            path.stem
            for path in self._directory.iterdir()
            if path.is_file() and path.suffix == ".json"
        ]
        return tuple(sorted(ids))

    def import_bytes(self, raw: bytes) -> StrategyTemplate:
        """Validate and persist one imported template document."""

        if not isinstance(raw, bytes) or len(raw) > _MAX_IMPORT_BYTES:
            raise TemplateMaterializationError(
                "TEMPLATE_IMPORT_INVALID", "Import boyutu sınırı aşıyor."
            )
        try:
            document = json.loads(raw.decode("utf-8"))
            template = new_strategy_template(
                template_id=document["template_id"],
                schema_version=document["schema_version"],
                payload=document["payload"],
                declared_capabilities=tuple(document["declared_capabilities"]),
            )
        except (UnicodeDecodeError, ValueError, KeyError, TypeError, StrategyTemplateError) as error:
            raise TemplateMaterializationError(
                "TEMPLATE_IMPORT_INVALID", "Import doğrulanamadı."
            ) from error
        self.save(template)
        return template

    def export_bytes(self, template_id: str) -> bytes:
        """Export one stored template as canonical bytes."""

        path = self._path(template_id)
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise TemplateMaterializationError(
                "TEMPLATE_NOT_FOUND", "Template bulunamadı."
            ) from error
        if len(raw) > _MAX_IMPORT_BYTES:
            raise TemplateMaterializationError(
                "TEMPLATE_CORRUPT", "Template dosyası sınırın üstünde."
            )
        self.load(template_id)
        return raw

    def _path(self, template_id: str) -> Path:
        if not isinstance(template_id, str) or _ID.fullmatch(template_id) is None:
            raise TemplateMaterializationError(
                "TEMPLATE_ID_INVALID", "Template kimliği geçersiz."
            )
        return self._directory / f"{template_id}.json"
