"""Icon and Image Manager for Genshin Impact Calculator.

Handles lazy downloading, local disk caching, elemental border rendering,
and thread-safe delivery of character avatars and artifact icons.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.request
from typing import Callable, Optional, Tuple, Any

try:
    from PIL import Image, ImageDraw, ImageOps
    import customtkinter as ctk
    HAS_GUI_LIBS = True
except Exception:
    HAS_GUI_LIBS = False

try:
    from .utils import get_project_root
except (ImportError, ValueError):
    from utils import get_project_root

ROOT_DIR = get_project_root()
CACHE_DIR = os.path.join(ROOT_DIR, ".cache", "icons")
DATA_DIR = os.path.join(ROOT_DIR, "data")

ELEMENT_COLORS: dict[str, str] = {
    "Пиро": "#ff5252",
    "Гидро": "#00e5ff",
    "Анемо": "#69f0ae",
    "Электро": "#b388ff",
    "Дендро": "#76ff03",
    "Крио": "#80d8ff",
    "Гео": "#ffd700",
}

ELEMENT_BG: dict[str, str] = {
    "Пиро": "#3e1b1b",
    "Гидро": "#0e2a38",
    "Анемо": "#123326",
    "Электро": "#2d1c3e",
    "Дендро": "#1e3312",
    "Крио": "#122f3e",
    "Гео": "#382e12",
}


class IconManager:
    _instance: Optional["IconManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "IconManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._memory_cache: dict[str, Any] = {}
        self._chars_meta: dict[str, dict] = {}
        self._name_to_meta: dict[str, dict] = {}
        self._load_metadata()
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _load_metadata(self):
        meta_path = os.path.join(DATA_DIR, "characters_meta.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._chars_meta = json.load(f)
                for cid, data in self._chars_meta.items():
                    name_ru = data.get("name_ru")
                    if name_ru:
                        clean_ru = name_ru.lower().replace(" ", "").replace("ё", "е")
                        self._name_to_meta[clean_ru] = data
                    name_en = data.get("name_en")
                    if name_en:
                        clean_en = name_en.lower().replace(" ", "").replace("-", "").replace("'", "")
                        self._name_to_meta[clean_en] = data
            except Exception:
                pass

    def get_element_color(self, element: str) -> str:
        return ELEMENT_COLORS.get(element, "#ffd700")

    def find_character_meta(self, char_name_or_key: str) -> Optional[dict]:
        if not char_name_or_key:
            return None
        clean = char_name_or_key.strip().lower().replace(" ", "").replace("_", "").replace("-", "").replace("ё", "е")
        if clean in self._name_to_meta:
            return self._name_to_meta[clean]
        for k, v in self._name_to_meta.items():
            if k in clean or clean in k:
                return v
        return None

    def _create_placeholder_avatar_pil(self, char_name: str, element: str, size: Tuple[int, int] = (48, 48)) -> Optional[Image.Image]:
        if not HAS_GUI_LIBS:
            return None
        w, h = size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        border_col = self.get_element_color(element)
        bg_col = ELEMENT_BG.get(element, "#1a1a2e")

        # Outer border
        draw.ellipse([0, 0, w - 1, h - 1], fill=bg_col, outline=border_col, width=2)

        # Draw character initial
        letter = (char_name[:1] if char_name else "?").upper()
        # Fallback text in middle
        bbox = draw.textbbox((0, 0), letter)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((w - tw) // 2, (h - th) // 2 - 2), letter, fill=border_col)
        return img

    def _create_placeholder_avatar(self, char_name: str, element: str, size: Tuple[int, int] = (48, 48)):
        pil_img = self._create_placeholder_avatar_pil(char_name, element, size)
        if pil_img and HAS_GUI_LIBS and hasattr(ctk, "CTkImage"):
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        return None

    def _process_avatar_image(self, raw_img: Image.Image, element: str, size: Tuple[int, int]) -> Image.Image:
        w, h = size
        # Make square and resize with antialiasing
        min_dim = min(raw_img.width, raw_img.height)
        left = (raw_img.width - min_dim) // 2
        top = (raw_img.height - min_dim) // 2
        cropped = raw_img.crop((left, top, left + min_dim, top + min_dim))
        scaled = cropped.resize((w, h), Image.Resampling.LANCZOS)

        # Circular mask
        mask = Image.new("L", (w, h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse([2, 2, w - 3, h - 3], fill=255)

        # Base transparent image
        final_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        final_img.paste(scaled, (0, 0), mask=mask)

        # Draw smooth elemental circular border
        draw = ImageDraw.Draw(final_img)
        border_col = self.get_element_color(element)
        draw.ellipse([1, 1, w - 2, h - 2], outline=border_col, width=2)
        return final_img

    def get_character_avatar(
        self,
        char_name: str,
        size: Tuple[int, int] = (48, 48),
        on_ready_cb: Optional[Callable[[Any, str], None]] = None,
    ) -> Tuple[Optional[Any], str]:
        """Get character avatar CTkImage and elemental border color.
        
        If cached in RAM, returns immediately.
        If on_ready_cb is provided, returns an instant placeholder and performs
        all disk I/O, download, and PIL LANCZOS resizing in a background thread.
        """
        meta = self.find_character_meta(char_name)
        element = meta.get("element", "Анемо") if meta else "Анемо"
        border_color = self.get_element_color(element)

        if not HAS_GUI_LIBS or not hasattr(ctk, "CTkImage"):
            return None, border_color

        cache_key = f"{char_name}_{size[0]}x{size[1]}"
        pil_img = self._memory_cache.get(cache_key)

        if pil_img is not None:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            return ctk_img, border_color

        # If on_ready_cb is provided, return instant placeholder and offload heavy I/O and PIL
        if on_ready_cb:
            placeholder_pil = self._create_placeholder_avatar_pil(char_name, element, size)
            placeholder_ctk = ctk.CTkImage(light_image=placeholder_pil, dark_image=placeholder_pil, size=size) if placeholder_pil else None

            def bg_load_and_process():
                try:
                    icon_url = meta.get("icon_url") if meta else ""
                    if not icon_url:
                        return

                    url_hash = hashlib.md5(icon_url.encode("utf-8")).hexdigest()[:12]
                    disk_file = os.path.join(CACHE_DIR, f"{meta.get('id', 'char')}_{url_hash}.png")

                    if not os.path.isfile(disk_file):
                        req = urllib.request.Request(icon_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            data = resp.read()
                        with open(disk_file, "wb") as f:
                            f.write(data)

                    with Image.open(disk_file) as raw:
                        fresh_pil = self._process_avatar_image(raw.convert("RGBA"), element, size)

                    self._memory_cache[cache_key] = fresh_pil
                    fresh_ctk = ctk.CTkImage(light_image=fresh_pil, dark_image=fresh_pil, size=size)
                    on_ready_cb(fresh_ctk, border_color)
                except Exception:
                    pass

            threading.Thread(target=bg_load_and_process, daemon=True).start()
            return placeholder_ctk, border_color

        # Synchronous fallback if no callback was provided (e.g. tests or CLI)
        icon_url = meta.get("icon_url") if meta else ""
        if icon_url:
            url_hash = hashlib.md5(icon_url.encode("utf-8")).hexdigest()[:12]
            disk_file = os.path.join(CACHE_DIR, f"{meta.get('id', 'char')}_{url_hash}.png")
            if os.path.isfile(disk_file):
                try:
                    with Image.open(disk_file) as raw:
                        pil_img = self._process_avatar_image(raw.convert("RGBA"), element, size)
                    self._memory_cache[cache_key] = pil_img
                except Exception:
                    pass

        if pil_img is None:
            pil_img = self._create_placeholder_avatar_pil(char_name, element, size)
            self._memory_cache[cache_key] = pil_img

        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size) if pil_img else None
        return ctk_img, border_color

    def clear_cache(self):
        self._memory_cache.clear()

    def get_character_avatar_path(self, char_name: str) -> Optional[str]:
        """Return the local disk path or placeholder file for character avatar."""
        meta = self.find_character_meta(char_name)
        if not meta:
            clean = char_name.lower().replace(" ", "_")
            for m in self._chars_meta.values():
                if clean in m.get("id", "").lower() or clean in m.get("name_ru", "").lower():
                    meta = m
                    break
        icon_url = meta.get("icon_url", "") if meta else ""
        if icon_url:
            url_hash = hashlib.md5(icon_url.encode("utf-8")).hexdigest()[:12]
            disk_file = os.path.join(CACHE_DIR, f"{meta.get('id', 'char')}_{url_hash}.png")
            if os.path.isfile(disk_file):
                return disk_file
            return disk_file  # Expected path for cached avatar
        # Return fallback icon if any exists in cache
        if os.path.isdir(CACHE_DIR):
            files = os.listdir(CACHE_DIR)
            if files:
                return os.path.join(CACHE_DIR, files[0])
        return os.path.join(CACHE_DIR, f"{char_name.lower()}_avatar.png")

    def get_artifact_slot_icon(self, slot_name: str) -> str:
        """Return emoji or glyph icon for an artifact slot."""
        try:
            from .artifact_logic import SLOT_EMOJI
        except (ImportError, ValueError):
            from artifact_logic import SLOT_EMOJI
        return SLOT_EMOJI.get(slot_name, "⭐")


# Global singleton instance
icon_manager = IconManager()
