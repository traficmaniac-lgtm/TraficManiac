"""Application entrypoint for the CPA Grip AI suite GUI."""

import os
import sys
import tkinter as tk


if __package__ is None or __package__ == "":
    # Allow running the file directly (e.g., by double-clicking on Windows)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from cpagrip_ai_suite.ui.app import CPAOfferApp


def main() -> None:
    root = tk.Tk()
    root.title("CPA Offer Intelligence Suite v0.2")
    root.geometry("1100x800")
    app = CPAOfferApp(master=root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
