"""Prepare or apply an opt-in desktop bridge configuration; no login or model call.

Requires Python 3.11+. Inspect the default dry-run, then repeat with --apply.
The selected ocx runtime, account login and compatibility patching are prerequisites.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import urlsplit
import uuid

from grok_codex_bridge.catalog import extend_native_catalog, read_catalog

SOURCE = Path(__file__).resolve().parent


class PreparedPlan(dict):
    """Payloads plus the read baseline, so another editor's changes are not overwritten."""

    originals: dict[Path, bytes | None]


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def plan(
    codex_home: Path,
    adapter: Path,
    binary: Path,
    routed_catalog: Path,
    model: str,
    effort: str,
    base_url: str,
) -> dict[Path, bytes]:
    home, adapter, binary, routed_catalog = (
        p.resolve() for p in [codex_home, adapter, binary, routed_catalog]
    )
    if not binary.is_file():
        raise ValueError("--codex-binary must identify an installed executable")
    if not re.fullmatch(r"xai/grok-[A-Za-z0-9._-]+", model):
        raise ValueError("Choose an explicit xai/grok model")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", effort):
        raise ValueError("Choose one explicit reasoning effort")
    url = urlsplit(base_url)
    if url.port is not None and not 1 <= url.port <= 65535:
        raise ValueError("Proxy port must be 1..65535")
    try:
        loopback = ipaddress.ip_address(url.hostname or "").is_loopback
    except ValueError:
        loopback = url.hostname == "localhost"
    if (
        not loopback
        or url.scheme != "http"
        or url.path.rstrip("/") != "/v1"
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError(
            "This setup supports a selected loopback HTTP /v1 proxy without URL credentials"
        )
    native = read_catalog(home / "models_cache.json")
    merged, _ = extend_native_catalog(native, read_catalog(routed_catalog), model)
    generated = adapter / "runtime/native-plus-grok-catalog.json"
    native_path = home / "config.toml"
    native_bytes = native_path.read_bytes() if native_path.exists() else None
    native_text = native_bytes.decode("utf-8-sig") if native_bytes is not None else ""
    config = tomllib.loads(native_text)
    configured = config.get("model_catalog_json")
    if configured and Path(configured).resolve() != generated:
        raise ValueError(
            "An unrelated startup catalog is already selected; no replacement was made"
        )
    provider_id = "ocx-grok"
    provider = dict(
        name="Grok via selected local proxy",
        base_url=base_url.rstrip("/"),
        wire_api="responses",
        requires_openai_auth=False,
    )
    existing = config.get("model_providers", {}).get(provider_id)
    if existing is not None:
        if set(existing) - set(provider):
            raise ValueError(
                "Existing Grok provider has extra options; preserve and configure that profile explicitly"
            )
        for key in ["base_url", "wire_api", "requires_openai_auth"]:
            if existing.get(key) != provider[key]:
                raise ValueError(
                    "Existing Grok provider differs; no rebinding was made"
                )
        provider = existing
    updated = native_text
    if not configured:
        position = re.search(r"(?m)^\s*\[", updated)
        at = position.start() if position else len(updated)
        prefix = updated[:at]
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        updated = (
            prefix
            + "model_catalog_json = "
            + json.dumps(str(generated))
            + "\n\n"
            + updated[at:]
        )
    if existing is None:
        updated = (
            updated.rstrip()
            + "\n\n[model_providers.ocx-grok]\n"
            + "".join(
                key
                + " = "
                + (str(value).lower() if isinstance(value, bool) else json.dumps(value))
                + "\n"
                for key, value in provider.items()
            )
        )
    parsed = tomllib.loads(updated)
    preserved = dict(parsed)
    preserved.pop("model_catalog_json", None)
    original = dict(config)
    original.pop("model_catalog_json", None)
    if existing is None:
        preserved["model_providers"] = dict(preserved["model_providers"])
        preserved["model_providers"].pop(provider_id)
        if not preserved["model_providers"] and "model_providers" not in original:
            preserved.pop("model_providers")
    if preserved != original:
        raise ValueError("Setup would change unrelated native configuration")
    profile_name = "grok-bridge"
    native_name = model.removeprefix("xai/")
    settings = {
        "schema_version": 1,
        "selected_model": native_name,
        "selected_effort": effort,
        "codex_grok_profile": profile_name,
        "codex_grok_provider": provider_id,
        "verified_model_aliases": {native_name: {"codex_model": model}},
    }
    profile = (
        "model = "
        + json.dumps(model)
        + '\nmodel_provider = "ocx-grok"\nmodel_reasoning_effort = '
        + json.dumps(effort)
        + "\n"
    )
    profile += (
        "model_catalog_json = "
        + json.dumps(str(routed_catalog))
        + "\n\n[model_providers.ocx-grok]\n"
    )
    profile += "".join(
        key
        + " = "
        + (str(value).lower() if isinstance(value, bool) else json.dumps(value))
        + "\n"
        for key, value in provider.items()
    )
    profile += "\n[features.context_management]\nexperimental_mode = false\n"
    writes = {
        adapter / "settings.json": encoded(settings),
        adapter / "desktop-settings.json": encoded(
            {
                "schema_version": 1,
                "source_root": str(SOURCE),
                "codex_binary": str(binary),
            }
        ),
        home / (profile_name + ".config.toml"): profile.encode("utf-8"),
        adapter / "desktop.py": (SOURCE / "desktop.py").read_bytes(),
        generated: encoded(merged),
        native_path: updated.encode("utf-8"),
    }
    for path, payload in writes.items():
        for component in (path, *path.parents):
            if component.exists() and (
                component.is_symlink()
                or getattr(component.lstat(), "st_file_attributes", 0) & 0x400
            ):
                raise ValueError("Setup paths must not traverse links/reparse points")
        if (
            path not in {native_path, generated}
            and path.is_file()
            and path.read_bytes() != payload
        ):
            raise ValueError(
                f"Existing bridge file differs: {path.name}; preserve/reconcile the current installation first"
            )
    prepared = PreparedPlan(writes)
    prepared.originals = {
        path: path.read_bytes() if path.is_file() else None for path in writes
    }
    if prepared.originals[native_path] != native_bytes:
        raise ValueError(
            "Native configuration changed while preparing the plan; reread it"
        )
    return prepared


def apply_plan(writes: dict[Path, bytes], adapter: Path) -> dict:
    # The main config is deliberately last: referenced files exist before the pointer changes.
    changed = []

    def unchanged(path):
        actual = path.read_bytes() if path.is_file() else None
        if actual != writes.originals[path]:
            raise ValueError("A planned file changed after inspection: " + path.name)

    for path in writes:
        unchanged(path)
    stamp = (
        dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    for path, payload in writes.items():
        unchanged(path)
        if path.is_file() and path.read_bytes() == payload:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            backup = adapter / "backups" / stamp / path.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(path.read_bytes())
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        with temporary.open("xb") as stream:
            stream.write(payload)
        os.replace(temporary, path)
        changed.append(str(path))
    return {
        "status": "configured",
        "changed_paths": changed,
        "model_calls": 0,
        "desktop_reopen_required": bool(changed),
        "backup_run": stamp if changed else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
    )
    parser.add_argument("--adapter-root", type=Path)
    parser.add_argument("--codex-binary", type=Path, required=True)
    parser.add_argument("--routed-catalog", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", default="xhigh")
    parser.add_argument("--base-url", default="http://127.0.0.1:10100/v1")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    adapter = args.adapter_root or args.codex_home / "grok-adapter"
    try:
        writes = plan(
            args.codex_home,
            adapter,
            args.codex_binary,
            args.routed_catalog,
            args.model,
            args.effort,
            args.base_url,
        )
        result = (
            apply_plan(writes, adapter)
            if args.apply
            else {
                "status": "dry_run",
                "writes": [
                    {
                        "path": str(path),
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                    for path, payload in writes.items()
                ],
                "model_calls": 0,
            }
        )
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "configuration_error",
                    "error_type": type(error).__name__,
                    "message": str(error),
                },
                indent=2,
            )
        )
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
