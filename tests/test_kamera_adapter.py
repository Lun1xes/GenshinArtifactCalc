"""Tests for Inventory Kamera integration adapter."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from decimal import Decimal

import kamera_adapter
from good_adapter import ParsedArtifact


SAMPLE_GOOD_DATA = {
    "format": "GOOD",
    "version": 2,
    "source": "InventoryKamera",
    "artifacts": [
        {
            "setKey": "GladiatorsFinale",
            "slotKey": "flower",
            "rarity": 5,
            "mainStatKey": "hp",
            "level": 20,
            "substats": [
                {"key": "critRate_", "value": 10.5},
                {"key": "critDMG_", "value": 21.0},
                {"key": "atk_", "value": 9.9},
                {"key": "enerRech_", "value": 5.8},
            ],
            "location": "Diluc",
            "lock": True,
        },
        {
            "setKey": "CrimsonWitchOfFlames",
            "slotKey": "plume",
            "rarity": 5,
            "mainStatKey": "atk",
            "level": 16,
            "substats": [
                {"key": "critRate_", "value": 7.0},
                {"key": "critDMG_", "value": 14.0},
                {"key": "eleMas", "value": 42.0},
                {"key": "hp_", "value": 4.1},
            ],
            "location": "",
            "lock": False,
        },
    ],
    "characters": [
        {"key": "Diluc", "level": 90},
    ],
}


class TestKameraAdapter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def test_find_kamera_executable_when_exists(self):
        # Create a dummy exe in temp dir
        dummy_exe = Path(self.temp_dir) / "InventoryKamera.exe"
        dummy_exe.write_text("dummy binary", encoding="utf-8")

        found = kamera_adapter.find_kamera_executable(search_dirs=[self.temp_dir])
        self.assertIsNotNone(found)
        self.assertEqual(Path(found).resolve(), dummy_exe.resolve())

    def test_find_kamera_executable_when_missing(self):
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        found = kamera_adapter.find_kamera_executable(search_dirs=[str(empty_dir)])
        self.assertIsNone(found)

    def test_find_latest_kamera_export(self):
        export_dir = Path(self.temp_dir) / "GenshinData"
        export_dir.mkdir()

        file_old = export_dir / "genshinData_GOOD_2026_09_01_12_00.json"
        file_old.write_text(json.dumps(SAMPLE_GOOD_DATA), encoding="utf-8")

        time.sleep(0.05)
        file_new = export_dir / "genshinData_GOOD_2026_10_01_14_00.json"
        file_new.write_text(json.dumps(SAMPLE_GOOD_DATA), encoding="utf-8")

        latest = kamera_adapter.find_latest_kamera_export(search_dirs=[str(export_dir)])
        self.assertIsNotNone(latest)
        self.assertEqual(Path(latest).resolve(), file_new.resolve())

    def test_list_kamera_exports(self):
        export_dir = Path(self.temp_dir) / "GenshinData"
        export_dir.mkdir()

        file1 = export_dir / "genshinData_GOOD_2026_10_01_10_00.json"
        file1.write_text(json.dumps(SAMPLE_GOOD_DATA), encoding="utf-8")

        exports = kamera_adapter.list_kamera_exports(search_dirs=[str(export_dir)])
        self.assertEqual(len(exports), 1)
        info = exports[0]
        self.assertEqual(info["filename"], "genshinData_GOOD_2026_10_01_10_00.json")
        self.assertEqual(info["artifact_count"], 2)
        self.assertIn("Diluc", info["characters"])

    def test_load_kamera_good_file(self):
        export_file = Path(self.temp_dir) / "test_export.json"
        export_file.write_text(json.dumps(SAMPLE_GOOD_DATA), encoding="utf-8")

        artifacts, meta = kamera_adapter.load_kamera_good_file(str(export_file))
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(artifacts[0].slot, "Цветок жизни")
        self.assertEqual(artifacts[0].location, "Diluc")
        self.assertEqual(artifacts[0].level, 20)
        self.assertEqual(artifacts[1].slot, "Перо смерти")
        self.assertEqual(artifacts[1].level, 16)
        self.assertEqual(meta.get("source"), "InventoryKamera")

    def test_export_watcher(self):
        export_dir = Path(self.temp_dir) / "GenshinData"
        export_dir.mkdir()

        detected = []
        watcher = kamera_adapter.KameraFolderWatcher(
            folders=[str(export_dir)],
            callback=lambda path: detected.append(path),
            poll_interval=0.1,
        )
        watcher.start()
        try:
            time.sleep(0.15)
            # Create a new file
            new_file = export_dir / "genshinData_GOOD_new.json"
            new_file.write_text(json.dumps(SAMPLE_GOOD_DATA), encoding="utf-8")
            time.sleep(0.35)
            self.assertGreaterEqual(len(detected), 1)
            self.assertEqual(Path(detected[0]).resolve(), new_file.resolve())
        finally:
            watcher.stop()

    def test_launch_kamera_missing_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            kamera_adapter.launch_kamera(exe_path="non_existent_kamera.exe")

    def test_launch_kamera_with_elevation_mock(self):
        from unittest.mock import patch

        dummy_exe = Path(self.temp_dir) / "InventoryKamera.exe"
        dummy_exe.write_text("dummy", encoding="utf-8")

        with patch("os.startfile") as mock_startfile:
            res = kamera_adapter.launch_kamera(exe_path=str(dummy_exe))
            self.assertTrue(res)
            mock_startfile.assert_called_once()
            args, kwargs = mock_startfile.call_args
            self.assertEqual(kwargs.get("operation"), "runas")

    def test_launch_kamera_user_canceled_uac_raises_permission_error(self):
        from unittest.mock import patch

        dummy_exe = Path(self.temp_dir) / "InventoryKamera.exe"
        dummy_exe.write_text("dummy", encoding="utf-8")

        err = OSError("The operation was canceled by the user.")
        err.winerror = 1223

        with patch("os.startfile", side_effect=err):
            with self.assertRaises(PermissionError):
                kamera_adapter.launch_kamera(exe_path=str(dummy_exe))


if __name__ == "__main__":
    unittest.main()
