"""
折りたたみ可能なフレームウィジェット
"""
import tkinter as tk
from tkinter import ttk
class CollapsibleFrame(ttk.Frame):
    """折りたたみ可能なフレーム"""
    def __init__(self, parent, text="", style="Modern.TFrame", **kwargs):
        super().__init__(parent, style=style, **kwargs)
        self.is_expanded = tk.BooleanVar(value=False)
        self.toggle_button = ttk.Button(
            self, 
            text=f"▶ {text}",
            command=self.toggle,
            style="Modern.TButton"
        )
        self.toggle_button.pack(fill=tk.X, pady=(0, 5))
        self.content_frame = ttk.Frame(self, style=style)
        self.text = text
    def toggle(self):
        """折りたたみ/展開を切り替え"""
        if self.is_expanded.get():
            self.content_frame.pack_forget()
            self.toggle_button.config(text=f"▶ {self.text}")
            self.is_expanded.set(False)
        else:
            self.content_frame.pack(fill=tk.BOTH, expand=True)
            self.toggle_button.config(text=f"▼ {self.text}")
            self.is_expanded.set(True)
    def get_content_frame(self):
        """コンテンツフレームを取得"""
        return self.content_frame
