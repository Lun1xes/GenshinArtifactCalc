"""Scanner and Import View supporting Enka.Network, Inventory Kamera, and GOOD JSON."""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional
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
    dropdown_style,
)
from ...enka_adapter import validate_uid, fetch_showcase, parse_enka_showcase
from ...good_adapter import ParsedArtifact, parse_good_json_string
from ...kamera_adapter import find_good_files, load_kamera_json, extract_parsed_artifacts
from ...utils import get_project_root


class ScannerView(ctk.CTkFrame):
    def __init__(self, master, on_transfer_to_calculator: Optional[Callable[[ParsedArtifact], None]] = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        
        self.on_transfer_to_calculator = on_transfer_to_calculator
        
        # Internal state
        self.active_tab = "enka"
        self.scanned_artifacts: List[ParsedArtifact] = []
        self.current_page = 0
        self.page_size = 10
        
        self._build_ui()

    def _build_ui(self):
        # Header / Tab Switcher
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 10))

        title = ctk.CTkLabel(
            header,
            text="Импорт и Сканирование артефактов",
            font=FONTS["title"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        )
        title.pack(side="left")

        # Tab segmented buttons
        self.tab_segmented = ctk.CTkSegmentedButton(
            header,
            values=["Enka.Network (UID)", "Inventory Kamera", "GOOD JSON"],
            command=self._on_tab_changed,
            selected_color=ThemeColors.GOLD_DIM,
            selected_hover_color=ThemeColors.GOLD,
            unselected_color=ThemeColors.BG_CARD,
            unselected_hover_color=ThemeColors.BG_HOVER,
            text_color=ThemeColors.BG_DEEP,
            font=FONTS["body_bold"],
        )
        self.tab_segmented.pack(side="right")
        self.tab_segmented.set("Enka.Network (UID)")

        # Main dynamic container
        self.container = ctk.CTkFrame(self, fg_color=ThemeColors.BG_CARD, corner_radius=METRICS["corner_radius_card"])
        self.container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Render initial tab
        self._render_enka_tab()

    def _on_tab_changed(self, choice: str):
        for w in self.container.winfo_children():
            w.destroy()

        if "Enka" in choice:
            self._render_enka_tab()
        elif "Kamera" in choice:
            self._render_kamera_tab()
        elif "GOOD" in choice:
            self._render_good_tab()

    # ─────────────────────────────────────────────────────────────────
    # Enka.Network Tab
    # ─────────────────────────────────────────────────────────────────
    def _render_enka_tab(self):
        # Description
        top_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            top_frame,
            text="Загрузка артефактов из витрины персонажей Enka.Network по UID игрока.",
            font=FONTS["body"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        input_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        input_row.pack(fill="x")

        ctk.CTkLabel(input_row, text="UID игрока:", font=FONTS["body_bold"], text_color=ThemeColors.TEXT_PRIMARY).pack(side="left", padx=(0, 10))

        self.uid_entry = ctk.CTkEntry(
            input_row,
            width=180,
            placeholder_text="700123456",
            **input_style(),
        )
        self.uid_entry.pack(side="left", padx=(0, 10))

        self.fetch_btn = ctk.CTkButton(
            input_row,
            text="Загрузить витрину",
            width=140,
            command=self._fetch_enka_showcase,
            **button_primary_style(),
        )
        self.fetch_btn.pack(side="left")

        self.enka_status_lbl = ctk.CTkLabel(top_frame, text="", font=FONTS["small"], text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self.enka_status_lbl.pack(fill="x", pady=(5, 0))

        # Results area
        self.enka_results = ctk.CTkScrollableFrame(self.container, fg_color=ThemeColors.BG_CARD_ALT, corner_radius=8)
        self.enka_results.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _fetch_enka_showcase(self):
        uid = self.uid_entry.get().strip()
        if not validate_uid(uid):
            self.enka_status_lbl.configure(text="❌ Некорректный UID: требуется 9 цифр.", text_color=ThemeColors.RED)
            return

        self.fetch_btn.configure(state="disabled", text="Загрузка...")
        self.enka_status_lbl.configure(text="Подключение к Enka.Network...", text_color=ThemeColors.CYAN)

        def worker():
            try:
                payload = fetch_showcase(uid)
                res = parse_enka_showcase(payload)
                self.after(0, lambda: self._on_enka_success(res))
            except Exception as e:
                self.after(0, lambda: self._on_enka_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_enka_success(self, res: dict):
        self.fetch_btn.configure(state="normal", text="Загрузить витрину")
        chars = res.get("characters", [])
        self.enka_status_lbl.configure(text=f"✅ Найдено персонажей: {len(chars)}", text_color=ThemeColors.GREEN)

        for w in self.enka_results.winfo_children():
            w.destroy()

        if not chars:
            ctk.CTkLabel(self.enka_results, text="Витрина пуста или скрыта в настройках игры.", font=FONTS["body"]).pack(pady=20)
            return

        for char_info in chars:
            c_name = char_info.get("name", "Персонаж")
            card = ctk.CTkFrame(self.enka_results, **card_style(border=True))
            card.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(card, text=f"👤 {c_name}", font=FONTS["header"], text_color=ThemeColors.GOLD).pack(anchor="w", padx=10, pady=(6, 4))

            artifacts = char_info.get("artifacts", [])
            for art in artifacts:
                row = ctk.CTkFrame(card, fg_color=ThemeColors.BG_PANEL, corner_radius=6)
                row.pack(fill="x", padx=8, pady=3)

                info_txt = f"{art.slot} | {art.main_stat} | +{art.level} | Сабстатов: {len(art.substats)}"
                ctk.CTkLabel(row, text=info_txt, font=FONTS["small"]).pack(side="left", padx=8, pady=4)

                transfer_btn = ctk.CTkButton(
                    row,
                    text="В калькулятор",
                    width=100,
                    height=24,
                    font=FONTS["caption"],
                    command=lambda a=art: self._transfer_artifact(a),
                    **button_accent_cyan_style(),
                )
                transfer_btn.pack(side="right", padx=8, pady=4)

    def _on_enka_error(self, err: str):
        self.fetch_btn.configure(state="normal", text="Загрузить витрину")
        self.enka_status_lbl.configure(text=f"❌ Ошибка загрузки: {err}", text_color=ThemeColors.RED)

    # ─────────────────────────────────────────────────────────────────
    # Inventory Kamera Tab
    # ─────────────────────────────────────────────────────────────────
    def _render_kamera_tab(self):
        top_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            top_frame,
            text="Импорт результатов сканирования Inventory Kamera (папка kamera/GenshinData/).",
            font=FONTS["body"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        scan_btn = ctk.CTkButton(
            btn_row,
            text="Проверить сканы",
            command=self._scan_kamera_folder,
            **button_primary_style(),
        )
        scan_btn.pack(side="left", padx=(0, 10))

        self.kamera_status_lbl = ctk.CTkLabel(btn_row, text="", font=FONTS["small"], text_color=ThemeColors.TEXT_MUTED)
        self.kamera_status_lbl.pack(side="left")

        # Table & Pagination
        self.kamera_results = ctk.CTkScrollableFrame(self.container, fg_color=ThemeColors.BG_CARD_ALT, corner_radius=8)
        self.kamera_results.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Pagination controls
        self.page_controls = ctk.CTkFrame(self.container, fg_color="transparent")
        self.page_controls.pack(fill="x", padx=15, pady=(0, 10))

        self.prev_page_btn = ctk.CTkButton(self.page_controls, text="◄ Назад", width=80, font=FONTS["small"], command=self._prev_page, **button_secondary_style())
        self.prev_page_btn.pack(side="left")

        self.page_lbl = ctk.CTkLabel(self.page_controls, text="Стр 0 / 0", font=FONTS["small_bold"])
        self.page_lbl.pack(side="left", padx=15)

        self.next_page_btn = ctk.CTkButton(self.page_controls, text="Вперёд ►", width=80, font=FONTS["small"], command=self._next_page, **button_secondary_style())
        self.next_page_btn.pack(side="left")

        self._scan_kamera_folder()

    def _scan_kamera_folder(self):
        root = get_project_root()
        kamera_dir = os.path.join(root, "kamera", "GenshinData")
        files = find_good_files(kamera_dir) if os.path.exists(kamera_dir) else []

        if not files:
            self.kamera_status_lbl.configure(text="Файлы сканирования не найдены в kamera/GenshinData", text_color=ThemeColors.YELLOW_WARN)
            self.scanned_artifacts = []
            self._update_kamera_table()
            return

        latest_file = files[0]
        data = load_kamera_json(latest_file)
        self.scanned_artifacts = extract_parsed_artifacts(data)
        self.kamera_status_lbl.configure(text=f"Загружен: {os.path.basename(latest_file)} ({len(self.scanned_artifacts)} арт.)", text_color=ThemeColors.GREEN)
        self.current_page = 0
        self._update_kamera_table()

    def _update_kamera_table(self):
        for w in self.kamera_results.winfo_children():
            w.destroy()

        total = len(self.scanned_artifacts)
        max_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page_lbl.configure(text=f"Стр {self.current_page + 1} / {max_pages} (Всего: {total})")

        start = self.current_page * self.page_size
        end = start + self.page_size
        slice_items = self.scanned_artifacts[start:end]

        if not slice_items:
            ctk.CTkLabel(self.kamera_results, text="Нет артефактов для отображения.", font=FONTS["body"]).pack(pady=20)
            return

        for art in slice_items:
            row = ctk.CTkFrame(self.kamera_results, **card_style())
            row.pack(fill="x", padx=5, pady=3)

            info = f"✦ {art.slot} | {art.main_stat} | +{art.level} | {art.set_name if hasattr(art, 'set_name') else ''}"
            ctk.CTkLabel(row, text=info, font=FONTS["small_bold"]).pack(side="left", padx=8, pady=4)

            btn = ctk.CTkButton(
                row,
                text="В калькулятор",
                width=100,
                height=24,
                font=FONTS["caption"],
                command=lambda a=art: self._transfer_artifact(a),
                **button_accent_cyan_style(),
            )
            btn.pack(side="right", padx=8, pady=4)

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_kamera_table()

    def _next_page(self):
        total = len(self.scanned_artifacts)
        if (self.current_page + 1) * self.page_size < total:
            self.current_page += 1
            self._update_kamera_table()

    # ─────────────────────────────────────────────────────────────────
    # GOOD JSON Tab
    # ─────────────────────────────────────────────────────────────────
    def _render_good_tab(self):
        top_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            top_frame,
            text="Импорт и экспорт в формате GOOD (Genshin Open Object Data).",
            font=FONTS["body"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        self.good_textbox = ctk.CTkTextbox(self.container, fg_color=ThemeColors.BG_INPUT, text_color=ThemeColors.TEXT_PRIMARY)
        self.good_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        btn_row = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))

        parse_btn = ctk.CTkButton(
            btn_row,
            text="Импортировать из поля ввода",
            command=self._parse_good_text,
            **button_primary_style(),
        )
        parse_btn.pack(side="left", padx=(0, 10))

        self.good_status_lbl = ctk.CTkLabel(btn_row, text="", font=FONTS["small"])
        self.good_status_lbl.pack(side="left")

    def _parse_good_text(self):
        text = self.good_textbox.get("1.0", "end").strip()
        if not text:
            return
        try:
            parsed_list = parse_good_json_string(text)
            if parsed_list:
                self.good_status_lbl.configure(text=f"✅ Найдено артефактов: {len(parsed_list)}", text_color=ThemeColors.GREEN)
                self._transfer_artifact(parsed_list[0])
            else:
                self.good_status_lbl.configure(text="❌ Артефакты не найдены в структуре GOOD", text_color=ThemeColors.RED)
        except Exception as e:
            self.good_status_lbl.configure(text=f"❌ Ошибка JSON: {e}", text_color=ThemeColors.RED)

    def _transfer_artifact(self, artifact: ParsedArtifact):
        if self.on_transfer_to_calculator:
            self.on_transfer_to_calculator(artifact)
