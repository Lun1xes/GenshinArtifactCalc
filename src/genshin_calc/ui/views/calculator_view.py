"""Calculator view coordinating artifact stat inputs and forecast analytics."""
from __future__ import annotations

from typing import Any, Optional
import customtkinter as ctk

from ..components.stat_inputs import StatInputs
from ..components.forecast_panel import ForecastPanel
from ..theme import get_rank
from ...good_adapter import RU_TO_STAT_KEY, RU_TO_SLOT_KEY
from ...character_builds import SET_NAME_TO_KEY


class CalculatorView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        
        self.forecast_panel: Optional[ForecastPanel] = None
        self.stat_inputs: Optional[StatInputs] = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, uniform="calc_cols")
        self.grid_columnconfigure(1, weight=1, uniform="calc_cols")
        
        self._build_ui()

    def _build_ui(self):
        # 1. Left Column: StatInputs
        self.stat_inputs = StatInputs(
            self,
            on_artifact_changed=self._on_artifact_changed,
        )
        self.stat_inputs.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        # 2. Right Column: ForecastPanel
        self.forecast_panel = ForecastPanel(
            self,
            on_fit_character=self._on_fit_character,
        )
        self.forecast_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        # Initial trigger
        self.forecast_panel.update_forecast(self.stat_inputs.get_data())

    def _on_artifact_changed(self, artifact_data: dict):
        if (
            self.forecast_panel is not None
            and hasattr(self.forecast_panel, "update_forecast")
            and callable(self.forecast_panel.update_forecast)
        ):
            self.forecast_panel.update_forecast(artifact_data)

    def _on_fit_character(self, char_name: str):
        # Sync if parent needs notification
        pass

    def load_parsed_artifact(self, parsed: Any):
        """Load artifact into inputs and recalculate."""
        self.stat_inputs.load_parsed_artifact(parsed)
        self.forecast_panel.update_forecast(self.stat_inputs.get_data())

    def set_selected_character(self, char_name: str):
        """Select a character in the forecast panel."""
        self.forecast_panel.set_selected_character(char_name)

    def calculate(self):
        """Recalculate forecast for current inputs."""
        self.forecast_panel.update_forecast(self.stat_inputs.get_data())

    def save_to_history(self):
        """Save current artifact to history."""
        self.forecast_panel.save_to_history()

    def copy_share_card(self):
        """Copy formatted report card to clipboard."""
        self.forecast_panel.copy_share_card()

    def export_current_artifact_to_good(self) -> dict:
        """Export current artifact as a standard GOOD v2 dictionary."""
        data = self.stat_inputs.get_data()
        slot = data.get("slot", "Цветок жизни")
        set_name = data.get("set", "(Не выбран)")
        main_stat = data.get("main_stat", "HP")
        level = data.get("level", 20)
        substats = data.get("substats", [])

        slot_key = RU_TO_SLOT_KEY.get(slot, "flower")
        set_key = SET_NAME_TO_KEY.get(set_name, "GladiatorsFinale")
        main_stat_key = RU_TO_STAT_KEY.get(main_stat, "hp")

        good_subs = []
        for s_name, val in substats:
            k = RU_TO_STAT_KEY.get(s_name)
            if k:
                good_subs.append({"key": k, "value": float(val)})

        return {
            "setKey": set_key,
            "slotKey": slot_key,
            "level": level,
            "rarity": 5,
            "mainStatKey": main_stat_key,
            "location": "",
            "lock": False,
            "substats": good_subs,
        }

    def get_current_artifact(self) -> Optional[dict]:
        """Return dict representation of current artifact for comparison/history."""
        if not hasattr(self, "stat_inputs"):
            return None
        data = self.stat_inputs.get_data()
        slot = data.get("slot")
        main_stat = data.get("main_stat")
        set_name = data.get("set", "")
        level = data.get("level", 20)
        substats = data.get("substats", [])

        if not substats:
            return None

        pot_pct = 0.0
        curr_pct = 0.0
        rank = "—"
        if hasattr(self, "forecast_panel") and self.forecast_panel and self.forecast_panel.last_eval:
            pot_pct = round(self.forecast_panel.last_eval.potential_pct, 1)
            curr_pct = round(self.forecast_panel.last_eval.current_pct, 1)
            rank, _ = get_rank(pot_pct)

        cv = 0.0
        if hasattr(self, "forecast_panel") and self.forecast_panel and self.forecast_panel.last_forecast:
            cv = round(self.forecast_panel.last_forecast.expected_cv, 1)
        else:
            for s_name, s_val in substats:
                if "Крит. шанс" in s_name:
                    cv += float(s_val) * 2
                elif "Крит. урон" in s_name:
                    cv += float(s_val)
            cv = round(cv, 1)

        char_name = ""
        if hasattr(self, "forecast_panel") and self.forecast_panel and self.forecast_panel.selected_build:
            char_name = self.forecast_panel.selected_build.name

        return {
            "slot": slot,
            "set": set_name,
            "main_stat": main_stat,
            "level": level,
            "substats": substats,
            "potential_pct": pot_pct,
            "current_pct": curr_pct,
            "rank": rank,
            "crit_value": cv,
            "character": char_name,
            "is_current": True,
        }
