from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List

from ..core.cpagrip_client import CPAGripClient
from ..core.offer_model import OfferNormalized
from ..core.offer_model import normalize_offers
from ..prompts.strategy_packet import build_strategy_packet
from ..utils.config import DEFAULT_SETTINGS
from .widgets import LabeledEntry, LabeledSpinbox


class CPAOfferApp(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.client = CPAGripClient()
        self.offers: List[OfferNormalized] = []
        self.filtered: List[OfferNormalized] = []
        self.strategy_json = ""
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.param_frame = ttk.LabelFrame(self, text="Параметры фида")
        self.param_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        self._build_params(self.param_frame)

        self.filter_frame = ttk.LabelFrame(self, text="Фильтр и ТОП-50")
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
        self.private_key = LabeledEntry(top_row, "private key", defaults["private_key"], width=36)
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
        ttk.Button(btn_row, text="Загрузить офферы", command=self.load_offers).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Экспорт всех офферов (JSON)", command=self.export_offers).pack(side=tk.LEFT, padx=4)

    def _build_filters(self, frame: ttk.LabelFrame) -> None:
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        self.search_entry = LabeledEntry(row1, "поиск", "", width=30)
        self.search_entry.pack(side=tk.LEFT, padx=4)
        ttk.Button(frame, text="Показать ТОП-50", command=self.apply_filters).pack(pady=2, padx=4, anchor="w")

    def _build_offer_list(self, parent: ttk.Frame) -> None:
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = ("rank", "offer_id", "title", "geo", "payout", "conversion", "score", "risk")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=25)
        self.tree.heading("rank", text="#")
        self.tree.heading("offer_id", text="ID")
        self.tree.heading("title", text="Оффер")
        self.tree.heading("geo", text="GEO")
        self.tree.heading("payout", text="Payout")
        self.tree.heading("conversion", text="Конверсия")
        self.tree.heading("score", text="Score")
        self.tree.heading("risk", text="Риск")
        self.tree.column("rank", width=40, anchor=tk.CENTER)
        self.tree.column("offer_id", width=70, anchor=tk.CENTER)
        self.tree.column("title", width=320)
        self.tree.column("geo", width=100, anchor=tk.CENTER)
        self.tree.column("payout", width=80, anchor=tk.CENTER)
        self.tree.column("conversion", width=120, anchor=tk.CENTER)
        self.tree.column("score", width=90, anchor=tk.CENTER)
        self.tree.column("risk", width=60, anchor=tk.CENTER)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_offer)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        detail_frame = ttk.Frame(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.rowconfigure(1, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(detail_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(btn_frame, text="AI Strategy Packet (PropellerAds)").pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Скопировать JSON", command=self.copy_strategy_json).pack(side=tk.LEFT, padx=4)

        self.detail_text = tk.Text(detail_frame, wrap="word")
        self.detail_text.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

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
            raw_offers = self.client.fetch_raw_offers(**params)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ошибка загрузки", str(exc))
            return

        normalization = normalize_offers(raw_offers, tracking_macro=params.get("tracking_id") or "${SUBID}")
        if normalization.errors:
            messagebox.showwarning("Нормализация", "\n".join(normalization.errors))
        self.offers = normalization.offers
        self.apply_filters()

    def apply_filters(self) -> None:
        query = self.search_entry.get().strip().lower()
        offers = self.offers
        if query:
            offers = [
                o
                for o in offers
                if query in o.name.lower() or (o.description or "").lower().find(query) >= 0
            ]
        self.filtered = offers[:50]
        self._refresh_tree()
        if self.filtered:
            self.tree.selection_set("0")
            self.on_select_offer(None)

    def _refresh_tree(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for idx, offer in enumerate(self.filtered):
            geo_display = ",".join(offer.geo_allowed[:3])
            if len(offer.geo_allowed) > 3:
                geo_display += "+"
            self.tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    idx + 1,
                    offer.offer_id,
                    offer.name,
                    geo_display,
                    f"{offer.payout_usd:.2f}",
                    offer.conversion_type or "?",
                    f"{offer.score:.3f}",
                    "⚠" if offer.risk_flag else "OK",
                ),
            )

    def on_select_offer(self, event: tk.Event | None) -> None:  # type: ignore[override]
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self.filtered):
            return
        offer = self.filtered[idx]
        self._display_offer_packet(offer)

    def _display_offer_packet(self, offer: OfferNormalized) -> None:
        packet = build_strategy_packet(offer)
        self.strategy_json = packet
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, packet)

    def export_offers(self) -> None:
        if not self.offers:
            messagebox.showinfo("Экспорт", "Сначала загрузите офферы")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fp:
            json.dump([offer.to_dict() for offer in self.offers], fp, indent=2, ensure_ascii=False)
        messagebox.showinfo("Экспорт", f"Сохранено: {path}")

    def copy_strategy_json(self) -> None:
        if not self.strategy_json:
            messagebox.showinfo("Буфер", "Нет данных для копирования")
            return
        self.clipboard_clear()
        self.clipboard_append(self.strategy_json)
        messagebox.showinfo("Буфер", "AI Strategy Packet скопирован")
