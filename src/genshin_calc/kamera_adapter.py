"""Adapter and runner for Inventory Kamera scanner.

Enables launching Inventory Kamera from within the Genshin Artifact Calculator,
monitoring scan outputs, and importing full inventory GOOD JSON scans.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from good_adapter import ParsedArtifact, from_good_artifact, from_good_json

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_PATHS = [
    "kamera/InventoryKamera.exe",
    "Inventory_Kamera-1.3.17/InventoryKamera.exe",
    "Inventory_Kamera-1.3.17/InventoryKamera/bin/Release/InventoryKamera.exe",
    "Inventory_Kamera-1.3.17/InventoryKamera/bin/Debug/InventoryKamera.exe",
    "InventoryKamera.exe",
]

DEFAULT_OUTPUT_DIRS = [
    "kamera/GenshinData",
    "Inventory_Kamera-1.3.17/GenshinData",
    "GenshinData",
]

KAMERA_LATEST_RELEASE_URL = (
    "https://github.com/Andrewthe13th/Inventory_Kamera/releases/download/v1.3.17/Inventory_KameraV1.3.17.zip"
)


def find_kamera_executable(search_dirs: Optional[Sequence[str | Path]] = None) -> Optional[Path]:
    """Search for InventoryKamera.exe in project folders or custom search directories."""
    if search_dirs is not None:
        for s_dir in search_dirs:
            p = Path(s_dir)
            if p.is_file() and p.name.lower() == "inventorykamera.exe":
                return p
            candidate = p / "InventoryKamera.exe"
            if candidate.is_file():
                return candidate
            # Check nested folders
            for sub in p.glob("**/InventoryKamera.exe"):
                if sub.is_file():
                    return sub
        return None

    from genshin_calc.utils import get_project_root
    root = Path(get_project_root())
    for rel_path in DEFAULT_SEARCH_PATHS:
        p = root / rel_path
        if p.is_file():
            return p

    return None


def get_kamera_output_dirs(search_dirs: Optional[Sequence[str | Path]] = None) -> list[Path]:
    """Return all valid or pre-configured output folders where Kamera exports GOOD files."""
    results: list[Path] = []
    seen = set()

    if search_dirs is not None:
        for s in search_dirs:
            p = Path(s).resolve()
            if p not in seen:
                seen.add(p)
                results.append(p)
        return results

    from genshin_calc.utils import get_project_root
    root = Path(get_project_root())
    for rel in DEFAULT_OUTPUT_DIRS:
        p = (root / rel).resolve()
        if p not in seen:
            seen.add(p)
            results.append(p)

    return results


def find_latest_kamera_export(search_dirs: Optional[Sequence[str | Path]] = None) -> Optional[Path]:
    """Find the most recent GOOD JSON export file produced by Inventory Kamera."""
    output_dirs = get_kamera_output_dirs(search_dirs)
    candidates: list[Path] = []

    for d in output_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for f in d.glob("*.json"):
            if f.is_file():
                candidates.append(f)

    if not candidates:
        return None

    # Sort by modification time descending
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Validate that it's a GOOD format file
    for cand in candidates:
        try:
            with open(cand, "r", encoding="utf-8", errors="replace") as fp:
                head = fp.read(1024)
                if '"format"' in head and '"GOOD"' in head:
                    return cand
                if '"artifacts"' in head:
                    return cand
        except Exception:
            continue

    return candidates[0] if candidates else None


def list_kamera_exports(search_dirs: Optional[Sequence[str | Path]] = None) -> list[dict[str, Any]]:
    """List all available scan files with artifact counts, characters, and timestamps."""
    output_dirs = get_kamera_output_dirs(search_dirs)
    exports: list[dict[str, Any]] = []

    for d in output_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for f in d.glob("*.json"):
            if not f.is_file():
                continue
            try:
                st = f.stat()
                mtime_dt = datetime.datetime.fromtimestamp(st.st_mtime)
                with open(f, "r", encoding="utf-8", errors="replace") as fp:
                    data = json.load(fp)

                artifacts_list = data.get("artifacts", [])
                characters_list = [c.get("key", "") for c in data.get("characters", []) if c.get("key")]
                source = data.get("source", "GOOD")

                exports.append(
                    {
                        "path": str(f.resolve()),
                        "filename": f.name,
                        "mtime": st.st_mtime,
                        "mtime_str": mtime_dt.strftime("%d.%m.%Y %H:%M"),
                        "size": st.st_size,
                        "artifact_count": len(artifacts_list),
                        "characters": characters_list,
                        "source": source,
                    }
                )
            except Exception as e:
                logger.debug("Failed reading export %s: %s", f, e)

    exports.sort(key=lambda item: item["mtime"], reverse=True)
    return exports


def load_kamera_good_file(file_path: str | Path) -> tuple[list[ParsedArtifact], dict[str, Any]]:
    """Load and parse an exported GOOD JSON file into ParsedArtifact instances.

    Returns:
        (artifacts, metadata_dict)
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Export file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    data = json.loads(content)
    raw_artifacts = data.get("artifacts", [])
    parsed_artifacts: list[ParsedArtifact] = []

    for raw in raw_artifacts:
        try:
            parsed_artifacts.append(from_good_artifact(raw))
        except Exception as e:
            logger.debug("Skipping unparseable artifact %s: %s", raw, e)

    meta = {
        "format": data.get("format", "GOOD"),
        "version": data.get("version", 2),
        "source": data.get("source", "InventoryKamera"),
        "characters": data.get("characters", []),
        "weapons": data.get("weapons", []),
        "materials": data.get("materials", {}),
    }

    return parsed_artifacts, meta


def launch_kamera(exe_path: Optional[str | Path] = None) -> bool:
    """Launch Inventory Kamera executable with Administrator elevation (UAC) on Windows.

    Inventory Kamera's manifest specifies requireAdministrator because it must interact
    with the elevated Genshin Impact window via SendInput. Standard CreateProcess (subprocess.Popen)
    fails with WinError 740 (The requested operation requires elevation).
    We use os.startfile with 'runas' or ShellExecuteW to trigger the Windows UAC elevation prompt.
    """
    if exe_path is None:
        target = find_kamera_executable()
        if target is None:
            raise FileNotFoundError(
                "InventoryKamera.exe не найден! Убедитесь, что приложение находится в папке kamera/ или Inventory_Kamera-1.3.17/"
            )
    else:
        target = Path(exe_path)
        if not target.is_file():
            raise FileNotFoundError(f"Файл {target} не найден!")

    working_dir = target.parent.resolve()
    target_str = str(target.resolve())
    working_dir_str = str(working_dir)
    logger.info("Launching %s (cwd=%s) with elevation", target_str, working_dir_str)

    if os.name == "nt":
        # First attempt: os.startfile with 'runas' operation
        try:
            if hasattr(os, "startfile"):
                os.startfile(target_str, operation="runas", cwd=working_dir_str)
                return True
        except OSError as exc:
            winerror = getattr(exc, "winerror", None)
            # 1223 = ERROR_CANCELLED (user clicked 'No' or closed the UAC prompt)
            if winerror == 1223 or "canceled" in str(exc).lower():
                raise PermissionError(
                    "Запуск отменен: требуется подтверждение прав администратора (UAC) для взаимодействия с Genshin Impact."
                ) from exc
            logger.warning("os.startfile runas failed: %s, trying ShellExecuteW", exc)

        # Fallback attempt: ctypes ShellExecuteW with 'runas'
        try:
            import ctypes
            res = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", target_str, "", working_dir_str, 1
            )
            if res > 32:
                return True
            if res in (5, 1223):
                raise PermissionError(
                    "Запуск отменен: требуется подтверждение прав администратора (UAC) для взаимодействия с Genshin Impact."
                )
            raise OSError(f"Ошибка вызова ShellExecuteW (код {res})")
        except Exception as exc:
            if isinstance(exc, PermissionError):
                raise
            logger.warning("ShellExecuteW failed: %s, falling back to subprocess", exc)

    # Fallback to subprocess for non-Windows or direct launch
    subprocess.Popen([target_str], cwd=working_dir_str)
    return True


def download_and_extract_kamera(
    dest_dir: str | Path = "kamera",
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """Download official pre-compiled Inventory Kamera release and extract into dest_dir."""
    dest_path = Path(dest_dir).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    temp_zip = dest_path / "temp_kamera_release.zip"

    def _reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            downloaded = min(block_num * block_size, total_size)
            progress_callback(downloaded, total_size)

    try:
        urllib.request.urlretrieve(KAMERA_LATEST_RELEASE_URL, str(temp_zip), reporthook=_reporthook)

        with zipfile.ZipFile(temp_zip, "r") as zf:
            zf.extractall(dest_path)

        exe_path = dest_path / "InventoryKamera.exe"
        if not exe_path.exists():
            for found in dest_path.glob("**/InventoryKamera.exe"):
                return found
        return exe_path
    finally:
        if temp_zip.exists():
            try:
                temp_zip.unlink()
            except Exception:
                pass


class KameraFolderWatcher:
    """Watches output folders in background and calls callback when a new export file is created."""

    def __init__(
        self,
        folders: Sequence[str | Path],
        callback: Callable[[str], None],
        poll_interval: float = 1.0,
    ):
        self.folders = [Path(f).resolve() for f in folders]
        self.callback = callback
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._known_files: set[str] = set()

        for folder in self.folders:
            if folder.exists() and folder.is_dir():
                for f in folder.glob("*.json"):
                    self._known_files.add(str(f.resolve()))

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _watch_loop(self):
        while self._running:
            try:
                for folder in self.folders:
                    if not folder.exists() or not folder.is_dir():
                        continue
                    for f in folder.glob("*.json"):
                        f_path = str(f.resolve())
                        if f_path not in self._known_files:
                            self._known_files.add(f_path)
                            # Give scanner a small moment to finish flushing to disk
                            time.sleep(0.2)
                            try:
                                self.callback(f_path)
                            except Exception as e:
                                logger.error("Watcher callback error: %s", e)
            except Exception as e:
                logger.debug("Watcher error: %s", e)
            time.sleep(self.poll_interval)
