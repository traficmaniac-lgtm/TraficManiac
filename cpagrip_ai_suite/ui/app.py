import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List

from ..core.cpagrip_client import CPAGripClient
from ..core.filters import filter_offers
from ..core.offer_model import OfferNormalized, normalize_offers
from ..prompts.ai_prompts import build_ai_selection_prompt
from ..prompts.propeller_prompt import build_propeller_campaign_prompt
from ..utils.config import DEFAULT_SETTINGS
from .widgets import LabeledCheck, LabeledEntry, LabeledSpinbox


class CPAOfferApp(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.client = CPAGripClient()
        self.offers: List[OfferNormalized] = []
        self.filtered: List[OfferNormalized] = []
        self.ai_prompt_text = ""
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.param_frame = ttk.LabelFrame(self, text="Feed Parameters")
        self.param_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        self._build_params(self.param_frame)

        self.filter_frame = ttk.LabelFrame(self, text="Filters")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        self._build_filters(self.filter_frame)

        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=6)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        self._build_offer_list(self.content_frame)
        self._build_detail_panel(self.content_frame)

    def _build_params(self, frame: ttk.LabelFrame) -> None:
        defaults = DEFAULT_SETTINGS
        top_row = ttk.Frame(frame)
        top_row.pack(fill=tk.X, pady=2)
        self.user_id = LabeledEntry(top_row, "user_id", defaults["user_id"])
        self.user_id.pack(side=tk.LEFT, padx=4)
        self.private_key = LabeledEntry(top_row, "private key", defaults["private_key"])
        self.private_key.pack(side=tk.LEFT, padx=4)
        self.tracking_id = LabeledEntry(top_row, "tracking", defaults["tracking_id"])
        self.tracking_id.pack(side=tk.LEFT, padx=4)

        second_row = ttk.Frame(frame)
        second_row.pack(fill=tk.X, pady=2)
        self.limit = LabeledSpinbox(second_row, "limit", 1, 500, defaults["limit"], increment=10)
        self.limit.pack(side=tk.LEFT, padx=4)
        self.showall = LabeledSpinbox(second_row, "showall", 0, 1, defaults["showall"], increment=1)
        self.showall.pack(side=tk.LEFT, padx=4)
        self.showmobile = LabeledSpinbox(second_row, "showmobile", 0, 1, defaults["showmobile"], increment=1)
        self.showmobile.pack(side=tk.LEFT, padx=4)
        self.country = LabeledEntry(second_row, "country", defaults["country"])
        self.country.pack(side=tk.LEFT, padx=4)
        self.offer_type = LabeledEntry(second_row, "offer_type", defaults["offer_type"])
        self.offer_type.pack(side=tk.LEFT, padx=4)
        self.domain = LabeledEntry(second_row, "domain", defaults["domain"])
        self.domain.pack(side=tk.LEFT, padx=4)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row, text="Load Offers", command=self.load_offers).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Export Offers JSON", command=self.export_offers).pack(side=tk.LEFT, padx=4)

    def _build_filters(self, frame: ttk.LabelFrame) -> None:
        defaults = DEFAULT_SETTINGS
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        self.search_entry = LabeledEntry(row1, "search", "", width=20)
        self.search_entry.pack(side=tk.LEFT, padx=4)
        self.include_geo = LabeledEntry(row1, "GEO include", "")
        self.include_geo.pack(side=tk.LEFT, padx=4)
        self.exclude_geo = LabeledEntry(row1, "GEO exclude", "")
        self.exclude_geo.pack(side=tk.LEFT, padx=4)
        self.kind_var = tk.StringVar(value="any")
        ttk.Label(row1, text="kind").pack(side=tk.LEFT, padx=(8, 4))
        ttk.Combobox(row1, textvariable=self.kind_var, values=["any", "SOI", "DOI", "SURVEY", "INSTALL", "PIN", "CC", "UNKNOWN"], width=10).pack(side=tk.LEFT)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)
        self.max_complexity = LabeledSpinbox(row2, "max complexity", 1, 5, defaults["max_complexity"], increment=1)
        self.max_complexity.pack(side=tk.LEFT, padx=4)
        self.payout_min = LabeledEntry(row2, "payout min", "")
        self.payout_min.pack(side=tk.LEFT, padx=4)
        self.payout_max = LabeledEntry(row2, "payout max", "")
        self.payout_max.pack(side=tk.LEFT, padx=4)
        self.hide_risk = LabeledCheck(row2, "hide risk", False)
        self.hide_risk.pack(side=tk.LEFT, padx=4)
        ttk.Label(row2, text="tier").pack(side=tk.LEFT, padx=(8, 4))
        self.tier_var = tk.StringVar(value="any")
        ttk.Combobox(row2, textvariable=self.tier_var, values=["any", "tier1", "tier2", "tier3", "mixed"], width=10).pack(side=tk.LEFT)
        ttk.Label(row2, text="sort").pack(side=tk.LEFT, padx=(8, 4))
        self.sort_var = tk.StringVar(value=defaults["sort_by"])
        ttk.Combobox(row2, textvariable=self.sort_var, values=["profit_score", "payout", "complexity"], width=12).pack(side=tk.LEFT)

        ttk.Button(frame, text="Apply Filters", command=self.apply_filters).pack(pady=2, padx=4, anchor="w")

    def _build_offer_list(self, parent: ttk.Frame) -> None:
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = ("title", "payout", "kind", "tier", "score")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=25)
        self.tree.heading("title", text="Title")
        self.tree.heading("payout", text="Payout")
        self.tree.heading("kind", text="Kind")
        self.tree.heading("tier", text="Geo Tier")
        self.tree.heading("score", text="Profit Score")
        self.tree.column("title", width=320)
        self.tree.column("payout", width=70, anchor=tk.CENTER)
        self.tree.column("kind", width=80, anchor=tk.CENTER)
        self.tree.column("tier", width=70, anchor=tk.CENTER)
        self.tree.column("score", width=90, anchor=tk.CENTER)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_offer)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        detail_frame = ttk.Frame(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.rowconfigure(2, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(detail_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        self.ai_budget = LabeledSpinbox(btn_frame, "AI budget", 0, 10000, 200, increment=50)
        self.ai_budget.pack(side=tk.LEFT, padx=4)
        self.ai_top_n = LabeledSpinbox(btn_frame, "TopN", 1, 100, DEFAULT_SETTINGS["ai_top_n"], increment=5)
        self.ai_top_n.pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="AI Selection Prompt", command=self.generate_ai_prompt).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Propeller Prompt", command=self.generate_propeller_prompt).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Export AI Prompt", command=self.export_ai_prompt).pack(side=tk.LEFT, padx=4)

        self.detail_text = tk.Text(detail_frame, wrap="word")
        self.detail_text.grid(row=2, column=0, sticky="nsew", pady=(6, 0))

    def load_offers(self) -> None:
        params = {
            "user_id": self.user_id.get(),
            "key": self.private_key.get(),
            "tracking_id": self.tracking_id.get(),
            "limit": int(self.limit.get()),
            "showall": int(self.showall.get()),
            "country": self.country.get(),
            "offer_type": self.offer_type.get(),
            "domain": self.domain.get(),
            "showmobile": int(self.showmobile.get()),
        }
        try:
            raw_offers = self.client.fetch_offers_list(**params)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load error", str(exc))
            return

        normalization = normalize_offers(raw_offers)
        if normalization.errors:
            messagebox.showwarning("Normalization", "\n".join(normalization.errors))
        self.offers = normalization.offers
        self.apply_filters()

    def apply_filters(self) -> None:
        try:
            payout_min = float(self.payout_min.get()) if self.payout_min.get() else None
            payout_max = float(self.payout_max.get()) if self.payout_max.get() else None
        except ValueError:
            messagebox.showerror("Filters", "Invalid payout value")
            return

        filtered = filter_offers(
            self.offers,
            search=self.search_entry.get(),
            include_geo=self._parse_geo(self.include_geo.get()),
            exclude_geo=self._parse_geo(self.exclude_geo.get()),
            kind=self.kind_var.get(),
            max_complexity=int(self.max_complexity.get()),
            payout_min=payout_min,
            payout_max=payout_max,
            hide_risk=self.hide_risk.get(),
            tier_only=self.tier_var.get(),
            sort_by=self.sort_var.get(),
        )
        self.filtered = filtered
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for idx, offer in enumerate(self.filtered):
            self.tree.insert(
                "", tk.END, iid=str(idx), values=(
                    offer.title,
                    f"{offer.payout:.2f}",
                    offer.kind,
                    offer.geo_tier,
                    f"{offer.profit_score:.3f}",
                )
            )

    def on_select_offer(self, event: tk.Event) -> None:  # type: ignore[override]
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self.filtered):
            return
        offer = self.filtered[idx]
        self._display_offer_details(offer)

    def _display_offer_details(self, offer: OfferNormalized) -> None:
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, json.dumps(offer.to_dict(), indent=2))

    def generate_ai_prompt(self) -> None:
        if not self.filtered:
            messagebox.showinfo("AI prompt", "No offers to include")
            return
        top_n = int(self.ai_top_n.get())
        cards = self.filtered[:top_n]
        prompt = build_ai_selection_prompt(cards, budget=float(self.ai_budget.get()))
        self.ai_prompt_text = prompt
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, prompt)

    def generate_propeller_prompt(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Propeller prompt", "Select an offer first")
            return
        idx = int(selection[0])
        if idx >= len(self.filtered):
            return
        offer = self.filtered[idx]
        prompt = build_propeller_campaign_prompt(offer, test_budget=float(self.ai_budget.get()))
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, prompt)

    def export_offers(self) -> None:
        if not self.offers:
            messagebox.showinfo("Export", "No offers to export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fp:
            json.dump([offer.to_dict() for offer in self.offers], fp, indent=2)
        messagebox.showinfo("Export", f"Saved offers to {path}")

    def export_ai_prompt(self) -> None:
        if not self.ai_prompt_text:
            messagebox.showinfo("Export", "Generate AI prompt first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(self.ai_prompt_text)
        messagebox.showinfo("Export", f"Saved prompt to {path}")

    def _parse_geo(self, value: str) -> List[str]:
        return [v.strip().upper() for v in value.split(",") if v.strip()]
