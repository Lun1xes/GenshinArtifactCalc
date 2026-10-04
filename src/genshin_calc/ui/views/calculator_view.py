import customtkinter as ctk
from ..components.stat_inputs import StatInputs
from ..components.forecast_panel import ForecastPanel

class CalculatorView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_ui()
        
    def _build_ui(self):
        self.forecast_panel = ForecastPanel(self)
        self.stat_inputs = StatInputs(self, on_artifact_changed=self._on_artifact_changed)
        
        self.stat_inputs.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.forecast_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
    def _on_artifact_changed(self, artifact_data: dict):
        self.forecast_panel.update_forecast(artifact_data)
