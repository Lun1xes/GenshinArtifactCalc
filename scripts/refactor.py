import re

with open('calculator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update minsize
if "self.minsize(" not in code:
    code = code.replace('self.geometry(f"1200x820+{x}+{y}")', 'self.geometry(f"1200x820+{x}+{y}")\n            self.minsize(1050, 700)')
    code = code.replace('self.geometry("1200x820")', 'self.geometry("1200x820")\n            self.minsize(1050, 700)')

# 2. Update view_calc columns
old_grid = '''        self.view_calc.grid_columnconfigure(0, weight=5)
        self.view_calc.grid_columnconfigure(1, weight=5)'''
new_grid = '''        self.view_calc.grid_columnconfigure(0, weight=0, minsize=460)
        self.view_calc.grid_columnconfigure(1, weight=1)'''
code = code.replace(old_grid, new_grid)

# 3. Modify left panel to be CTkScrollableFrame
code = code.replace('''    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=12)''', '''    def _build_left_panel(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=C.BG_DARK, corner_radius=12)''')

# Modify right panel to be CTkScrollableFrame
code = code.replace('''    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=12)''', '''    def _build_right_panel(self, parent):
        right = ctk.CTkScrollableFrame(parent, fg_color=C.BG_DARK, corner_radius=12)''')

# 4. Modify calculate and save buttons in left panel
old_calc_btn = '''        ctk.CTkButton(
            left,
            text="⚡  Рассчитать ценность и потенциал",
            font=("Segoe UI", 15, "bold"),
            fg_color=C.CYAN_DIM, hover_color=C.CYAN,
            text_color=C.BG_DEEP,
            height=46, corner_radius=10,
            command=self.calculate,
        ).pack(fill="x", padx=14, pady=(10, 14))'''
        
new_calc_btn = '''        # ─── Кнопки расчёта и сохранения ───
        btn_frame = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        btn_frame.pack(fill="x", padx=14, pady=(6, 10))
        
        self.calc_btn = ctk.CTkButton(
            btn_frame,
            text="⚡  Рассчитать",
            font=("Segoe UI", 14, "bold"),
            fg_color=C.CYAN_DIM, hover_color=C.CYAN,
            text_color=C.BG_DEEP,
            height=42, corner_radius=8,
            command=self.calculate,
        )
        self.calc_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.save_btn = ctk.CTkButton(
            btn_frame, text="💾  Сохранить",
            font=("Segoe UI", 14, "bold"),
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
            height=42, corner_radius=8,
            command=self.save_to_history, state="disabled",
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))'''

if "self.save_btn = ctk.CTkButton" in old_calc_btn or "btn_frame" not in code:
    code = code.replace(old_calc_btn, new_calc_btn)

# Remove old save_btn from right panel
old_act1 = '''        self.save_btn = ctk.CTkButton(
            act1, text="💾  Сохранить", width=120,
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
            command=self.save_to_history, state="disabled",
        )
        self.save_btn.pack(side="left", padx=(0, 4))'''
code = code.replace(old_act1, '')

# Adjust char menu widths
code = code.replace('width=220,', 'width=180,')

# Reduce paddings globally for better compact view
code = re.sub(r'pady=\(\d+,\s*14\)', 'pady=(2, 6)', code)
code = re.sub(r'pady=\(\d+,\s*12\)', 'pady=(2, 6)', code)
code = re.sub(r'pady=\(\d+,\s*10\)', 'pady=(2, 4)', code)
code = re.sub(r'pady=\(\d+,\s*8\)', 'pady=(2, 4)', code)
code = re.sub(r'pady=\(\d+,\s*6\)', 'pady=(2, 4)', code)

with open('calculator.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Refactoring done.")
