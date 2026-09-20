---
name: typeless-backup
description: Preserve Typeless voice history with private, read-only backups on Windows and macOS.
---

# Typeless Backup

Preserve Typeless conversations, transcripts, and linked voice recordings as a local archive. This workflow is read-only and backup-only: it never uploads personal data, modifies the live Typeless profile, or imports records into another voice service.

## Use This Skill When

- A user wants to preserve Typeless history before an app, account, quota, or pricing change.
- A user wants a local copy of SQLite history and OGG recordings.
- A user wants a readable transcript export after creating a backup.

Do not use this workflow for Linux backups, cloud synchronization, database repair, or service migration.

## Platform and Requirements

- Windows or macOS only.
- Python 3.10 or later.
- Read access to the Typeless local data directory.
- A new or empty local destination directory.
- No third-party Python packages.

## Run

Run commands from this repository. The CLI discovers candidate profiles and validates that each contains `typeless.db` and `Recordings/`.

Windows PowerShell:

```powershell
python .\scripts/typeless_backup.py backup `
  --output "D:\TypelessBackups\typeless-backup"
```

macOS:

```bash
python3 ./scripts/typeless_backup.py backup \
  --output "$HOME/TypelessBackups/typeless-backup"
```

When discovery cannot find the profile, pass it explicitly:

```text
python[3] scripts/typeless_backup.py backup --source <Typeless-data-directory> --output <new-local-directory>
```

## Procedure

1. Create the backup in a new destination. Verify that it contains `typeless.db`, `Recordings/`, and `manifest.json`.
2. Inspect `manifest.json`. Verify `recording_count`, `recording_bytes`, database statistics, and `database_sha256`.
3. Export machine-readable records from the backup, never from the live profile:

   ```text
   python[3] scripts/typeless_backup.py export-jsonl --backup <backup-directory> --output <backup-directory>/history.jsonl
   ```

4. Export the human-readable transcript:

   ```text
   python[3] scripts/typeless_backup.py export-markdown --backup <backup-directory> --output <backup-directory>/history.md
   ```

5. Keep the original Typeless profile until the backup and its recording count are independently verified.

## Safety Rules

- Never overwrite a non-empty destination.
- Never write the output directory inside the live Typeless profile.
- Close Typeless first when an application-level freeze matters; SQLite still provides a consistent database snapshot.
- Treat the archive as private data. Do not commit `typeless.db`, `Recordings/`, `*.ogg`, `history.jsonl`, or `history.md` to a public repository.
- Do not claim that a backup grants legal ownership rights; describe it as practical privacy, continuity, and data-portability control.

## Verification

Run the self-contained checks:

```text
python[3] -m unittest discover -s tests -v
python[3] -m py_compile scripts/typeless_backup.py
```

A complete run has passing tests, a successful compile, a valid `manifest.json`, `PRAGMA integrity_check = ok`, and matching database/recording counts.
