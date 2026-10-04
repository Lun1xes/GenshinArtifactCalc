import customtkinter as ctk

from ...artifact_logic import evaluate_artifact, ArtifactInputError, get_rank
from ...upgrade_probability import calculate_upgrade_forecast
from ...character_builds import get_unique_character_names, get_builds_for_character

class ForecastPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#1F2937", corner_radius=12, **kwargs)
        
        self.artifact_data = None
        self.char_var = ctk.StringVar(value="(Выберите персонажа)")
        self.role_var = ctk.StringVar(value="(Выберите билд)")
        self.selected_build = None
        
        self._build_ui()
        
    def _build_ui(self):
        # COLORS
        BG_CARD = "#111827"
        BG_INPUT = "#374151"
        TEXT_PRIMARY = "#F3F4F6"
        TEXT_MUTED = "#9CA3AF"
        
        # --- TITLE ---
        ctk.CTkLabel(self, text="Шаг 4: Оценка и Прогноз", font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 10))
        
        # --- TARGET BUILD SECTION ---
        build_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        build_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(build_frame, text="Целевой билд:", font=("Segoe UI", 12, "bold"), text_color="#EAB308").pack(anchor="w", padx=10, pady=(10, 2))
        
        self.char_menu = ctk.CTkOptionMenu(
            build_frame,
            values=["(Выберите персонажа)"] + get_unique_character_names(),
            variable=self.char_var,
            command=self._on_char_change,
            fg_color=BG_INPUT
        )
        self.char_menu.pack(fill="x", padx=10, pady=5)
        
        self.role_menu = ctk.CTkOptionMenu(
            build_frame,
            values=["(Выберите билд)"],
            variable=self.role_var,
            command=self._on_role_change,
            fg_color=BG_INPUT
        )
        self.role_menu.pack(fill="x", padx=10, pady=(5, 10))
        
        # --- SCORE & RANK METRICS ---
        metrics_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        metrics_frame.pack(fill="x", padx=15, pady=10)
        
        self.rank_lbl = ctk.CTkLabel(metrics_frame, text="?", font=("Segoe UI", 36, "bold"), text_color=TEXT_MUTED)
        self.rank_lbl.pack(pady=(15, 0))
        
        self.score_lbl = ctk.CTkLabel(metrics_frame, text="Рейтинг: 0.0%", font=("Segoe UI", 14), text_color=TEXT_MUTED)
        self.score_lbl.pack(pady=(0, 5))
        
        self.cv_lbl = ctk.CTkLabel(metrics_frame, text="Crit Value: 0.0", font=("Segoe UI", 14, "bold"), text_color="#A855F7")
        self.cv_lbl.pack(pady=(0, 15))
        
        # --- PROBABILITY / PROGRESS ---
        prob_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        prob_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(prob_frame, text="Прогноз улучшения (+20):", font=("Segoe UI", 12, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(prob_frame, progress_color="#3B82F6", fg_color=BG_INPUT)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.prob_details_lbl = ctk.CTkLabel(prob_frame, text="Шанс S-тира: 0%", font=("Segoe UI", 12), text_color=TEXT_MUTED)
        self.prob_details_lbl.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.advice_lbl = ctk.CTkLabel(self, text="Ожидание данных...", font=("Segoe UI", 12, "italic"), text_color=TEXT_MUTED, wraplength=280)
        self.advice_lbl.pack(fill="x", padx=15, pady=20)

    def _on_char_change(self, choice: str):
        if choice == "(Выберите персонажа)":
            self.role_menu.configure(values=["(Выберите билд)"])
            self.role_var.set("(Выберите билд)")
            self.selected_build = None
        else:
            builds = get_builds_for_character(choice)
            role_names = [b.role for b in builds] if builds else ["(Нет билдов)"]
            self.role_menu.configure(values=role_names)
            self.role_var.set(role_names[0] if role_names else "(Выберите билд)")
            self._on_role_change(self.role_var.get())
            
    def _on_role_change(self, choice: str):
        char = self.char_var.get()
        builds = get_builds_for_character(char)
        self.selected_build = next((b for b in builds if b.role == choice), None)
        self._recalculate()

    def update_forecast(self, artifact_data: dict):
        self.artifact_data = artifact_data
        self._recalculate()
        
    def _recalculate(self):
        if not self.artifact_data:
            return
            
        slot = self.artifact_data["slot"]
        main_stat = self.artifact_data["main_stat"]
        level = self.artifact_data["level"]
        substats = self.artifact_data["substats"]
        
        if not substats:
            self._reset_ui("Введите сабстаты для оценки")
            return
            
        # Determine weights
        if self.selected_build:
            weights = dict(self.selected_build.substat_weights)
        else:
            # Fallback universal DPS weights
            weights = {
                "Крит. Урон": 2.0, "Шанс крит. попадания": 2.0, 
                "Сила атаки %": 1.0, "Восст. энергии": 0.5
            }
            
        entries = [(i + 1, s, str(v)) for i, (s, v) in enumerate(substats)]
        is_3_stat = len(substats) <= 3 and level <= 4
        
        try:
            # 1. Evaluate Current Artifact
            ev = evaluate_artifact(level, is_3_stat, entries, weights, slot=slot, main_stat=main_stat)
            rank, color = get_rank(ev.potential_pct)
            
            self.rank_lbl.configure(text=rank, text_color=color)
            self.score_lbl.configure(text=f"Рейтинг: {ev.potential_pct:.1f}%")
            
            # 2. Upgrade Forecast
            curr_subs_dict = {s: v for s, v in substats}
            forecast = calculate_upgrade_forecast(
                slot=slot, main_stat=main_stat, current_substats=curr_subs_dict,
                level=level, substat_weights=weights
            )
            
            # Update Progress Bar based on expected final rating
            expected_pct = min(forecast.expected_pav / 100.0, 1.0)
            self.progress_bar.set(expected_pct)
            
            self.cv_lbl.configure(text=f"Crit Value (CV): {forecast.expected_cv:.1f}")
            self.prob_details_lbl.configure(text=f"Шанс S-тира (>70%): {forecast.prob_s_plus:.1f}%\nШанс SS-тира (>80%): {forecast.prob_ss_plus:.1f}%")
            
            advice = forecast.advice
            self.advice_lbl.configure(text=f"Вердикт: {advice}", text_color=color)
            
        except ArtifactInputError as e:
            self._reset_ui(str(e))
        except Exception as e:
            self._reset_ui(f"Ошибка расчета: {str(e)}")
            
    def _reset_ui(self, msg: str):
        self.rank_lbl.configure(text="?", text_color="#9CA3AF")
        self.score_lbl.configure(text="Рейтинг: 0.0%")
        self.cv_lbl.configure(text="Crit Value: 0.0")
        self.progress_bar.set(0)
        self.prob_details_lbl.configure(text="Шанс S-тира: 0%")
        self.advice_lbl.configure(text=msg, text_color="#EF4444")
