import tkinter as tk
from tkinter import ttk
from typing import Callable


class LabeledEntry(ttk.Frame):
    def __init__(self, master: tk.Widget, label: str, default: str = "", width: int = 18):
        super().__init__(master)
        self.label = ttk.Label(self, text=label)
        self.label.pack(side=tk.LEFT, padx=(0, 4))
        self.var = tk.StringVar(value=default)
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)


class LabeledSpinbox(ttk.Frame):
    def __init__(self, master: tk.Widget, label: str, from_: float, to: float, default: float, increment: float = 1.0, width: int = 6):
        super().__init__(master)
        ttk.Label(self, text=label).pack(side=tk.LEFT, padx=(0, 4))
        self.var = tk.DoubleVar(value=default)
        self.spin = ttk.Spinbox(self, from_=from_, to=to, increment=increment, textvariable=self.var, width=width)
        self.spin.pack(side=tk.LEFT)

    def get(self) -> float:
        return float(self.var.get())


class LabeledCheck(ttk.Frame):
    def __init__(self, master: tk.Widget, label: str, default: bool = False):
        super().__init__(master)
        self.var = tk.BooleanVar(value=default)
        check = ttk.Checkbutton(self, text=label, variable=self.var)
        check.pack(side=tk.LEFT)

    def get(self) -> bool:
        return bool(self.var.get())


class ActionButton(ttk.Button):
    def __init__(self, master: tk.Widget, text: str, command: Callable[[], None]):
        super().__init__(master, text=text, command=command)
