"""Shared helpers: config loading, output writing, provenance."""
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path="config/config.yaml"):
    with open(ROOT / path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def p(rel):
    """Resolve a path relative to the project root."""
    return (ROOT / rel).resolve()


def write_csv(df, rel, cfg):
    out = p(Path(cfg["outputs"]["dir"]) / rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding=cfg["outputs"]["encoding"])
    return out


def write_geojson(gdf, rel, cfg):
    out = p(Path(cfg["outputs"]["dir"]) / rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    gdf.to_file(out, driver="GeoJSON")
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo):
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "log", "-1", "--format=%H %cI"], text=True
        ).strip()
    except Exception:
        return None


def write_provenance(cfg, outputs, notes):
    inputs = {}
    for key, rel in cfg["inputs"].items():
        fp = p(rel)
        if fp.is_file():
            inputs[key] = {"path": rel, "sha256": sha256(fp)}
    for key, rel in cfg["catalogs"].items():
        fp = p(rel)
        if fp.is_file():
            inputs[f"catalog:{key}"] = {"path": rel, "sha256": sha256(fp)}
    prov = {
        "project": cfg["project"],
        "script_version": cfg["version"],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "pleiades_snapshot_commit": git_commit(p(cfg["inputs"]["pleiades_repo"])),
        "inputs": inputs,
        "outputs": {k: str(Path(v).relative_to(ROOT)) for k, v in outputs.items()},
        "notes": notes,
    }
    out = p(Path(cfg["outputs"]["dir"]) / "provenance.json")
    out.write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
