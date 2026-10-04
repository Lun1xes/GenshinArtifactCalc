import customtkinter as ctk
from decimal import Decimal

# Internal imports
from ...artifact_logic import (
    ARTIFACT_SLOTS, MAIN_STATS_BY_SLOT, STATS_DB, 
    SLOT_EMOJI, possible_roll_counts
)
from ...character_builds import SET_NAME_TO_KEY

class StatInputs(ctk.CTkScrollableFrame):
    def __init__(self, master, on_artifact_changed=None, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self.on_artifact_changed = on_artifact_changed
        
        # Variables
        self.slot_var = ctk.StringVar(value="flower")
        self.set_var = ctk.StringVar(value="(Не выбран)")
        self.main_stat_var = ctk.StringVar(value="HP")
        self.level_var = ctk.IntVar(value=20)
        self.substat_vars = []
        
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
                # Quick estimation of rolls (min_n=1, max_n=6 for +20 artifact)
                # Normally, we'd use more complex logic, but for UI badge:
                counts = possible_roll_counts(stat, val, 1, 6)
                if counts:
                    c = counts[0]
                    if c == 1:
                        badge_lbl.configure(text="1 Ролл", fg_color="#3B82F6", text_color="white") # Blue
                    elif c == 2:
                        badge_lbl.configure(text="2 Ролла", fg_color="#10B981", text_color="white") # Green
                    elif c == 3:
                        badge_lbl.configure(text="3 Ролла", fg_color="#F59E0B", text_color="white") # Yellow
                    elif c >= 4:
                        badge_lbl.configure(text=f"{c} Роллов", fg_color="#EF4444", text_color="white") # Red
                else:
                    badge_lbl.configure(text="?", fg_color="gray30", text_color="white")
            except Exception:
                badge_lbl.configure(text="ERR", fg_color="#EF4444", text_color="white")

    def _on_interaction(self, *args):
        self._update_substat_badges()
        self._notify_change()
        
    def _on_slot_change(self, slot_name: str):
        self.slot_var.set(slot_name)
        # Update main stat menu
        valid_mains = list(MAIN_STATS_BY_SLOT[slot_name])
        self.main_stat_menu.configure(values=valid_mains)
        if self.main_stat_var.get() not in valid_mains:
            self.main_stat_var.set(valid_mains[0])
            
        # Highlight buttons
        for s, btn in self._slot_buttons.items():
            btn.configure(fg_color="#374151" if s == slot_name else "#1F2937")
            
        self._on_interaction()

    def _build_ui(self):
        # COLORS
        BG_CARD = "#1F2937"
        BG_INPUT = "#374151"
        TEXT_PRIMARY = "#F3F4F6"
        
        # --- STEP 1: Slot and Set ---
        ctk.CTkLabel(self, text="Шаг 1: Сет и Слот", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        slot_frame = ctk.CTkFrame(self, fg_color="transparent")
        slot_frame.pack(fill="x", padx=10, pady=5)
        
        self._slot_buttons = {}
        for slot_name in ARTIFACT_SLOTS:
            emoji = SLOT_EMOJI[slot_name]
            short = slot_name.split()[0]
            btn = ctk.CTkButton(
                slot_frame,
                text=f"{emoji}\n{short}",
                font=("Segoe UI", 11),
                width=60, height=50,
                fg_color=BG_CARD,
                command=lambda s=slot_name: self._on_slot_change(s),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self._slot_buttons[slot_name] = btn
            
        # Set selection
        set_row = ctk.CTkFrame(self, fg_color="transparent")
        set_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(set_row, text="Сет:", width=60, anchor="w").pack(side="left")
        self.set_menu = ctk.CTkOptionMenu(
            set_row,
            values=["(Не выбран)"] + sorted(SET_NAME_TO_KEY.keys()),
            variable=self.set_var,
            command=self._on_interaction,
            fg_color=BG_CARD
        )
        self.set_menu.pack(side="left", fill="x", expand=True)
        
        # --- STEP 2: Main Stat and Level ---
        ctk.CTkLabel(self, text="Шаг 2: Главный стат и уровень", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(15, 5))
        
        stat_row = ctk.CTkFrame(self, fg_color="transparent")
        stat_row.pack(fill="x", padx=10, pady=5)
        
        self.main_stat_menu = ctk.CTkOptionMenu(
            stat_row,
            values=list(MAIN_STATS_BY_SLOT[self.slot_var.get()]),
            variable=self.main_stat_var,
            command=self._on_interaction,
            fg_color=BG_CARD
        )
        self.main_stat_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        lvl_frame = ctk.CTkFrame(stat_row, fg_color="transparent")
        lvl_frame.pack(side="left")
        ctk.CTkLabel(lvl_frame, text="Ур:").pack(side="left", padx=(0, 5))
        lvl_menu = ctk.CTkOptionMenu(
            lvl_frame,
            values=[str(i) for i in range(21)],
            command=lambda v: [self.level_var.set(int(v)), self._on_interaction()],
            width=60,
            fg_color=BG_CARD
        )
        lvl_menu.set("20")
        lvl_menu.pack(side="left")
        
        # --- STEP 3: Substats ---
        ctk.CTkLabel(self, text="Шаг 3: Сабстаты", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(15, 5))
        
        stat_names = list(STATS_DB)
        for i in range(4):
            row = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8)
            row.pack(fill="x", padx=10, pady=4)
            
            s_var = ctk.StringVar(value=stat_names[i])
            v_var = ctk.StringVar()
            
            combo = ctk.CTkComboBox(
                row, values=stat_names, variable=s_var,
                width=160, state="readonly",
                fg_color=BG_INPUT,
                command=self._on_interaction
            )
            combo.pack(side="left", padx=8, pady=8)
            
            entry = ctk.CTkEntry(
                row, textvariable=v_var, width=80,
                placeholder_text="Значение",
                fg_color=BG_INPUT
            )
            entry.pack(side="left", padx=8, pady=8)
            entry.bind("<KeyRelease>", self._on_interaction)
            
            badge = ctk.CTkLabel(row, text="", width=60, corner_radius=6)
            badge.pack(side="right", padx=10, pady=8)
            
            self.substat_vars.append({"stat": s_var, "val": v_var, "badge": badge})
            
        self._on_slot_change(self.slot_var.get())
        
    def get_data(self) -> dict:
        substats = []
        for sub in self.substat_vars:
            val = sub["val"].get().replace(",", ".").strip()
            if val:
                try:
                    substats.append((sub["stat"].get(), float(val)))
                except ValueError:
                    pass
                    
        return {
            "slot": self.slot_var.get(),
            "set": self.set_var.get(),
            "main_stat": self.main_stat_var.get(),
            "level": self.level_var.get(),
            "substats": substats
        }
