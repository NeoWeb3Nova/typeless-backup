# Typeless Backup

A privacy-first, read-only backup and export tool for Typeless on Windows.

It preserves the local SQLite history database and the linked `.ogg` recordings, so users can keep their own Typeless conversations even if the service changes its pricing or limits.

## What it backs up

- `typeless.db` via SQLite's online backup API
- `Recordings/*.ogg`
- `manifest.json` with counts, sizes, hashes, and integrity metadata

It does **not** upload, transcribe, or publish your private conversations.

## Usage

On Windows PowerShell:

```powershell
python .\typeless_backup.py backup `
  --output "D:\TypelessBackups\typeless-2026-09-19"
```

If Typeless is installed in the normal location, `--source` is optional. Otherwise:

```powershell
python .\typeless_backup.py backup `
  --source "$env:APPDATA\Typeless.exe" `
  --output "D:\TypelessBackups\typeless-2026-09-19"
```

Export text and metadata from a backup without changing the backup:

```powershell
python .\typeless_backup.py export-jsonl `
  --backup "D:\TypelessBackups\typeless-2026-09-19" `
  --output "D:\TypelessBackups\typeless-2026-09-19\history.jsonl"
```

The JSONL export is for local search, archival, and future tooling. This project does not implement import into Doubao or any other voice service.

## Safety

- The source database is opened read-only.
- The SQLite backup uses a consistent snapshot while Typeless is running.
- The destination must be empty; the tool refuses to overwrite an existing backup.
- Backups contain private text and audio. Treat them like personal records: encrypt or protect the destination and never commit it to GitHub.

## Development

```bash
python -m unittest discover -s tests -v
```

## License

MIT
