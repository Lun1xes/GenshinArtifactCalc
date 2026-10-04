import customtkinter as ctk
from typing import Callable, List, Tuple

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_nav_click: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.on_nav_click = on_nav_click
        self.buttons: List[ctk.CTkButton] = []
        
        # Build UI
        self._build_sidebar()
        
    def _build_sidebar(self):
        # App Title / Logo Area
        self.logo_label = ctk.CTkLabel(
            self, 
            text="GenshinArtifactCalc", 
            font=("Segoe UI", 16, "bold")
        )
        self.logo_label.pack(padx=20, pady=(20, 30))
        
        # Navigation Buttons
        nav_items: List[Tuple[str, str]] = [
            ("calculator", "≡ Калькулятор"),
            ("scanner", "≡ Импорт / Скан"),
            ("builds", "≡ Билды героев"),
            ("about", "≡ О программе")
        ]
        
        for view_id, label in nav_items:
            btn = ctk.CTkButton(
                self,
                text=label,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=lambda vid=view_id: self._handle_nav(vid)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.buttons.append((view_id, btn))
            
    def _handle_nav(self, view_id: str):
        # Highlight active button
        for vid, btn in self.buttons:
            if vid == view_id:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
                
        # Trigger callback
        self.on_nav_click(view_id)

    def set_active(self, view_id: str):
        self._handle_nav(view_id)
