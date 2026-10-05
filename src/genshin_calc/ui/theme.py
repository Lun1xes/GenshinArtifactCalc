"""Centralized design system for Genshin Impact Artifact Calculator UI.

Defines the authentic Genshin Impact color palette, typography scales,
metrics, and widget style helpers for CustomTkinter components.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class ThemeColors:
    """Centralized Genshin Impact dark palette & application colors."""
    # Primary Palette
    BG_DEEP: str      = "#0f0f1e"  # Deepest background (main window / root)
    BG_DARK: str      = "#1a1a2e"  # Secondary deep background / contrast
    BG_PANEL: str     = "#16213e"  # Sidebar, panels, container sections
    BG_CARD: str      = "#1e2a45"  # Card containers, interactive boxes
    BG_CARD_ALT: str  = "#1b2540"  # Alternate card tone for row banding
    BG_INPUT: str     = "#0e1a30"  # Text entries, spinboxes, dropdown inputs
    BG_HOVER: str     = "#243555"  # Button & item hover state background

    # Borders
    BORDER: str       = "#243555"  # Subtle container border
    BORDER_FOCUS: str = "#3a5075"  # Focused / active border tone

    # Accent Colors
    GOLD: str         = "#ffd700"  # Genshin signature gold accent
    GOLD_DIM: str     = "#c9a900"  # Muted gold / button base
    GOLD_HOVER: str   = "#ffe033"  # Bright gold hover highlight
    CYAN: str         = "#00e5ff"  # Genshin signature cyan accent
    CYAN_DIM: str     = "#00acc1"  # Muted cyan / secondary button base
    CYAN_HOVER: str   = "#33ebff"  # Bright cyan hover highlight

    # Semantic Status Colors
    SUCCESS: str      = "#69f0ae"  # Green success indicator
    WARNING: str      = "#ffd54f"  # Yellow warning indicator
    DANGER: str       = "#ff5252"  # Red danger indicator / error

    # Specific Button & State Accents
    GREEN: str        = "#69f0ae"
    GREEN_BTN: str    = "#2e7d32"
    GREEN_HOVER: str  = "#1b5e20"
    RED: str          = "#ff5252"
    RED_BTN: str      = "#c62828"
    RED_HOVER: str    = "#8e0000"
    RED_ERR: str      = "#d32f2f"
    ORANGE: str       = "#ff8c00"
    ORANGE_WARM: str  = "#ffb74d"
    PURPLE: str       = "#e040fb"
    PURPLE_BTN: str   = "#4a148c"
    PURPLE_HOVER: str = "#311b92"
    BLUE_LIGHT: str   = "#64b5f6"
    BLUE_LINK: str    = "#81d4fa"
    BLUE_BTN: str     = "#1565c0"
    BLUE_SS: str      = "#4488ff"
    TEAL_BTN: str     = "#00695c"
    TEAL_HOVER: str   = "#004d40"
    KAMERA_BTN: str   = "#bf360c"
    KAMERA_HOVER: str = "#d84315"
    GRAY: str         = "#424242"
    GRAY_HOVER: str   = "#616161"
    GRAY_SLATE: str   = "#37474f"
    GRAY_SLATE_H: str = "#455a64"

    # Typography Foreground Colors
    TEXT_PRIMARY: str = "#e0e0e0"  # Main readable text
    TEXT_MUTED: str   = "#90a4ae"  # Secondary / descriptive text
    TEXT_DIM: str     = "#aaaaaa"  # De-emphasized notes / labels
    TEXT_SUBS: str    = "#b0bec5"  # Monospace substat text
    YELLOW_WARN: str  = "#ffd54f"  # Warning text accent

    # Special
    TRANSPARENT: str  = "transparent"


# Backward-compatible alias
C = ThemeColors


# ─── Elemental Colors ───────────────────────────────────────────────────
ELEMENT_COLORS: dict[str, str] = {
    "Пиро": "#ff5252",
    "Гидро": "#00e5ff",
    "Анемо": "#69f0ae",
    "Электро": "#e040fb",
    "Дендро": "#76ff03",
    "Крио": "#80d8ff",
    "Гео": "#ffd700",
    "pyro": "#ff5252",
    "hydro": "#00e5ff",
    "anemo": "#69f0ae",
    "electro": "#e040fb",
    "dendro": "#76ff03",
    "cryo": "#80d8ff",
    "geo": "#ffd700",
    "Pyro": "#ff5252",
    "Hydro": "#00e5ff",
    "Anemo": "#69f0ae",
    "Electro": "#e040fb",
    "Dendro": "#76ff03",
    "Cryo": "#80d8ff",
    "Geo": "#ffd700",
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

def get_element_color(element: str, default: str = ThemeColors.GOLD) -> str:
    """Return hex color for a character/artifact element."""
    return ELEMENT_COLORS.get(element, default)

def get_element_bg(element: str, default: str = ThemeColors.BG_PANEL) -> str:
    """Return tinted background hex color for an element badge/avatar."""
    return ELEMENT_BG.get(element, default)


# ─── Artifact Ranks & Thresholds ────────────────────────────────────────
RANK_THRESHOLDS: list[tuple[float, str, str]] = [
    (90.0, "SSS", ThemeColors.PURPLE),     # #e040fb
    (80.0, "SS",  ThemeColors.BLUE_SS),    # #4488ff
    (70.0, "S",   ThemeColors.GREEN),      # #69f0ae
    (50.0, "A",   ThemeColors.GOLD),       # #ffd700
    (30.0, "B",   ThemeColors.ORANGE),     # #ff8c00
    (0.0,  "C",   ThemeColors.RED),        # #ff5252
]

RANK_COLORS: dict[str, str] = {name: color for _, name, color in RANK_THRESHOLDS}

def get_rank(pct: float) -> tuple[str, str]:
    """Return (rank_name, rank_color) for a given score percentage (0-100)."""
    for threshold, name, color in RANK_THRESHOLDS:
        if pct >= threshold:
            return name, color
    return "C", ThemeColors.RED


# ─── Substat Roll Colors & Badges ───────────────────────────────────────
ROLL_COLORS: dict[int, str] = {
    1: "#3b82f6",  # Blue (Base roll)
    2: "#10b981",  # Green (1 upgrade)
    3: "#f59e0b",  # Amber (2 upgrades)
    4: "#ff8c00",  # Orange (3 upgrades)
    5: "#ef4444",  # Red (4 upgrades)
    6: "#e040fb",  # Purple (5 upgrades, max 6 total)
}

def get_roll_color(rolls: int) -> str:
    """Return hex color for a discrete roll count."""
    if rolls <= 1:
        return ROLL_COLORS[1]
    if rolls in ROLL_COLORS:
        return ROLL_COLORS[rolls]
    return ROLL_COLORS[6]


# ─── Compatibility Verdict Colors ───────────────────────────────────────
COMPATIBILITY_COLORS: dict[str, str] = {
    "Идеально": ThemeColors.GOLD,
    "Отлично": ThemeColors.GREEN,
    "Приемлемо": ThemeColors.YELLOW_WARN,
    "Не подходит": ThemeColors.RED,
}

def get_compatibility_color(verdict: str, default: str = ThemeColors.TEXT_MUTED) -> str:
    """Return hex color for a character build compatibility verdict."""
    return COMPATIBILITY_COLORS.get(verdict, default)


# ─── Artifact Slot Emojis ───────────────────────────────────────────────
SLOT_EMOJI: dict[str, str] = {
    "Цветок жизни": "🌺",
    "Перо смерти": "✒️",
    "Пески времени": "⏳",
    "Кубок пространства": "🍷",
    "Корона разума": "👑",
}


# ─── Typography System ──────────────────────────────────────────────────
FONTS: dict[str, tuple] = {
    "title":       ("Segoe UI", 16, "bold"),
    "header":      ("Segoe UI", 13, "bold"),
    "body":        ("Segoe UI", 11),
    "small":       ("Segoe UI", 10),
    "mono":        ("Consolas", 11),
    "body_bold":   ("Segoe UI", 11, "bold"),
    "small_bold":  ("Segoe UI", 10, "bold"),
    "caption":     ("Segoe UI", 9),
    "mono_bold":   ("Consolas", 11, "bold"),
    "mono_small":  ("Consolas", 10),
    "display":     ("Segoe UI", 36, "bold"),
    "display_lg":  ("Segoe UI", 40, "bold"),
}

def get_font(name: str) -> tuple:
    """Safely return a font tuple by identifier, falling back to body."""
    return FONTS.get(name, FONTS["body"])


# ─── Metrics System ─────────────────────────────────────────────────────
METRICS: dict[str, int] = {
    "corner_radius_card": 10,
    "corner_radius_btn": 6,
    "border_width": 1,
    "corner_radius_pill": 12,
    "corner_radius_input": 6,
    "corner_radius_badge": 4,
    "border_width_active": 2,
    "border_width_none": 0,
    "padding_screen": 15,
    "padding_card": 10,
    "padding_sm": 5,
    "sidebar_width": 220,
    "avatar_size_normal": 48,
    "avatar_size_large": 64,
    "slot_icon_size": 32,
    "badge_height": 22,
    "progress_bar_height": 8,
}


# ─── Widget Style Helpers ───────────────────────────────────────────────
def card_style(alt: bool = False, border: bool = True) -> dict[str, Any]:
    """Returns kwargs for CTkFrame cards."""
    style: dict[str, Any] = {
        "fg_color": ThemeColors.BG_CARD_ALT if alt else ThemeColors.BG_CARD,
        "corner_radius": METRICS["corner_radius_card"],
    }
    if border:
        style["border_width"] = METRICS["border_width"]
        style["border_color"] = ThemeColors.BORDER
    else:
        style["border_width"] = 0
    return style


def panel_style() -> dict[str, Any]:
    """Returns kwargs for secondary container panels."""
    return {
        "fg_color": ThemeColors.BG_PANEL,
        "corner_radius": METRICS["corner_radius_card"],
    }


def button_primary_style() -> dict[str, Any]:
    """Primary Gold CTA button."""
    return {
        "fg_color": ThemeColors.GOLD_DIM,
        "hover_color": ThemeColors.GOLD,
        "text_color": ThemeColors.BG_DEEP,
        "corner_radius": METRICS["corner_radius_btn"],
    }


def button_secondary_style() -> dict[str, Any]:
    """Neutral card-toned button."""
    return {
        "fg_color": ThemeColors.BG_CARD,
        "hover_color": ThemeColors.BG_HOVER,
        "text_color": ThemeColors.TEXT_PRIMARY,
        "border_width": METRICS["border_width"],
        "border_color": ThemeColors.BORDER,
        "corner_radius": METRICS["corner_radius_btn"],
    }


def button_accent_cyan_style() -> dict[str, Any]:
    """Cyan accent button."""
    return {
        "fg_color": ThemeColors.CYAN_DIM,
        "hover_color": ThemeColors.CYAN,
        "text_color": ThemeColors.BG_DEEP,
        "corner_radius": METRICS["corner_radius_btn"],
    }


def button_danger_style() -> dict[str, Any]:
    """Red/Danger action button."""
    return {
        "fg_color": "#d32f2f",
        "hover_color": ThemeColors.RED,
        "text_color": "#ffffff",
        "corner_radius": METRICS["corner_radius_btn"],
    }


def button_nav_style(active: bool = False) -> dict[str, Any]:
    """Sidebar navigation tab button styling."""
    if active:
        return {
            "fg_color": ThemeColors.BG_CARD,
            "text_color": ThemeColors.GOLD,
            "hover_color": ThemeColors.BG_CARD,
            "anchor": "w",
            "corner_radius": METRICS["corner_radius_btn"],
            "font": FONTS["body_bold"],
        }
    return {
        "fg_color": "transparent",
        "text_color": ThemeColors.TEXT_MUTED,
        "hover_color": ThemeColors.BG_CARD_ALT,
        "anchor": "w",
        "corner_radius": METRICS["corner_radius_btn"],
        "font": FONTS["body"],
    }


def button_slot_style(active: bool = False) -> dict[str, Any]:
    """Artifact slot selector emoji/icon button styling."""
    if active:
        return {
            "fg_color": ThemeColors.BG_HOVER,
            "text_color": ThemeColors.GOLD,
            "hover_color": ThemeColors.BG_HOVER,
            "border_width": METRICS["border_width_active"],
            "border_color": ThemeColors.GOLD,
            "corner_radius": METRICS["corner_radius_btn"],
            "font": FONTS["body_bold"],
        }
    return {
        "fg_color": ThemeColors.BG_CARD,
        "text_color": ThemeColors.TEXT_PRIMARY,
        "hover_color": ThemeColors.BG_HOVER,
        "border_width": METRICS["border_width"],
        "border_color": ThemeColors.BORDER,
        "corner_radius": METRICS["corner_radius_btn"],
        "font": FONTS["body"],
    }


def input_style() -> dict[str, Any]:
    """Form entry / text box input styling."""
    return {
        "fg_color": ThemeColors.BG_INPUT,
        "text_color": ThemeColors.TEXT_PRIMARY,
        "border_color": ThemeColors.BORDER,
        "border_width": METRICS["border_width"],
        "corner_radius": METRICS["corner_radius_input"],
        "font": FONTS["body"],
    }


def dropdown_style() -> dict[str, Any]:
    """OptionMenu / ComboBox dropdown styling."""
    return {
        "fg_color": ThemeColors.BG_INPUT,
        "button_color": ThemeColors.BG_CARD,
        "button_hover_color": ThemeColors.BG_HOVER,
        "text_color": ThemeColors.TEXT_PRIMARY,
        "dropdown_fg_color": ThemeColors.BG_CARD,
        "dropdown_hover_color": ThemeColors.BG_HOVER,
        "dropdown_text_color": ThemeColors.TEXT_PRIMARY,
        "corner_radius": METRICS["corner_radius_input"],
        "font": FONTS["body"],
    }


def badge_style(color: str, text_color: str = "#ffffff") -> dict[str, Any]:
    """Compact badge label styling."""
    return {
        "fg_color": color,
        "text_color": text_color,
        "corner_radius": METRICS["corner_radius_badge"],
        "font": FONTS["small_bold"],
    }


def roll_badge_style(rolls: int) -> dict[str, Any]:
    """Discrete substat roll count badge styling."""
    return badge_style(get_roll_color(rolls), "#ffffff")


def progress_bar_style(accent_color: str = ThemeColors.CYAN) -> dict[str, Any]:
    """CTkProgressBar styling."""
    return {
        "fg_color": ThemeColors.BG_DEEP,
        "progress_color": accent_color,
        "corner_radius": METRICS["corner_radius_badge"],
        "height": METRICS["progress_bar_height"],
    }


def refine_dpi_scaling() -> None:
    """Refine CustomTkinter's ScalingTracker and event handlers to prevent window dragging lag.

    1. Neutralizes 100ms DPI polling loop and alpha flickering in ScalingTracker.
    2. Deactivates CustomTkinter's destructive withdraw/update header manipulation loop.
    3. Filters out pure WM_MOVE coordinate changes from CTkScrollableFrame <Configure> events,
       completely eliminating canvas redraw freezes when moving windows.
    4. Debounces actual resize operations to prevent CPU bottlenecks.
    """
    try:
        import sys
        import customtkinter as ctk
        from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker
        from customtkinter.windows.widgets.ctk_scrollable_frame import CTkScrollableFrame

        # 1. Disable automatic DPI tracker loop
        if hasattr(ctk, "deactivate_automatic_dpi_awareness"):
            ctk.deactivate_automatic_dpi_awareness()

        # 2. Deactivate destructive window header manipulation (withdraw/update/deiconify)
        if hasattr(ctk.CTk, "_deactivate_windows_window_header_manipulation"):
            ctk.CTk._deactivate_windows_window_header_manipulation = True

        # Mark update loop as running to prevent add_widget from scheduling initial .after(100)
        ScalingTracker.update_loop_running = True

        orig_check = getattr(ScalingTracker, "check_dpi_scaling", None)
        if orig_check:
            @classmethod
            def refined_check_dpi_scaling(cls):
                # When automatic DPI awareness is disabled, do not poll or reschedule
                if getattr(cls, "deactivate_automatic_dpi_awareness", False):
                    cls.update_loop_running = True
                    return
                return orig_check()

            ScalingTracker.check_dpi_scaling = refined_check_dpi_scaling

        # 3. Patch CTkScrollableFrame to ignore pure WM_MOVE events
        orig_fit = getattr(CTkScrollableFrame, "_fit_frame_dimensions_to_canvas", None)
        if orig_fit and not getattr(CTkScrollableFrame, "_is_move_filter_patched", False):
            CTkScrollableFrame._is_move_filter_patched = True

            def refined_fit_frame_dimensions_to_canvas(self, event):
                last_w = getattr(self, "_last_canvas_w", None)
                last_h = getattr(self, "_last_canvas_h", None)
                if event.width == last_w and event.height == last_h:
                    return  # Pure window move (x/y coordinate change), do not redraw
                self._last_canvas_w = event.width
                self._last_canvas_h = event.height
                orig_fit(self, event)

            CTkScrollableFrame._fit_frame_dimensions_to_canvas = refined_fit_frame_dimensions_to_canvas

            orig_sf_init = CTkScrollableFrame.__init__

            def refined_sf_init(self, *args, **kwargs):
                orig_sf_init(self, *args, **kwargs)
                self._last_sf_w = None
                self._last_sf_h = None

                def on_sf_configure(event):
                    if event.width == self._last_sf_w and event.height == self._last_sf_h:
                        return  # Pure window move (x/y), no redraw needed
                    self._last_sf_w = event.width
                    self._last_sf_h = event.height

                    try:
                        if (
                            self.winfo_exists()
                            and hasattr(self, "_parent_canvas")
                            and self._parent_canvas.winfo_exists()
                        ):
                            self._parent_canvas.configure(scrollregion=self._parent_canvas.bbox("all"))
                    except Exception:
                        pass

                self.bind("<Configure>", on_sf_configure)

            CTkScrollableFrame.__init__ = refined_sf_init

        # 4. Windows native System DPI Awareness mode 1
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
    except Exception:
        pass


def apply_native_dark_titlebar(window: Any) -> bool:
    """Apply Windows 10/11 immersive dark mode directly to HWND without withdraw/update."""
    import sys
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        val = ctypes.c_int(1)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
        )
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ctypes.byref(val), ctypes.sizeof(val)
            )
        return True
    except Exception:
        return False


def apply_app_theme() -> None:
    """Configure global CustomTkinter appearance settings safely."""
    try:
        import customtkinter as ctk
        refine_dpi_scaling()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
    except Exception:
        pass


