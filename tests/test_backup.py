import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import typeless_backup


class BackupTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
