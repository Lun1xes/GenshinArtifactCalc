import math
from typing import Callable, List, Optional
import customtkinter as ctk

from ..theme import (
    ThemeColors,
    FONTS,
    METRICS,
    card_style,
    button_primary_style,
    button_secondary_style,
    button_accent_cyan_style,
    input_style,
    get_element_color,
)
from ...character_builds import CHARACTER_BUILDS, CharacterBuild
from ...icon_manager import icon_manager


class BuildsView(ctk.CTkFrame):
    def __init__(self, master, on_select_character: Optional[Callable[[str], None]] = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        
        self.on_select_character = on_select_character
        
        self.selected_element: str = "Все"
        self.search_query: str = ""
        self.selected_build: Optional[CharacterBuild] = None
        self.current_page: int = 1
        self.page_size: int = 24
        self.filtered_builds: List[CharacterBuild] = []
        self._search_after_id: Optional[str] = None
        
        # Pre-cache builds for fast O(1)/O(N) filtering without string allocation overhead
        self._builds_cache = [(b, b.element, b.display_name.lower()) for b in CHARACTER_BUILDS]
        
        self._build_ui()

    def _build_ui(self):
        # Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        title = ctk.CTkLabel(
            header,
            text="База мета-билдов персонажей (130+ сборок)",
            font=FONTS["title"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        )
        title.pack(side="left")

        # Element filter pills
        elem_row = ctk.CTkFrame(self, fg_color="transparent")
        elem_row.pack(fill="x", padx=10, pady=(0, 8))

        elements = ["Все", "Пиро", "Гидро", "Анемо", "Электро", "Дендро", "Крио", "Гео"]
        self.elem_buttons = {}
        for elem in elements:
            btn = ctk.CTkButton(
                elem_row,
                text=elem,
                width=60,
                height=26,
                font=FONTS["caption"],
                command=lambda e=elem: self._filter_by_element(e),
                **button_secondary_style(),
            )
            btn.pack(side="left", padx=2)
            self.elem_buttons[elem] = btn
        self._highlight_active_element_button("Все")

        # Search Bar
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Поиск по имени героя (Фурина, Райдэн, Невиллет...)",
            **input_style(),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Main Split Content (Left: list, Right: details)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=4)
        content_frame.grid_columnconfigure(1, weight=5)
        content_frame.grid_rowconfigure(0, weight=1)

        # 1. Left List Container
        left_box = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_box.grid_rowconfigure(0, weight=1)
        left_box.grid_rowconfigure(1, weight=0)
        left_box.grid_columnconfigure(0, weight=1)

        self.builds_list = ctk.CTkScrollableFrame(left_box, fg_color=ThemeColors.BG_CARD, corner_radius=METRICS["corner_radius_card"])
        self.builds_list.grid(row=0, column=0, sticky="nsew")

        # Pagination toolbar
        self.pagination_frame = ctk.CTkFrame(left_box, fg_color=ThemeColors.BG_PANEL, height=36, corner_radius=6)
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

        # 2. Right Details Card
        self.details_card = ctk.CTkFrame(content_frame, **card_style())
        self.details_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self._build_details_ui()
        self._render_builds_list()

    def _build_details_ui(self):
        # Empty placeholder initially
        self.details_container = ctk.CTkScrollableFrame(self.details_card, fg_color="transparent")
        self.details_container.pack(fill="both", expand=True, padx=15, pady=15)

        self.empty_lbl = ctk.CTkLabel(
            self.details_container,
            text="Выберите персонажа из списка слева для просмотра билда.",
            font=FONTS["body"],
            text_color=ThemeColors.TEXT_MUTED,
            justify="center",
        )
        self.empty_lbl.pack(pady=40)

    def _filter_by_element(self, element: str):
        self.selected_element = element
        self.current_page = 1
        self._highlight_active_element_button(element)
        self._render_builds_list()

    def _highlight_active_element_button(self, element: str):
        for e, btn in self.elem_buttons.items():
            if e == element:
                btn.configure(fg_color=ThemeColors.GOLD_DIM, text_color=ThemeColors.BG_DEEP)
            else:
                btn.configure(fg_color=ThemeColors.BG_CARD, text_color=ThemeColors.TEXT_PRIMARY)

    def _on_search_changed(self, event=None):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(150, self._perform_search)

    def _perform_search(self):
        self._search_after_id = None
        self.search_query = self.search_entry.get().strip().lower()
        self.current_page = 1
        self._render_builds_list()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_builds) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_current_page()

    def _render_builds_list(self):
        elem = self.selected_element
        query = self.search_query

        if elem == "Все" and not query:
            self.filtered_builds = list(CHARACTER_BUILDS)
        else:
            self.filtered_builds = [
                b for b, b_elem, b_name in self._builds_cache
                if (elem == "Все" or b_elem == elem) and (not query or query in b_name)
            ]

        total_items = len(self.filtered_builds)
        max_page = max(1, math.ceil(total_items / self.page_size))
        if self.current_page > max_page:
            self.current_page = max_page
        elif self.current_page < 1:
            self.current_page = 1

        self._render_current_page()

    def _render_current_page(self):
        for w in self.builds_list.winfo_children():
            w.destroy()
        try:
            self.builds_list._parent_canvas.yview_moveto(0)
        except Exception:
            pass

        total_items = len(self.filtered_builds)
        total_pages = max(1, math.ceil(total_items / self.page_size))

        self.prev_page_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        self.page_label.configure(text=f"Страница {self.current_page} из {total_pages} (Всего: {total_items})")

        if not self.filtered_builds:
            ctk.CTkLabel(self.builds_list, text="Персонажи не найдены.", font=FONTS["body"], text_color=ThemeColors.TEXT_MUTED).pack(pady=20)
            return

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        page_items = self.filtered_builds[start_idx:end_idx]

        for build in page_items:
            item_frame = ctk.CTkFrame(self.builds_list, **card_style(alt=True))
            item_frame.pack(fill="x", padx=4, pady=3)

            elem_col = get_element_color(build.element)
            
            # Badge with element
            badge = ctk.CTkLabel(item_frame, text=f" {build.element[:1]} ", font=FONTS["caption"], fg_color=elem_col, text_color=ThemeColors.BG_DEEP, corner_radius=4)
            badge.pack(side="left", padx=(8, 6), pady=6)

            info = ctk.CTkLabel(item_frame, text=build.display_name, font=FONTS["small_bold"], anchor="w")
            info.pack(side="left", fill="x", expand=True, padx=4)

            view_btn = ctk.CTkButton(
                item_frame,
                text="Смотреть",
                width=65,
                height=24,
                font=FONTS["caption"],
                command=lambda b=build: self._show_build_details(b),
                **button_secondary_style(),
            )
            view_btn.pack(side="right", padx=6, pady=6)

    def _show_build_details(self, build: CharacterBuild):
        self.selected_build = build
        for w in self.details_container.winfo_children():
            w.destroy()

        elem_col = get_element_color(build.element)

        # Header with character name and element
        head = ctk.CTkFrame(self.details_container, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(head, text=build.name, font=FONTS["title"], text_color=elem_col, anchor="w")
        title.pack(anchor="w")

        role = ctk.CTkLabel(head, text=f"Стихия: {build.element} | Роль: {build.build_name}", font=FONTS["body_bold"], text_color=ThemeColors.TEXT_MUTED, anchor="w")
        role.pack(anchor="w")

        # Select for Calculator CTA
        select_btn = ctk.CTkButton(
            self.details_container,
            text="✨ Выбрать этого персонажа для калькулятора",
            height=34,
            command=lambda: self._apply_to_calculator(build.name),
            **button_primary_style(),
        )
        select_btn.pack(fill="x", pady=(0, 15))

        # Recommended Artifact Sets
        sets_card = ctk.CTkFrame(self.details_container, fg_color=ThemeColors.BG_PANEL, corner_radius=8)
        sets_card.pack(fill="x", pady=5)
        ctk.CTkLabel(sets_card, text="Рекомендуемые наборы артефактов:", font=FONTS["small_bold"], text_color=ThemeColors.GOLD).pack(anchor="w", padx=10, pady=(8, 4))
        sets_text = "\n".join([f" • {s}" for s in build.best_sets]) if build.best_sets else "Любые подходящие"
        ctk.CTkLabel(sets_card, text=sets_text, font=FONTS["small"], justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        # Recommended Main Stats
        stats_card = ctk.CTkFrame(self.details_container, fg_color=ThemeColors.BG_PANEL, corner_radius=8)
        stats_card.pack(fill="x", pady=5)
        ctk.CTkLabel(stats_card, text="Главные характеристики:", font=FONTS["small_bold"], text_color=ThemeColors.CYAN).pack(anchor="w", padx=10, pady=(8, 4))
        
        sands = ", ".join(build.main_stats.get("Пески времени", ["Любые"]))
        goblet = ", ".join(build.main_stats.get("Кубок пространства", ["Любые"]))
        circlet = ", ".join(build.main_stats.get("Корона разума", ["Любые"]))
        
        stat_lines = f" • ⏳ Пески времени: {sands}\n • 🍷 Кубок пространства: {goblet}\n • 👑 Корона разума: {circlet}"
        ctk.CTkLabel(stats_card, text=stat_lines, font=FONTS["small"], justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        # Top Weapons
        weap_card = ctk.CTkFrame(self.details_container, fg_color=ThemeColors.BG_PANEL, corner_radius=8)
        weap_card.pack(fill="x", pady=5)
        ctk.CTkLabel(weap_card, text="Топ оружие:", font=FONTS["small_bold"], text_color=ThemeColors.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 4))
        weap_text = "\n".join([f" {i+1}. {w}" for i, w in enumerate(build.top_weapon_names[:4])]) if build.top_weapon_names else "Любое"
        ctk.CTkLabel(weap_card, text=weap_text, font=FONTS["small"], justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        # Notes / ER
        if build.notes:
            notes_card = ctk.CTkFrame(self.details_container, fg_color=ThemeColors.BG_PANEL, corner_radius=8)
            notes_card.pack(fill="x", pady=5)
            ctk.CTkLabel(notes_card, text="Советы и требования к ВЭ:", font=FONTS["small_bold"], text_color=ThemeColors.YELLOW_WARN).pack(anchor="w", padx=10, pady=(8, 4))
            ctk.CTkLabel(notes_card, text=build.notes, font=FONTS["small"], wraplength=320, justify="left").pack(anchor="w", padx=15, pady=(0, 8))

    def _apply_to_calculator(self, char_name: str):
        if self.on_select_character:
            self.on_select_character(char_name)
