---
name: typeless-backup
description: Back up Typeless history on Windows and macOS.
version: 0.1.0
author: NeoWeb3Nova, Hermes Agent
license: MIT
platforms: [windows, macos]
metadata:
  hermes:
    tags: [Typeless, backup, privacy, SQLite, macOS, Windows]
    related_skills: []
---

# Typeless Backup Skill

Use the repository's standard-library CLI to preserve Typeless local history and linked recordings. The workflow is read-only, local, and backup-only: it does not upload data, modify the source database, or import records into another voice service.

## When to Use

- The user wants to preserve Typeless conversations before pricing, quota, or access changes.
- The user wants a local SQLite and OGG archive on Windows or macOS.
- The user wants a JSONL export for local search or later processing.

Do not use this skill for Linux backups, cloud upload, database repair, or migration into Doubao or another service.

## Prerequisites

- Windows or macOS with Typeless installed.
- Python 3.10+.
- Read access to the Typeless data directory.
- A new or empty local destination directory.

No third-party Python package is required.

## How to Run

From the cloned repository, use `terminal` with one of these commands:

```powershell
python .\typeless_backup.py backup --output "D:\TypelessBackups\typeless-backup"
```

```bash
python3 ./typeless_backup.py backup --output "$HOME/TypelessBackups/typeless-backup"
```

If discovery does not find the profile, pass `--source` explicitly. The source must contain `typeless.db` and `Recordings/`:

```text
python[3] typeless_backup.py backup --source <Typeless-data-directory> --output <new-local-directory>
```

## Procedure

1. Run `backup` with a new local output path. Completion criterion: the command returns JSON and creates `typeless.db`, `Recordings/`, and `manifest.json`.
2. Inspect `manifest.json`. Completion criterion: `recording_count`, `recording_bytes`, database statistics, and `database_sha256` are present.
3. Export only from the backup, never the live profile:

   ```text
   python[3] typeless_backup.py export-jsonl --backup <backup-directory> --output <backup-directory>/history.jsonl
   ```

   Completion criterion: the output contains one JSON object per `history_v2` record.
5. For normal reading, use `export-markdown` instead of opening JSONL directly:

   ```text
   python[3] typeless_backup.py export-markdown --backup <backup-directory> --output <backup-directory>/history.md
   ```

   Completion criterion: `history.md` contains timestamped entries and readable transcript blocks.
6. Keep the original Typeless profile until the backup and its recording count are independently verified.

## Pitfalls

- The tool rejects non-empty output directories instead of overwriting them.
- A running Typeless process may add records after the SQLite snapshot begins; close Typeless first when an application-level freeze matters.
- Backups contain private text and audio. Do not commit them or attach them to public issues.
- The project supports Windows and macOS only. Linux is intentionally rejected by the backup CLI.
- The discovered layout is validated rather than assumed; use `--source` when a Typeless version stores data elsewhere.

## Verification

Run the repository's self-contained tests with `terminal`:

```text
python3 -m unittest discover -s tests -v
```

Completion criterion: all tests pass and `python3 -m py_compile typeless_backup.py` exits successfully.
