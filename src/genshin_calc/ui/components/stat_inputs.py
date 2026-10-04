import customtkinter as ctk

class StatInputs(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()
        
    def _build_ui(self):
        # Placeholder for Step 1-3 inputs
        ctk.CTkLabel(self, text="Stat Inputs Component").pack(expand=True)
