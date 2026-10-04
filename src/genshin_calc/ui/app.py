import customtkinter as ctk
from typing import Dict
from .components.sidebar import Sidebar

class GenshinCalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Genshin Artifact Calculator v2")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Grid layout: Sidebar on left, Main content on right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Views dictionary
        self.views: Dict[str, ctk.CTkFrame] = {}
        self.current_view_id = None
        
        self._build_ui()
        
    def _build_ui(self):
        # 1. Sidebar
        self.sidebar = Sidebar(self, on_nav_click=self.show_view, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Main content container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Initialize views (Placeholders for now)
        self._init_views()
        
        # Set default view
        self.sidebar.set_active("calculator")
        
    def _init_views(self):
        from .views.calculator_view import CalculatorView
        
        # Instantiate real calculator view
        self.views["calculator"] = CalculatorView(self.main_container)
        
        # Placeholder frames for others
        for view_id in ["scanner", "builds", "about"]:
            frame = ctk.CTkFrame(self.main_container)
            label = ctk.CTkLabel(frame, text=f"View: {view_id}", font=("Segoe UI", 24))
            label.pack(expand=True)
            self.views[view_id] = frame
            
    def show_view(self, view_id: str):
        if view_id not in self.views:
            return
            
        # Hide current view
        if self.current_view_id and self.current_view_id in self.views:
            self.views[self.current_view_id].grid_forget()
            
        # Show new view
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.current_view_id = view_id
