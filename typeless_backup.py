#!/usr/bin/env python3
"""Backup and export Typeless Windows local history without touching the source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

APP_DIR_NAME = "Typeless.exe"
DB_NAME = "typeless.db"
RECORDINGS_DIR = "Recordings"


def default_source() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / APP_DIR_NAME
    users_root = Path("/mnt/c/Users")
    candidates = sorted(
        (user / "AppData/Roaming" / APP_DIR_NAME for user in users_root.iterdir())
        if users_root.is_dir() else []
    )
    if candidates:
        return candidates[0]
    return Path.home() / "AppData/Roaming" / APP_DIR_NAME


def sha256(path: Path, chunk=1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sqlite_backup(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    source_uri = f"file:{source.as_posix()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
        dst.execute("PRAGMA foreign_keys=ON")
        result = dst.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"backup integrity_check failed: {result}")


def db_stats(path: Path) -> dict:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as con:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        stats = {t: con.execute(f' select count(*) from "{t}"').fetchone()[0] for t in tables}
        stats["history_v2_with_text"] = con.execute(
            "select count(*) from history_v2 where refined_text is not null and length(refined_text)>0"
        ).fetchone()[0] if "history_v2" in tables else 0
        stats["history_v2_with_audio_path"] = con.execute(
            "select count(*) from history_v2 where audio_local_path is not null and length(audio_local_path)>0"
        ).fetchone()[0] if "history_v2" in tables else 0
        return stats


def copy_recordings(source: Path, target: Path) -> tuple[int, int]:
    target.mkdir(parents=True, exist_ok=True)
    count = total = 0
    for src in sorted(source.glob("*.ogg")):
        dst = target / src.name
        shutil.copy2(src, dst)
        count += 1
        total += dst.stat().st_size
    return count, total


def backup(source: Path, output: Path) -> dict:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    db = source / DB_NAME
    recordings = source / RECORDINGS_DIR
    if not db.is_file():
        raise FileNotFoundError(f"missing database: {db}")
    if not recordings.is_dir():
        raise FileNotFoundError(f"missing recordings directory: {recordings}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    sqlite_backup(db, output / DB_NAME)
    recording_count, recording_bytes = copy_recordings(recordings, output / RECORDINGS_DIR)
    source_stats = db_stats(db)
    backup_stats = db_stats(output / DB_NAME)
    if source_stats != backup_stats:
        raise RuntimeError(f"database stats differ: source={source_stats}, backup={backup_stats}")
    if recording_count != source_stats.get("history_v2_with_audio_path", recording_count):
        raise RuntimeError("recording count does not match history_v2 audio path count")
    manifest = {
        "format": "typeless-backup-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Typeless Windows local data",
        "database": DB_NAME,
        "database_sha256": sha256(output / DB_NAME),
        "recordings_directory": RECORDINGS_DIR,
        "recording_count": recording_count,
        "recording_bytes": recording_bytes,
        "database_stats": backup_stats,
        "privacy": "This backup contains private conversation text and audio; do not publish it.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def export_jsonl(backup_dir: Path, output: Path) -> dict:
    db = backup_dir / DB_NAME
    if not db.is_file():
        raise FileNotFoundError(db)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as con, output.open("w", encoding="utf-8") as out:
        columns = [r[1] for r in con.execute("pragma table_info(history_v2)")]
        order = "created_at, id" if "created_at" in columns else "rowid"
        for row in con.execute(f"select * from history_v2 order by {order}"):
            record = dict(zip(columns, row))
            for key in ("mic_device_info", "client_metadata", "mode_meta"):
                if isinstance(record.get(key), bytes):
                    record[key] = record[key].hex()
            audio_path = str(record.get("audio_local_path") or "").replace("\\", "/")
            record["audio_file"] = f"{RECORDINGS_DIR}/{audio_path.rsplit('/', 1)[-1]}"
            out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            count += 1
    return {"records": count, "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup/export Typeless Windows local history")
    sub = parser.add_subparsers(dest="command", required=True)
    p_backup = sub.add_parser("backup")
    p_backup.add_argument("--source", type=Path, default=default_source())
    p_backup.add_argument("--output", type=Path, required=True)
    p_export = sub.add_parser("export-jsonl")
    p_export.add_argument("--backup", type=Path, required=True)
    p_export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "backup":
        print(json.dumps(backup(args.source, args.output), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(export_jsonl(args.backup, args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
