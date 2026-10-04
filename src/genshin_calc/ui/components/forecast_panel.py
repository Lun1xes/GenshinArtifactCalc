import customtkinter as ctk

class ForecastPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()
        
    def _build_ui(self):
        # Placeholder for Step 4 forecast
        ctk.CTkLabel(self, text="Forecast Panel Component").pack(expand=True)
