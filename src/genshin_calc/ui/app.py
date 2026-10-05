"""Main application window for Genshin Impact Modular Artifact Calculator v2."""
from __future__ import annotations

from typing import Any, Dict, Optional
import customtkinter as ctk

from .theme import ThemeColors, apply_app_theme, apply_native_dark_titlebar
from .hotkeys import setup_layout_agnostic_hotkeys
from .components.sidebar import Sidebar
from .views.calculator_view import CalculatorView
from .views.scanner_view import ScannerView
from .views.builds_view import BuildsView
from .views.history_view import HistoryView
from .views.about_view import AboutView
from ..good_adapter import ParsedArtifact


class LazyViewsDict(dict):
    """Dictionary supporting transparent on-demand lazy initialization of views."""
    KNOWN_VIEWS = ("calculator", "scanner", "builds", "history", "about")

    def __init__(self, app: GenshinCalcApp):
        super().__init__()
        self._app = app

    def __getitem__(self, key: str) -> ctk.CTkFrame:
        if not dict.__contains__(self, key) and key in self.KNOWN_VIEWS:
            self._app._get_or_create_view(key)
        return super().__getitem__(key)

    def get(self, key: str, default=None):
        if key in self.KNOWN_VIEWS and not dict.__contains__(self, key):
            self._app._get_or_create_view(key)
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self.KNOWN_VIEWS

    def keys(self):
        return list(self.KNOWN_VIEWS)

    def __iter__(self):
        return iter(self.KNOWN_VIEWS)

    def __len__(self):
        return len(self.KNOWN_VIEWS)

    def items(self):
        for k in self.KNOWN_VIEWS:
            yield (k, self[k])

    def values(self):
        for k in self.KNOWN_VIEWS:
            yield self[k]


class GenshinCalcApp(ctk.CTk):
    def __init__(self):
        apply_app_theme()
        super().__init__()
        apply_native_dark_titlebar(self)
        
        # Move filter: ignore pure WM_MOVE coordinate changes
        self._last_root_w: Optional[int] = None
        self._last_root_h: Optional[int] = None
        orig_update_dim = self._update_dimensions_event

        def debounced_root_update_dimensions(event=None):
            if event is not None and getattr(event, "widget", None) is not self:
                return
            curr_w = self.winfo_width()
            curr_h = self.winfo_height()
            if curr_w == self._last_root_w and curr_h == self._last_root_h:
                return  # Pure window move (x/y), skip dimension recalculation
            self._last_root_w = curr_w
            self._last_root_h = curr_h
            orig_update_dim(event)

        self._update_dimensions_event = debounced_root_update_dimensions
        self.bind("<Configure>", debounced_root_update_dimensions)
        
        self.title("Genshin Impact — Калькулятор Артефактов v2")
        self.geometry("1200x780")
        self.minsize(950, 650)
        self.configure(fg_color=ThemeColors.BG_DEEP)
        
        # Configure layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        # Lazy Views dictionary
        self.views = LazyViewsDict(self)
        self.current_view_id: Optional[str] = None
        
        self._build_ui()
        setup_layout_agnostic_hotkeys(self)

    def _build_ui(self):
        # 1. Sidebar on left
        self.sidebar = Sidebar(self, on_nav_click=self.show_view)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Main content container on right
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # 3. Initialize active view
        self._init_views()

        # 4. Set initial active view
        self.show_view("calculator")

    def _init_views(self):
        # Initialize default active view (Calculator)
        self._get_or_create_view("calculator")

    def _get_or_create_view(self, view_id: str) -> Optional[ctk.CTkFrame]:
        if dict.__contains__(self.views, view_id):
            return dict.__getitem__(self.views, view_id)

        view = None
        if view_id == "calculator":
            view = CalculatorView(self.main_container)
        elif view_id == "scanner":
            view = ScannerView(
                self.main_container,
                on_transfer_to_calculator=self.transfer_artifact_to_calculator,
            )
        elif view_id == "builds":
            view = BuildsView(
                self.main_container,
                on_select_character=self.select_character_for_calculator,
            )
        elif view_id == "history":
            view = HistoryView(
                self.main_container,
                on_transfer_to_calculator=self.transfer_artifact_to_calculator,
                get_current_calculator_artifact=self.get_current_calculator_artifact,
            )
        elif view_id == "about":
            view = AboutView(self.main_container)

        if view is not None:
            self.views[view_id] = view
        return view

    def show_view(self, view_id: str):
        target_view = self._get_or_create_view(view_id)
        if target_view is None:
            return

        # Hide current view
        if self.current_view_id and self.current_view_id in self.views:
            self.views[self.current_view_id].grid_forget()

        # Show target view
        target_view.grid(row=0, column=0, sticky="nsew")
        self.current_view_id = view_id

        # Update sidebar if called programmatically
        if hasattr(self, "sidebar") and self.sidebar.active_view != view_id:
            self.sidebar.active_view = view_id
            for vid, btn in self.sidebar.buttons:
                from .theme import button_nav_style
                btn.configure(**button_nav_style(active=(vid == view_id)))

        # Refresh history view if selected (using smart if_needed check)
        if view_id == "history" and hasattr(target_view, "refresh_history"):
            target_view.refresh_history(if_needed=True)

    def get_current_calculator_artifact(self) -> Optional[dict]:
        """Fetch currently calculated artifact from CalculatorView."""
        calc_view = self.views.get("calculator")
        if calc_view and hasattr(calc_view, "get_current_artifact"):
            return calc_view.get_current_artifact()
        return None

    def transfer_artifact_to_calculator(self, artifact: ParsedArtifact):
        """Transfer artifact from Scanner or History into Calculator inputs."""
        calc_view: CalculatorView = self.views["calculator"]
        calc_view.load_parsed_artifact(artifact)
        self.show_view("calculator")

    def select_character_for_calculator(self, char_name: str):
        """Select character from Builds catalog into Calculator."""
        calc_view: CalculatorView = self.views["calculator"]
        calc_view.set_selected_character(char_name)
        self.show_view("calculator")
