import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import typeless_backup


class BackupTests(unittest.TestCase):
    def test_discovers_windows_profile_without_wsl_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profile = root / "AppData" / "Roaming" / "Typeless.exe"
            (profile / "Recordings").mkdir(parents=True)
            (profile / "typeless.db").touch()
            found = typeless_backup.discover_sources(
                "win32", {"APPDATA": str(root / "AppData"), "USERPROFILE": str(root)}, root
            )
            self.assertEqual(found, [profile.resolve()])

    def test_discovers_macos_profile(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            profile = home / "Library" / "Application Support" / "Typeless"
            (profile / "Recordings").mkdir(parents=True)
            (profile / "typeless.db").touch()
            self.assertEqual(typeless_backup.discover_sources("darwin", {}, home), [profile.resolve()])

    def test_linux_is_not_a_supported_backup_platform(self):
        self.assertEqual(typeless_backup.discover_sources("linux", {}, Path("/tmp")), [])

    def test_backup_rejects_output_inside_source(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "Typeless"
            (source / "Recordings").mkdir(parents=True)
            (source / "typeless.db").touch()
            with self.assertRaises(ValueError):
                typeless_backup.backup(source, source / "archive")

    def test_backup_and_export(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "Typeless.exe"
            (source / "Recordings").mkdir(parents=True)
            db = source / "typeless.db"
            with sqlite3.connect(db) as con:
                con.execute("create table history_v2 (id text, refined_text text, audio_local_path text)")
                con.execute("insert into history_v2 values (?, ?, ?)", ('1', 'hello', r'C:\\Recordings\\a.ogg'))
                con.commit()
            (source / "Recordings" / "a.ogg").write_bytes(b"ogg")
            out = root / "backup"
            manifest = typeless_backup.backup(source, out)
            self.assertEqual(manifest["recording_count"], 1)
            self.assertEqual(typeless_backup.db_stats(out / "typeless.db")["history_v2"], 1)
            exported = root / "history.jsonl"
            result = typeless_backup.export_jsonl(out, exported)
            self.assertEqual(result["records"], 1)
            self.assertEqual(json.loads(exported.read_text())["audio_file"], "Recordings/a.ogg")
            readable = root / "history.md"
            result = typeless_backup.export_markdown(out, readable)
            self.assertEqual(result["records"], 1)
            self.assertIn("hello", readable.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
