import tkinter as tk

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
