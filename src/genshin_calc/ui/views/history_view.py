"""History and Side-by-Side Comparison View for saved artifacts.

Optimized with:
- Pagination (20 items per page) to eliminate lag & CPU saturation
- Smart caching based on file mtime to avoid unnecessary re-reads
- Search bar with debounced input (set, main stat, character, substats)
- Sorting (newest, potential desc/asc, CV desc, level desc)
- Item deletion and bulk history clear
- Side-by-side comparison including 'Current from Calculator'
"""
from __future__ import annotations

from decimal import Decimal
import json
import math
import os
from typing import Any, Callable, Dict, List, Optional, Tuple
import tkinter as tk
import customtkinter as ctk

from ..theme import (
    ThemeColors,
    FONTS,
    METRICS,
    card_style,
    button_primary_style,
    button_secondary_style,
    button_accent_cyan_style,
    button_danger_style,
    dropdown_style,
    input_style,
    get_rank,
)
from ...artifact_logic import ARTIFACT_SLOTS, SLOT_EMOJI
from ...good_adapter import ParsedArtifact


class HistoryView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_transfer_to_calculator: Optional[Callable[[ParsedArtifact], None]] = None,
        get_current_calculator_artifact: Optional[Callable[[], Optional[dict]]] = None,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self.on_transfer_to_calculator = on_transfer_to_calculator
        self.get_current_calculator_artifact = get_current_calculator_artifact

        # Data & Cache state
        self.history_records: List[dict] = []
        self.filtered_records: List[dict] = []
        self._cache_mtime: float = -1.0

        # Pagination state
        self.current_page: int = 1
        self.page_size: int = 20

        # Filter & Sort state
        self.selected_slot_filter: str = "Все"
        self.selected_rank_filter: str = "Все"
        self.selected_sort: str = "Новые"
        self.search_query: str = ""
        self._search_timer: Optional[str] = None

        # Comparison selections
        self.compare_a: Optional[dict] = None
        self.compare_b: Optional[dict] = None

        self._build_ui()
        self.refresh_history(force=True)

    def _get_history_file(self) -> str:
        try:
            from ...calculator import HISTORY_FILE
            return HISTORY_FILE
        except Exception:
            return "artifact_history.json"

    def _build_ui(self):
        # 1. Top Controls Bar
        top_bar = ctk.CTkFrame(self, fg_color=ThemeColors.BG_CARD, corner_radius=METRICS["corner_radius_card"])
        top_bar.pack(fill="x", padx=10, pady=(10, 6))

        # Title & Count
        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left", padx=(12, 10), pady=8)

        ctk.CTkLabel(
            title_box,
            text="📜 История и Сравнение",
            font=FONTS["title"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(
            title_box,
            text="",
            font=FONTS["caption"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        )
        self.count_label.pack(side="left", padx=(10, 0), pady=(3, 0))

        # Action buttons on right
        actions_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_box.pack(side="right", padx=(4, 10), pady=8)

        clear_all_btn = ctk.CTkButton(
            actions_box,
            text="🗑️ Очистить всё",
            width=110,
            height=28,
            font=FONTS["caption"],
            command=self._clear_all_history,
            **button_danger_style(),
        )
        clear_all_btn.pack(side="right", padx=(4, 0))

        reload_btn = ctk.CTkButton(
            actions_box,
            text="🔄 Обновить",
            width=90,
            height=28,
            font=FONTS["caption"],
            command=lambda: self.refresh_history(force=True),
            **button_secondary_style(),
        )
        reload_btn.pack(side="right", padx=4)

        # 2. Filters & Search Row
        filters_bar = ctk.CTkFrame(self, fg_color="transparent")
        filters_bar.pack(fill="x", padx=10, pady=(0, 8))

        # Slot filter
        ctk.CTkLabel(filters_bar, text="Слот:", font=FONTS["small_bold"], text_color=ThemeColors.TEXT_MUTED).pack(side="left", padx=(0, 4))
        slot_options = ["Все"] + list(ARTIFACT_SLOTS)
        self.slot_filter_menu = ctk.CTkOptionMenu(
            filters_bar,
            values=slot_options,
            command=self._on_slot_filter,
            width=135,
            height=28,
            **dropdown_style(),
        )
        self.slot_filter_menu.pack(side="left", padx=(0, 8))

        # Rank filter
        ctk.CTkLabel(filters_bar, text="Ранг:", font=FONTS["small_bold"], text_color=ThemeColors.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.rank_filter_menu = ctk.CTkOptionMenu(
            filters_bar,
            values=["Все", "SSS", "SS", "S", "A", "B", "C"],
            command=self._on_rank_filter,
            width=85,
            height=28,
            **dropdown_style(),
        )
        self.rank_filter_menu.pack(side="left", padx=(0, 8))

        # Sort filter
        ctk.CTkLabel(filters_bar, text="Сорт.:", font=FONTS["small_bold"], text_color=ThemeColors.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.sort_menu = ctk.CTkOptionMenu(
            filters_bar,
            values=["Новые", "Потенциал ↓", "Потенциал ↑", "CV ↓", "Уровень ↓"],
            command=self._on_sort_filter,
            width=130,
            height=28,
            **dropdown_style(),
        )
        self.sort_menu.pack(side="left", padx=(0, 8))

        # Search field
        self.search_var = ctk.StringVar(value="")
        self.search_entry = ctk.CTkEntry(
            filters_bar,
            placeholder_text="🔍 Поиск по сету / статам / герою...",
            textvariable=self.search_var,
            width=210,
            height=28,
            **input_style(),
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Return>", lambda _: self._on_search_timer_fired())

        # 3. Main Split View: Left (Cards + Pagination), Right (Comparison Diff)
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        split.grid_columnconfigure(0, weight=5)
        split.grid_columnconfigure(1, weight=4)
        split.grid_rowconfigure(0, weight=1)

        # --- Left Column Container ---
        left_container = ctk.CTkFrame(split, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_rowconfigure(1, weight=0)
        left_container.grid_columnconfigure(0, weight=1)

        # Scrollable Cards Area
        self.list_frame = ctk.CTkScrollableFrame(
            left_container,
            fg_color=ThemeColors.BG_CARD,
            corner_radius=METRICS["corner_radius_card"],
        )
        self.list_frame.grid(row=0, column=0, sticky="nsew")

        self.cards_box = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.cards_box.pack(fill="both", expand=True, padx=2, pady=2)

        # Pagination Toolbar
        self.pagination_frame = ctk.CTkFrame(left_container, fg_color=ThemeColors.BG_PANEL, height=36, corner_radius=6)
        self.pagination_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.prev_page_btn = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Назад",
            width=75,
            height=26,
            font=FONTS["caption"],
            command=self._prev_page,
            **button_secondary_style(),
        )
        self.prev_page_btn.pack(side="left", padx=8, pady=4)

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Страница 1 из 1",
            font=FONTS["small_bold"],
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        self.page_label.pack(side="left", expand=True)

        self.next_page_btn = ctk.CTkButton(
            self.pagination_frame,
            text="Вперёд ▶",
            width=75,
            height=26,
            font=FONTS["caption"],
            command=self._next_page,
            **button_secondary_style(),
        )
        self.next_page_btn.pack(side="right", padx=8, pady=4)

        # --- Right Column (Comparison Panel) ---
        self.compare_frame = ctk.CTkFrame(split, **card_style())
        self.compare_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._build_compare_ui()

    def _build_compare_ui(self):
        head = ctk.CTkFrame(self.compare_frame, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(head, text="Сравнение (Side-by-Side)", font=FONTS["header"], text_color=ThemeColors.CYAN).pack(side="left")

        btn_box = ctk.CTkFrame(head, fg_color="transparent")
        btn_box.pack(side="right")

        self.calc_compare_btn = ctk.CTkButton(
            btn_box,
            text="⚡ Из калькулятора",
            width=115,
            height=24,
            font=FONTS["caption"],
            command=self._set_compare_from_calculator,
            **button_accent_cyan_style(),
        )
        self.calc_compare_btn.pack(side="left", padx=(0, 4))

        clear_cmp_btn = ctk.CTkButton(
            btn_box,
            text="Сброс",
            width=50,
            height=24,
            font=FONTS["caption"],
            command=self._clear_comparison,
            **button_secondary_style(),
        )
        clear_cmp_btn.pack(side="left")

        self.compare_container = ctk.CTkScrollableFrame(self.compare_frame, fg_color="transparent")
        self.compare_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._render_compare_state()

    # ──────────────────────────────────────────────────────────────────
    #  CACHE & DATA LOADING
    # ──────────────────────────────────────────────────────────────────
    def refresh_history(self, if_needed: bool = False, force: bool = False):
        path = self._get_history_file()
        if not os.path.exists(path):
            self.history_records = []
            self._cache_mtime = 0.0
            self._apply_filters_and_render()
            return

        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0

        if if_needed and not force and mtime == self._cache_mtime and self.history_records:
            return

        self._cache_mtime = mtime
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.history_records = data if isinstance(data, list) else []
        except Exception:
            self.history_records = []

        self._apply_filters_and_render()

    def _save_history_to_disk(self):
        path = self._get_history_file()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.history_records, f, ensure_ascii=False, indent=2)
            self._cache_mtime = os.path.getmtime(path)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────
    #  FILTERS, SEARCH & SORTING
    # ──────────────────────────────────────────────────────────────────
    def _on_slot_filter(self, choice: str):
        self.selected_slot_filter = choice
        self.current_page = 1
        self._apply_filters_and_render()

    def _on_rank_filter(self, choice: str):
        self.selected_rank_filter = choice
        self.current_page = 1
        self._apply_filters_and_render()

    def _on_sort_filter(self, choice: str):
        self.selected_sort = choice
        self.current_page = 1
        self._apply_filters_and_render()

    def _on_search_key(self, event=None):
        if self._search_timer is not None:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
        self._search_timer = self.after(180, self._on_search_timer_fired)

    def _on_search_timer_fired(self):
        self._search_timer = None
        self.search_query = self.search_var.get().strip().lower()
        self.current_page = 1
        self._apply_filters_and_render()

    def _apply_filters_and_render(self):
        filtered = []
        q = self.search_query

        for item in self.history_records:
            # Slot filter
            slot = item.get("slot", "")
            if self.selected_slot_filter != "Все" and slot != self.selected_slot_filter:
                continue

            # Rank filter
            rank = item.get("rank", "—")
            if self.selected_rank_filter != "Все" and rank != self.selected_rank_filter:
                continue

            # Text Search
            if q:
                set_name = self._get_item_set_name(item).lower()
                set_key = str(item.get("set_key", "")).lower()
                char_name = str(item.get("character", "") or item.get("location", "")).lower()
                main_stat = str(item.get("main_stat", "")).lower()
                subs_text = " ".join(f"{s} {v}" for s, v in self._get_item_substats(item)).lower()
                search_blob = f"{slot.lower()} {set_name} {set_key} {char_name} {main_stat} {subs_text}"
                if q not in search_blob:
                    continue

            filtered.append(item)

        # Sorting
        if self.selected_sort == "Потенциал ↓":
            filtered.sort(key=self._get_item_potential, reverse=True)
        elif self.selected_sort == "Потенциал ↑":
            filtered.sort(key=self._get_item_potential)
        elif self.selected_sort == "CV ↓":
            filtered.sort(key=self._get_item_cv, reverse=True)
        elif self.selected_sort == "Уровень ↓":
            filtered.sort(key=self._get_item_level, reverse=True)

        self.filtered_records = filtered

        # Adjust page boundary
        total_items = len(filtered)
        max_page = max(1, math.ceil(total_items / self.page_size))
        if self.current_page > max_page:
            self.current_page = max_page
        elif self.current_page < 1:
            self.current_page = 1

        # Update count label
        if total_items > 0:
            start_num = (self.current_page - 1) * self.page_size + 1
            end_num = min(self.current_page * self.page_size, total_items)
            self.count_label.configure(
                text=f"Показано {start_num}–{end_num} из {total_items} (Всего: {len(self.history_records)})"
            )
        else:
            self.count_label.configure(text=f"Всего: {len(self.history_records)}")

        self._render_current_page()

    # ──────────────────────────────────────────────────────────────────
    #  PAGINATION & CARD RENDERING
    # ──────────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._apply_filters_and_render()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_records) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._apply_filters_and_render()

    def _render_current_page(self):
        # Clear only cards_box
        for child in self.cards_box.winfo_children():
            child.destroy()

        total_items = len(self.filtered_records)
        total_pages = max(1, math.ceil(total_items / self.page_size))

        # Update pagination buttons state
        self.prev_page_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        self.page_label.configure(text=f"Страница {self.current_page} из {total_pages}")

        if not self.filtered_records:
            empty_msg = "История пуста." if not self.history_records else "Нет артефактов, соответствующих фильтрам."
            ctk.CTkLabel(
                self.cards_box,
                text=empty_msg,
                font=FONTS["body"],
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(pady=40)
            return

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        page_items = self.filtered_records[start_idx:end_idx]

        for idx, item in enumerate(page_items):
            self._create_artifact_card(self.cards_box, item, idx)

    def _create_artifact_card(self, parent, item: dict, idx: int):
        card = ctk.CTkFrame(parent, **card_style(alt=(idx % 2 == 1)))
        card.pack(fill="x", padx=4, pady=3)

        slot = item.get("slot", "Слот")
        emoji = SLOT_EMOJI.get(slot, "✦")
        rank = item.get("rank", "—")
        pot = self._get_item_potential(item)
        _, r_col = get_rank(pot)
        cv = self._get_item_cv(item)
        lvl = self._get_item_level(item)
        set_name = self._get_item_set_name(item)
        main_stat = item.get("main_stat", "—")

        loc = item.get("location") or item.get("character") or "Инвентарь"
        loc_str = f"👤 {loc}" if loc != "Инвентарь" else "🎒 Инвентарь"

        # 1. Left badge
        badge = ctk.CTkLabel(
            card,
            text=f" {emoji} {rank} ",
            font=FONTS["caption"],
            fg_color=r_col,
            text_color="#ffffff",
            corner_radius=4,
        )
        badge.pack(side="left", padx=8, pady=6)

        # 2. Center info
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        line1 = f"{slot} (+{lvl}) • {set_name} • ({loc_str})"
        ctk.CTkLabel(
            info_box,
            text=line1,
            font=FONTS["small_bold"],
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        line2 = f"🎯 {main_stat}   |   Оценка: {pot:.1f}%   |   CV: {cv:.1f}"
        ctk.CTkLabel(
            info_box,
            text=line2,
            font=FONTS["caption"],
            text_color=ThemeColors.CYAN,
            anchor="w",
        ).pack(fill="x")

        subs = self._get_item_substats(item)
        if subs:
            subs_str = "   •   ".join(f"{s}: {v:.1f}" if isinstance(v, float) and v % 1 != 0 else f"{s}: {v}" for s, v in subs)
            ctk.CTkLabel(
                info_box,
                text=subs_str,
                font=FONTS["caption"],
                text_color=ThemeColors.TEXT_SUBS,
                anchor="w",
            ).pack(fill="x", pady=(1, 0))

        # 3. Right action buttons
        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(side="right", padx=6, pady=4)

        ctk.CTkButton(
            btn_box,
            text="📥 В калькулятор",
            width=90,
            height=22,
            font=FONTS["caption"],
            command=lambda it=item: self._load_to_calculator(it),
            **button_accent_cyan_style(),
        ).pack(side="top", pady=1)

        row2 = ctk.CTkFrame(btn_box, fg_color="transparent")
        row2.pack(side="top", pady=1)

        ctk.CTkButton(
            row2,
            text="Сравн. А",
            width=42,
            height=20,
            font=FONTS["caption"],
            command=lambda it=item: self._set_compare_a(it),
            **button_secondary_style(),
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            row2,
            text="Сравн. Б",
            width=42,
            height=20,
            font=FONTS["caption"],
            command=lambda it=item: self._set_compare_b(it),
            **button_secondary_style(),
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            row2,
            text="🗑️",
            width=26,
            height=20,
            font=FONTS["caption"],
            command=lambda it=item: self._delete_item(it),
            **button_danger_style(),
        ).pack(side="left", padx=(2, 0))

    # ──────────────────────────────────────────────────────────────────
    #  SIDE-BY-SIDE COMPARISON
    # ──────────────────────────────────────────────────────────────────
    def _set_compare_a(self, item: dict):
        self.compare_a = item
        self._render_compare_state()

    def _set_compare_b(self, item: dict):
        self.compare_b = item
        self._render_compare_state()

    def _set_compare_from_calculator(self):
        if not self.get_current_calculator_artifact:
            return
        art = self.get_current_calculator_artifact()
        if not art:
            self._render_compare_state(toast="⚠️ В калькуляторе пока нет рассчитанного артефакта!")
            return
        self.compare_a = art
        self._render_compare_state()

    def _clear_comparison(self):
        self.compare_a = None
        self.compare_b = None
        self._render_compare_state()

    def _render_compare_state(self, toast: Optional[str] = None):
        for w in self.compare_container.winfo_children():
            w.destroy()

        if toast:
            ctk.CTkLabel(
                self.compare_container,
                text=toast,
                font=FONTS["small_bold"],
                text_color=ThemeColors.YELLOW,
            ).pack(pady=10)

        if not self.compare_a and not self.compare_b:
            ctk.CTkLabel(
                self.compare_container,
                text="Нажмите «Сравн. А» и «Сравн. Б» у любых артефактов\nили «⚡ Из калькулятора» для мгновенного анализа.",
                font=FONTS["small"],
                text_color=ThemeColors.TEXT_MUTED,
                justify="center",
            ).pack(pady=40)
            return

        # Render Side-by-Side Cards
        if self.compare_a:
            self._render_compare_mini_card(self.compare_container, self.compare_a, "Артефакт А", ThemeColors.CYAN)
        else:
            ctk.CTkLabel(
                self.compare_container,
                text="[ Выберите Артефакт А ]",
                font=FONTS["caption"],
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(pady=4)

        if self.compare_b:
            self._render_compare_mini_card(self.compare_container, self.compare_b, "Артефакт Б", ThemeColors.GOLD)
        else:
            ctk.CTkLabel(
                self.compare_container,
                text="[ Выберите Артефакт Б ]",
                font=FONTS["caption"],
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(pady=4)

        # Render Diff Breakdown if both present
        if self.compare_a and self.compare_b:
            self._render_compare_diff(self.compare_container, self.compare_a, self.compare_b)

    def _render_compare_mini_card(self, parent, item: dict, title: str, accent: str):
        card = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_CARD_ALT, corner_radius=8, border_width=1, border_color=accent)
        card.pack(fill="x", pady=4, padx=2)

        slot = item.get("slot", "—")
        lvl = self._get_item_level(item)
        set_name = self._get_item_set_name(item)
        rank = item.get("rank", "—")
        main_stat = item.get("main_stat", "—")
        pot = self._get_item_potential(item)
        cv = self._get_item_cv(item)

        is_current = item.get("is_current", False)
        prefix = f"{title} (Калькулятор)" if is_current else title

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(4, 1))

        ctk.CTkLabel(hdr, text=f"{prefix}: [{rank}]", font=FONTS["small_bold"], text_color=accent).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{slot} (+{lvl})", font=FONTS["caption"], text_color=ThemeColors.TEXT_PRIMARY).pack(side="right")

        ctk.CTkLabel(
            card,
            text=f"🔮 {set_name} | 🎯 {main_stat} | Оценка: {pot:.1f}% | CV: {cv:.1f}",
            font=FONTS["caption"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 4))

    def _render_compare_diff(self, parent, art_a: dict, art_b: dict):
        diff_box = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_PANEL, corner_radius=8)
        diff_box.pack(fill="x", pady=6, padx=2)

        ctk.CTkLabel(
            diff_box,
            text="📊 Анализ разницы (А vs Б):",
            font=FONTS["small_bold"],
            text_color=ThemeColors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=10, pady=(6, 4))

        score_a = self._get_item_potential(art_a)
        score_b = self._get_item_potential(art_b)
        diff_score = score_a - score_b
        score_sign = "+" if diff_score > 0 else ""
        score_color = ThemeColors.GREEN if diff_score > 0.1 else (ThemeColors.RED if diff_score < -0.1 else ThemeColors.CYAN)

        cv_a = self._get_item_cv(art_a)
        cv_b = self._get_item_cv(art_b)
        diff_cv = cv_a - cv_b
        cv_sign = "+" if diff_cv > 0 else ""
        cv_color = ThemeColors.GREEN if diff_cv > 0.1 else (ThemeColors.RED if diff_cv < -0.1 else ThemeColors.CYAN)

        summary_frame = ctk.CTkFrame(diff_box, fg_color="transparent")
        summary_frame.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(
            summary_frame,
            text=f"• Потенциал: {score_sign}{diff_score:.1f}%  (А: {score_a:.1f}% / Б: {score_b:.1f}%)",
            font=FONTS["small_bold"],
            text_color=score_color,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            summary_frame,
            text=f"• Crit Value: {cv_sign}{diff_cv:.1f}  (А: {cv_a:.1f} / Б: {cv_b:.1f})",
            font=FONTS["small_bold"],
            text_color=cv_color,
            anchor="w",
        ).pack(fill="x")

        # Substat breakdown table
        subs_a = dict(self._get_item_substats(art_a))
        subs_b = dict(self._get_item_substats(art_b))
        all_stats = list(dict.fromkeys(list(subs_a.keys()) + list(subs_b.keys())))

        if all_stats:
            sep = ctk.CTkFrame(diff_box, height=1, fg_color=ThemeColors.BORDER)
            sep.pack(fill="x", padx=10, pady=(4, 4))

            ctk.CTkLabel(
                diff_box,
                text="Детализация по сабстатам:",
                font=FONTS["caption"],
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(anchor="w", padx=10, pady=(0, 2))

            for s_name in all_stats:
                v_a = subs_a.get(s_name)
                v_b = subs_b.get(s_name)

                row = ctk.CTkFrame(diff_box, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=1)

                ctk.CTkLabel(row, text=f"• {s_name}:", font=FONTS["caption"], width=130, anchor="w").pack(side="left")

                if v_a is not None and v_b is not None:
                    d = v_a - v_b
                    sign = "+" if d > 0 else ""
                    tag_col = ThemeColors.GREEN if d > 0.05 else (ThemeColors.TEXT_MUTED if abs(d) <= 0.05 else ThemeColors.RED)
                    txt = f"{v_a:.1f} vs {v_b:.1f} ({sign}{d:.1f})"
                    ctk.CTkLabel(row, text=txt, font=FONTS["caption"], text_color=tag_col).pack(side="left", padx=4)
                elif v_a is not None:
                    txt = f"{v_a:.1f} (только в А)"
                    ctk.CTkLabel(row, text=txt, font=FONTS["caption"], text_color=ThemeColors.CYAN).pack(side="left", padx=4)
                else:
                    txt = f"{v_b:.1f} (только в Б)"
                    ctk.CTkLabel(row, text=txt, font=FONTS["caption"], text_color=ThemeColors.GOLD).pack(side="left", padx=4)

    # ──────────────────────────────────────────────────────────────────
    #  ITEM ACTIONS
    # ──────────────────────────────────────────────────────────────────
    def _load_to_calculator(self, item: dict):
        if not self.on_transfer_to_calculator:
            return

        subs = self._get_item_substats(item)
        subs_decimal = []
        for s_name, s_val in subs:
            try:
                subs_decimal.append((s_name, Decimal(str(s_val))))
            except Exception:
                pass

        slot = item.get("slot", "Цветок жизни")
        main_stat = item.get("main_stat", "HP")
        level = self._get_item_level(item)
        set_key = item.get("set_key", "")
        if not set_key and item.get("set"):
            from ...character_builds import SET_NAME_TO_KEY
            set_key = SET_NAME_TO_KEY.get(item.get("set"), "")

        parsed = ParsedArtifact(
            slot=slot,
            main_stat=main_stat,
            level=level,
            rarity=5,
            substats=subs_decimal,
            set_key=set_key,
            location=item.get("location", ""),
        )
        self.on_transfer_to_calculator(parsed)

    def _delete_item(self, target_item: dict):
        self.history_records = [h for h in self.history_records if h is not target_item]
        if self.compare_a is target_item:
            self.compare_a = None
        if self.compare_b is target_item:
            self.compare_b = None

        self._save_history_to_disk()
        self._apply_filters_and_render()
        self._render_compare_state()

    def _clear_all_history(self):
        self.history_records = []
        self.compare_a = None
        self.compare_b = None
        self._save_history_to_disk()
        self._apply_filters_and_render()
        self._render_compare_state()

    # ──────────────────────────────────────────────────────────────────
    #  STATIC HELPERS FOR DATA EXTRACTION
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _get_item_substats(item: dict) -> list[tuple[str, float]]:
        raw_subs = item.get("substats")
        if isinstance(raw_subs, dict):
            res = []
            for k, v in raw_subs.items():
                try:
                    res.append((str(k), float(v)))
                except (ValueError, TypeError):
                    pass
            return res
        elif isinstance(raw_subs, list):
            res = []
            for entry in raw_subs:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    try:
                        res.append((str(entry[0]), float(entry[1])))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(entry, dict) and "key" in entry and "value" in entry:
                    try:
                        from ...good_adapter import STAT_KEY_TO_RU
                        k = STAT_KEY_TO_RU.get(entry["key"], entry["key"])
                        res.append((str(k), float(entry["value"])))
                    except Exception:
                        pass
            return res
        return []

    @staticmethod
    def _get_item_cv(item: dict) -> float:
        if "crit_value" in item:
            try:
                return float(item["crit_value"])
            except (ValueError, TypeError):
                pass
        cv = 0.0
        for s_name, s_val in HistoryView._get_item_substats(item):
            if "Крит. шанс" in s_name:
                cv += s_val * 2
            elif "Крит. урон" in s_name:
                cv += s_val
        return round(cv, 1)

    @staticmethod
    def _get_item_potential(item: dict) -> float:
        for k in ("potential_pct", "current_pct", "expected_pct"):
            if k in item:
                try:
                    return float(item[k])
                except (ValueError, TypeError):
                    pass
        return 0.0

    @staticmethod
    def _get_item_level(item: dict) -> int:
        lvl = item.get("level", 0)
        if isinstance(lvl, int):
            return lvl
        cleaned = str(lvl).replace("+", "").strip()
        if cleaned.isdigit():
            return int(cleaned)
        return 0

    @staticmethod
    def _get_item_set_name(item: dict) -> str:
        set_name = item.get("set")
        if set_name and set_name != "(Не выбран)":
            return set_name
        set_key = item.get("set_key", "")
        if set_key:
            from ...character_builds import get_set_name_ru
            ru = get_set_name_ru(set_key)
            if ru:
                return ru
            return set_key
        return "Без сета"
