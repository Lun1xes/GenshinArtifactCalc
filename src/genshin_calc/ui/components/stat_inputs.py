"""Stat inputs panel for artifact slot, set, level, and substats.

Features dynamic roll badges, discrete addend estimation,
quick paste, clear actions, and auto-filtering by slot.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple
import tkinter as tk
import customtkinter as ctk

from ...artifact_logic import (
    ARTIFACT_SLOTS,
    MAIN_STATS_BY_SLOT,
    STATS_DB,
    SLOT_EMOJI,
    possible_roll_counts,
)
from ...character_builds import SET_NAME_TO_KEY
from ..theme import (
    ThemeColors,
    FONTS,
    METRICS,
    card_style,
    button_slot_style,
    button_secondary_style,
    input_style,
    dropdown_style,
    roll_badge_style,
    get_roll_color,
)

# Reverse lookup for GOOD set keys -> Russian display names
SET_KEY_TO_NAME: dict[str, str] = {v: k for k, v in SET_NAME_TO_KEY.items()}


class StatInputs(ctk.CTkScrollableFrame):
    def __init__(self, master, on_artifact_changed: Optional[Callable[[dict], None]] = None, **kwargs):
        kwargs.setdefault("fg_color", ThemeColors.BG_CARD)
        kwargs.setdefault("corner_radius", METRICS["corner_radius_card"])
        super().__init__(master, **kwargs)
        
        self.on_artifact_changed = on_artifact_changed
        
        # State variables
        self.slot_var = ctk.StringVar(value=ARTIFACT_SLOTS[0])
        self.set_var = ctk.StringVar(value="(Не выбран)")
        self.main_stat_var = ctk.StringVar(value="HP")
        int_var_cls = getattr(ctk, "IntVar", tk.IntVar)
        self.level_var = int_var_cls(value=20)
        self.substat_vars: List[Dict[str, Any]] = []
        self._slot_buttons: Dict[str, ctk.CTkButton] = {}
        
        self._build_ui()
        self._notify_change()

    def _notify_change(self, *args):
        if self.on_artifact_changed:
            self.on_artifact_changed(self.get_data())

    def _update_substat_badges(self):
        for sub_data in self.substat_vars:
            stat = sub_data["stat"].get()
            val_str = sub_data["val"].get().replace(",", ".").strip()
            badge_lbl = sub_data["badge"]
            
            if not val_str or stat not in STATS_DB:
                badge_lbl.configure(text="", fg_color="transparent")
                continue
                
            try:
                val = Decimal(val_str)
                counts = possible_roll_counts(stat, val, 1, 6)
                if counts:
                    c = counts[0]
                    if c == 1:
                        badge_lbl.configure(text="1 Ролл", **roll_badge_style(1))
                    elif c == 2:
                        badge_lbl.configure(text="2 Ролла", **roll_badge_style(2))
                    elif c == 3:
                        badge_lbl.configure(text="3 Ролла", **roll_badge_style(3))
                    elif c == 4:
                        badge_lbl.configure(text="4 Ролла", **roll_badge_style(4))
                    else:
                        badge_lbl.configure(text=f"{c} Роллов", **roll_badge_style(c))
                else:
                    badge_lbl.configure(text="?", fg_color=ThemeColors.GRAY, text_color=ThemeColors.TEXT_PRIMARY)
            except Exception:
                badge_lbl.configure(text="ERR", fg_color=ThemeColors.RED_ERR, text_color="#ffffff")

    def _on_interaction(self, *args):
        self._update_substat_badges()
        self._notify_change()

    def _on_slot_change(self, slot_name: str):
        self.slot_var.set(slot_name)
        
        # Filter valid main stats for chosen slot
        valid_mains = list(MAIN_STATS_BY_SLOT.get(slot_name, ("HP",)))
        self.main_stat_menu.configure(values=valid_mains)
        if self.main_stat_var.get() not in valid_mains:
            self.main_stat_var.set(valid_mains[0])
            
        # Highlight active slot button
        for s, btn in self._slot_buttons.items():
            btn.configure(**button_slot_style(active=(s == slot_name)))
            
        self._on_interaction()

    def _build_ui(self):
        # Header / Actions row
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(10, 5))

        step1_lbl = ctk.CTkLabel(
            header_row,
            text="ШАГ 1: Слот и Сет артефакта",
            font=FONTS["header"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        )
        step1_lbl.pack(side="left", fill="x", expand=True)

        clear_btn = ctk.CTkButton(
            header_row,
            text="Очистить",
            width=75,
            height=26,
            font=FONTS["small"],
            command=self.clear_inputs,
            **button_secondary_style(),
        )
        clear_btn.pack(side="right", padx=(5, 0))

        paste_btn = ctk.CTkButton(
            header_row,
            text="Вставить",
            width=75,
            height=26,
            font=FONTS["small"],
            command=self._quick_paste,
            **button_secondary_style(),
        )
        paste_btn.pack(side="right")

        # Slot selector buttons
        slot_frame = ctk.CTkFrame(self, fg_color="transparent")
        slot_frame.pack(fill="x", padx=10, pady=5)
        
        for slot_name in ARTIFACT_SLOTS:
            emoji = SLOT_EMOJI.get(slot_name, "⭐")
            short = slot_name.split()[0]
            is_active = (slot_name == self.slot_var.get())
            btn = ctk.CTkButton(
                slot_frame,
                text=f"{emoji}\n{short}",
                width=55,
                height=48,
                command=lambda s=slot_name: self._on_slot_change(s),
                **button_slot_style(active=is_active),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self._slot_buttons[slot_name] = btn

        # Set selector dropdown
        set_row = ctk.CTkFrame(self, fg_color="transparent")
        set_row.pack(fill="x", padx=10, pady=(6, 12))
        
        ctk.CTkLabel(set_row, text="Сет:", width=50, font=FONTS["body_bold"], anchor="w", text_color=ThemeColors.TEXT_MUTED).pack(side="left")
        
        sorted_sets = ["(Не выбран)"] + sorted(SET_NAME_TO_KEY.keys())
        self.set_menu = ctk.CTkOptionMenu(
            set_row,
            values=sorted_sets,
            variable=self.set_var,
            command=self._on_interaction,
            **dropdown_style(),
        )
        self.set_menu.pack(side="left", fill="x", expand=True)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=ThemeColors.BORDER).pack(fill="x", padx=10, pady=6)

        # --- STEP 2: Main Stat & Level ---
        ctk.CTkLabel(
            self,
            text="ШАГ 2: Главный стат и уровень",
            font=FONTS["header"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(6, 5))

        stat_row = ctk.CTkFrame(self, fg_color="transparent")
        stat_row.pack(fill="x", padx=10, pady=5)

        self.main_stat_menu = ctk.CTkOptionMenu(
            stat_row,
            values=list(MAIN_STATS_BY_SLOT.get(self.slot_var.get(), ("HP",))),
            variable=self.main_stat_var,
            command=self._on_interaction,
            **dropdown_style(),
        )
        self.main_stat_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))

        lvl_frame = ctk.CTkFrame(stat_row, fg_color="transparent")
        lvl_frame.pack(side="left")
        ctk.CTkLabel(lvl_frame, text="Ур:", font=FONTS["body_bold"], text_color=ThemeColors.TEXT_MUTED).pack(side="left", padx=(0, 5))
        
        lvl_menu = ctk.CTkOptionMenu(
            lvl_frame,
            values=[str(i) for i in range(21)],
            command=lambda v: [self.level_var.set(int(v)), self._on_interaction()],
            width=65,
            **dropdown_style(),
        )
        lvl_menu.set("20")
        lvl_menu.pack(side="left")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=ThemeColors.BORDER).pack(fill="x", padx=10, pady=6)

        # --- STEP 3: Substats ---
        ctk.CTkLabel(
            self,
            text="ШАГ 3: Дополнительные характеристики (сабстаты)",
            font=FONTS["header"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(6, 5))

        default_stat_names = list(STATS_DB.keys())
        for i in range(4):
            card = ctk.CTkFrame(self, **card_style(alt=(i % 2 == 1)))
            card.pack(fill="x", padx=10, pady=3)

            s_var = ctk.StringVar(value=default_stat_names[i % len(default_stat_names)])
            v_var = ctk.StringVar()

            combo = ctk.CTkComboBox(
                card,
                values=default_stat_names,
                variable=s_var,
                width=175,
                state="readonly",
                command=self._on_interaction,
                **dropdown_style(),
            )
            combo.pack(side="left", padx=8, pady=6)

            entry = ctk.CTkEntry(
                card,
                textvariable=v_var,
                width=80,
                placeholder_text="0.0",
                **input_style(),
            )
            entry.pack(side="left", padx=8, pady=6)
            entry.bind("<KeyRelease>", self._on_interaction)

            badge = ctk.CTkLabel(
                card,
                text="",
                width=70,
                height=22,
                **roll_badge_style(1),
            )
            badge.configure(text="", fg_color="transparent")
            badge.pack(side="right", padx=10, pady=6)

            self.substat_vars.append({
                "stat": s_var,
                "val": v_var,
                "badge": badge,
                "combo": combo,
                "entry": entry,
            })

        self._on_slot_change(self.slot_var.get())

    def get_data(self) -> dict:
        """Return the current artifact data payload."""
        substats = []
        for sub in self.substat_vars:
            val_str = sub["val"].get().replace(",", ".").strip()
            if val_str:
                try:
                    substats.append((sub["stat"].get(), float(val_str)))
                except ValueError:
                    pass

        return {
            "slot": self.slot_var.get(),
            "set": self.set_var.get(),
            "main_stat": self.main_stat_var.get(),
            "level": self.level_var.get(),
            "substats": substats,
        }

    def clear_inputs(self):
        """Reset all inputs to blank defaults."""
        for sub in self.substat_vars:
            sub["val"].set("")
            sub["badge"].configure(text="", fg_color="transparent")
        self.set_var.set("(Не выбран)")
        self.level_var.set(20)
        self._on_interaction()

    def load_parsed_artifact(self, parsed: Any):
        """Populate inputs from a ParsedArtifact or dictionary."""
        slot = getattr(parsed, "slot", None) or (parsed.get("slot") if isinstance(parsed, dict) else None)
        if slot and slot in ARTIFACT_SLOTS:
            self._on_slot_change(slot)

        set_key = getattr(parsed, "set_key", None) or (parsed.get("set_key") if isinstance(parsed, dict) else None)
        if set_key:
            name_ru = SET_KEY_TO_NAME.get(set_key, set_key)
            if name_ru in SET_NAME_TO_KEY:
                self.set_var.set(name_ru)
            elif getattr(parsed, "set_name", None) in SET_NAME_TO_KEY:
                self.set_var.set(parsed.set_name)

        main_stat = getattr(parsed, "main_stat", None) or (parsed.get("main_stat") if isinstance(parsed, dict) else None)
        if main_stat:
            valid_mains = list(MAIN_STATS_BY_SLOT.get(self.slot_var.get(), ()))
            if main_stat in valid_mains:
                self.main_stat_var.set(main_stat)

        lvl = getattr(parsed, "level", None) or (parsed.get("level") if isinstance(parsed, dict) else None)
        if lvl is not None:
            self.level_var.set(int(lvl))

        subs = getattr(parsed, "substats", None) or (parsed.get("substats") if isinstance(parsed, dict) else [])
        for i, sub_data in enumerate(self.substat_vars):
            if i < len(subs):
                stat_name, val = subs[i]
                sub_data["stat"].set(stat_name)
                sub_data["val"].set(str(val))
            else:
                sub_data["val"].set("")

        self._on_interaction()

    def _quick_paste(self):
        """Paste and parse clipboard content into artifact inputs."""
        try:
            raw = self.clipboard_get().strip()
        except Exception:
            return
        if not raw:
            return

        # Check for JSON
        if raw.startswith("{") and raw.endswith("}"):
            try:
                from ...good_adapter import good_to_parsed_artifact, parse_good_json_string
                parsed = parse_good_json_string(raw)
                if parsed:
                    self.load_parsed_artifact(parsed[0] if isinstance(parsed, list) else parsed)
                    return
            except Exception:
                pass

        # Text line parsing
        lines = [line.strip() for line in raw.replace(",", "\n").split("\n") if line.strip()]
        sub_idx = 0
        for line in lines:
            if ":" in line or "=" in line:
                sep = ":" if ":" in line else "="
                parts = line.split(sep, 1)
                k = parts[0].strip()
                v = parts[1].strip().replace("+", "").replace("%", "").strip()
                # Check for main stat
                if "главный" in k.lower() or "основной" in k.lower():
                    if k in MAIN_STATS_BY_SLOT.get(self.slot_var.get(), ()):
                        self.main_stat_var.set(k)
                    continue
                # Try matching substat
                for db_stat in STATS_DB:
                    if db_stat.lower() in k.lower() or k.lower() in db_stat.lower():
                        if sub_idx < 4:
                            self.substat_vars[sub_idx]["stat"].set(db_stat)
                            self.substat_vars[sub_idx]["val"].set(v)
                            sub_idx += 1
                        break
        self._on_interaction()
