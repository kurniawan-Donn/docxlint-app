"""Config validation, hashing, import/export Phase 7."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from ..config import DEFAULT_LIMITS


@dataclass
class ConfigValidationReport:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def compute_config_hash(config: Dict[str, Any]) -> str:
    normalized = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _require_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML tidak tersedia.")


def parse_yaml(data: bytes) -> Tuple[Dict[str, Any], ConfigValidationReport]:
    if len(data) > DEFAULT_LIMITS.max_file_size_mb * 1024 * 1024:
        return {}, ConfigValidationReport(
            ok=False, errors=["CONFIG_TOO_LARGE"],
        )
    try:
        _require_yaml()
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {}, ConfigValidationReport(
            ok=False, errors=["CONFIG_ENCODING_INVALID"],
        )
    try:
        loaded = yaml.safe_load(text)
    except Exception as exc:
        return {}, ConfigValidationReport(
            ok=False, errors=[f"CONFIG_PARSE_ERROR: {type(exc).__name__}"],
        )
    if not isinstance(loaded, dict):
        return {}, ConfigValidationReport(
            ok=False, errors=["CONFIG_NOT_MAPPING"],
        )
    return loaded, ConfigValidationReport(ok=True)


def dump_yaml(config: Dict[str, Any]) -> bytes:
    _require_yaml()
    text = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    return text.encode("utf-8")


def validate_config(config: Dict[str, Any]) -> ConfigValidationReport:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(config, dict):
        return ConfigValidationReport(
            ok=False, errors=["CONFIG_NOT_MAPPING"],
        )
    version = config.get("version")
    if version is None:
        warnings.append("CONFIG_VERSION_MISSING")
    elif not isinstance(version, int) or version < 1:
        errors.append("CONFIG_VERSION_INVALID")
    limits = config.get("limits", {})
    if limits is not None:
        if not isinstance(limits, dict):
            errors.append("LIMITS_NOT_MAPPING")
        else:
            _validate_limits(limits, errors)
    conf = config.get("confidence", {})
    if conf is not None and isinstance(conf, dict):
        _validate_confidence(conf, errors)
    profiles = config.get("profiles")
    if profiles is not None:
        if not isinstance(profiles, list):
            errors.append("PROFILES_NOT_LIST")
        else:
            seen = set()
            for i, p in enumerate(profiles):
                if not isinstance(p, dict):
                    errors.append(f"PROFILE_{i}_NOT_MAPPING")
                    continue
                pid = p.get("profile_id")
                if not pid:
                    errors.append(f"PROFILE_{i}_MISSING_ID")
                    continue
                if pid in seen:
                    errors.append(f"PROFILE_DUPLICATE_ID: {pid}")
                seen.add(pid)
    return ConfigValidationReport(
        ok=not errors, errors=errors, warnings=warnings,
    )


def _validate_limits(limits: Dict[str, Any], errors: List[str]) -> None:
    positive_ints = (
        "max_file_size_mb", "max_uncompressed_mb", "max_zip_entries",
        "max_compression_ratio", "timeout_seconds", "max_findings",
        "max_tokens",
    )
    for key in positive_ints:
        if key not in limits:
            continue
        val = limits[key]
        if not isinstance(val, int) or val <= 0:
            errors.append(f"LIMIT_INVALID: {key}")


def _validate_confidence(conf: Dict[str, Any], errors: List[str]) -> None:
    required = ("high", "medium", "low")
    for key in required:
        if key not in conf:
            errors.append(f"CONFIDENCE_MISSING: {key}")
            continue
        v = conf[key]
        if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
            errors.append(f"CONFIDENCE_RANGE: {key}")
    if all(k in conf for k in required):
        try:
            if not (conf["high"] > conf["medium"] > conf["low"]):
                errors.append("CONFIDENCE_ORDER_INVALID")
        except TypeError:
            pass


def export_config(config: Dict[str, Any]) -> bytes:
    return dump_yaml(config)


__all__ = [
    "ConfigValidationReport",
    "compute_config_hash",
    "dump_yaml",
    "export_config",
    "parse_yaml",
    "validate_config",
]