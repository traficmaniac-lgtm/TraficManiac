from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from ..core.cpagrip_client import CPAGripClient
from ..core.offer_model import OfferNormalized, normalize_offers
from ..prompts.strategy_packet import build_strategy_packet
from ..utils.config import DEFAULT_SETTINGS, load_app_config, save_app_config
from .bindings_strategy import StrategyBindings
from .widgets import LabeledEntry, LabeledSpinbox


class CPAOfferApp(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.client = CPAGripClient()
        self.offers: List[OfferNormalized] = []
        self.filtered: List[OfferNormalized] = []
        self.displayed: List[OfferNormalized] = []
        self.strategy_json = ""
        self.current_offer: Optional[OfferNormalized] = None
        self.force_regen_var = tk.BooleanVar(value=False)
        self.strategy_status_var = tk.StringVar(value="-")
        self.sort_column: str | None = None
        self.sort_reverse = False

        self.user_config = load_app_config()
        self.top_n_var = tk.IntVar(value=int(DEFAULT_SETTINGS.get("ai_top_n", 50)))
        self.risk_filter_var = tk.StringVar(value="all")
        self.min_payout_var = tk.DoubleVar(value=0.0)
        self.auto_sort_var = tk.BooleanVar(value=True)
        self.offer_count_var = tk.StringVar(value="0 / 0")

        self.api_key_var = tk.StringVar(value=self.user_config.get("OPENAI_API_KEY", ""))
        self.api_model_var = tk.StringVar(value=self.user_config.get("OPENAI_MODEL", "gpt-4.1"))
        self.api_temperature_var = tk.DoubleVar(value=float(self.user_config.get("OPENAI_TEMPERATURE", 0.2)))
        self.api_temperature_label = tk.StringVar(value=f"{self.api_temperature_var.get():.2f}")
        self.api_key_visible = tk.BooleanVar(value=False)
        self.openai_status_var = tk.StringVar(value="config.json")

        self.style = ttk.Style()
        self._configure_style()

        self._build_ui()
        self.strategy_bindings = StrategyBindings(self)

    def _configure_style(self) -> None:
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Card.TLabelframe", padding=10, borderwidth=2)
        self.style.configure("Accent.TButton", padding=6)
        self.style.configure("Inline.TLabel", font=("TkDefaultFont", 10, "bold"))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)

        self.param_frame = ttk.LabelFrame(self, text="Параметры фида", style="Card.TLabelframe")
        self.param_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=6)
        self._build_params(self.param_frame)

        self.openai_frame = ttk.LabelFrame(self, text="Настройки OpenAI API", style="Card.TLabelframe")
        self.openai_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=6)
        self._build_openai_settings(self.openai_frame)

        self.filter_frame = ttk.LabelFrame(self, text="Фильтры и подбор", style="Card.TLabelframe")
        self.filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
        self._build_filters(self.filter_frame)

        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=6)
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
        ttk.Button(btn_row, text="Экспорт всех офферов (JSON)", command=self.export_offers).pack(
            side=tk.LEFT, padx=4
        )

    def _build_openai_settings(self, frame: ttk.LabelFrame) -> None:
        ttk.Label(frame, text="API ключ и модель", style="Inline.TLabel").pack(anchor="w")

        key_row = ttk.Frame(frame)
        key_row.pack(fill=tk.X, pady=2)
        ttk.Label(key_row, text="OPENAI_API_KEY").pack(side=tk.LEFT, padx=(0, 4))
        self.api_key_entry = ttk.Entry(key_row, textvariable=self.api_key_var, width=34, show="•")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Checkbutton(
            key_row, text="показать", variable=self.api_key_visible, command=self._toggle_api_visibility
        ).pack(side=tk.LEFT, padx=4)

        model_row = ttk.Frame(frame)
        model_row.pack(fill=tk.X, pady=2)
        ttk.Label(model_row, text="Модель").pack(side=tk.LEFT, padx=(0, 4))
        models = ("gpt-4.1", "gpt-4o-mini", "o3-mini")
        ttk.Combobox(model_row, values=models, textvariable=self.api_model_var, state="readonly", width=18).pack(
            side=tk.LEFT, padx=4
        )

        temp_row = ttk.Frame(frame)
        temp_row.pack(fill=tk.X, pady=4)
        ttk.Label(temp_row, text="Температура").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Scale(
            temp_row,
            from_=0.0,
            to=1.0,
            variable=self.api_temperature_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.api_temperature_label.set(f"{float(v):.2f}"),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(temp_row, textvariable=self.api_temperature_label, width=6).pack(side=tk.LEFT, padx=4)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="Сохранить", style="Accent.TButton", command=self.save_openai_settings).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Проверить", command=self.test_openai_settings).pack(side=tk.LEFT, padx=4)
        ttk.Label(btn_row, textvariable=self.openai_status_var, foreground="#3f6b39").pack(side=tk.LEFT, padx=6)

        ttk.Label(frame, text="Данные сохраняются в config.json", foreground="#6c6c6c").pack(
            anchor="w", pady=(0, 4)
        )

    def _build_filters(self, frame: ttk.LabelFrame) -> None:
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        self.search_entry = LabeledEntry(row1, "поиск", "", width=30)
        self.search_entry.pack(side=tk.LEFT, padx=4)
        ttk.Label(row1, text="Риск").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Combobox(
            row1,
            values=("all", "low", "medium", "high"),
            textvariable=self.risk_filter_var,
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Мин. payout").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Spinbox(row2, from_=0.0, to=200.0, increment=0.5, textvariable=self.min_payout_var, width=8).pack(
            side=tk.LEFT
        )
        ttk.Label(row2, text="ТОП N").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Spinbox(row2, from_=5, to=200, increment=5, textvariable=self.top_n_var, width=6).pack(side=tk.LEFT)
        ttk.Checkbutton(row2, text="Авто-сортировка по Score", variable=self.auto_sort_var).pack(
            side=tk.LEFT, padx=(12, 4)
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="Применить фильтр", command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="Автоподбор топовых", style="Accent.TButton", command=self.auto_pick_top).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btn_row, text="Сброс", command=self.reset_filters).pack(side=tk.LEFT, padx=6)
        ttk.Label(btn_row, textvariable=self.offer_count_var, foreground="#4b5563").pack(side=tk.RIGHT)

    def _build_offer_list(self, parent: ttk.Frame) -> None:
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = (
            "rank",
            "offer_id",
            "title",
            "geo",
            "payout",
            "conversion",
            "lp_type",
            "traffic_fit",
            "score",
            "risk",
        )
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=25)
        self.tree.heading("rank", text="#", command=lambda: self.sort_by("rank"))
        self.tree.heading("offer_id", text="ID", command=lambda: self.sort_by("offer_id"))
        self.tree.heading("title", text="Оффер", command=lambda: self.sort_by("title"))
        self.tree.heading("geo", text="GEO", command=lambda: self.sort_by("geo"))
        self.tree.heading("payout", text="Payout", command=lambda: self.sort_by("payout"))
        self.tree.heading("conversion", text="Conv.Type", command=lambda: self.sort_by("conversion"))
        self.tree.heading("lp_type", text="LP type", command=lambda: self.sort_by("lp_type"))
        self.tree.heading("traffic_fit", text="Traffic fit", command=lambda: self.sort_by("traffic_fit"))
        self.tree.heading("score", text="Score", command=lambda: self.sort_by("score"))
        self.tree.heading("risk", text="Риск", command=lambda: self.sort_by("risk"))
        self.tree.column("rank", width=40, anchor=tk.CENTER)
        self.tree.column("offer_id", width=70, anchor=tk.CENTER)
        self.tree.column("title", width=280)
        self.tree.column("geo", width=100, anchor=tk.CENTER)
        self.tree.column("payout", width=80, anchor=tk.CENTER)
        self.tree.column("conversion", width=100, anchor=tk.CENTER)
        self.tree.column("lp_type", width=100, anchor=tk.CENTER)
        self.tree.column("traffic_fit", width=110, anchor=tk.CENTER)
        self.tree.column("score", width=90, anchor=tk.CENTER)
        self.tree.column("risk", width=70, anchor=tk.CENTER)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_offer)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.tag_configure("risk_low", background="#e6ffe6")
        self.tree.tag_configure("risk_medium", background="#fff9e6")
        self.tree.tag_configure("risk_high", background="#ffe6e6")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        detail_frame = ttk.Frame(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.rowconfigure(1, weight=1)
        detail_frame.rowconfigure(2, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(detail_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        ttk.Button(btn_frame, text="Generate Strategy", command=self.generate_strategy).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(btn_frame, text="Regenerate", variable=self.force_regen_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(btn_frame, textvariable=self.strategy_status_var).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Copy Propeller JSON", command=self.copy_propeller_json).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="Apply to Form", command=self.apply_to_form).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Export Preset", command=self.export_preset).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Скопировать JSON", command=self.copy_strategy_json).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Export Campaign Preset", command=self.export_campaign_preset).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="Auto Strategy", command=self.auto_strategy).pack(side=tk.LEFT, padx=4)

        form_frame = ttk.LabelFrame(detail_frame, text="Быстрая форма")
        form_frame.grid(row=1, column=0, sticky="ew", pady=4)
        self.form_format = LabeledEntry(form_frame, "format", "", width=14)
        self.form_format.pack(side=tk.LEFT, padx=4)
        self.form_geo = LabeledEntry(form_frame, "GEO", "", width=20)
        self.form_geo.pack(side=tk.LEFT, padx=4)
        self.form_bid = LabeledEntry(form_frame, "bid", "", width=10)
        self.form_bid.pack(side=tk.LEFT, padx=4)
        self.form_budget = LabeledEntry(form_frame, "daily budget", "", width=12)
        self.form_budget.pack(side=tk.LEFT, padx=4)

        self.detail_text = tk.Text(detail_frame, wrap="word")
        self.detail_text.grid(row=2, column=0, sticky="nsew", pady=(6, 6))

        self.tabs = ttk.Notebook(detail_frame)
        self.tabs.grid(row=3, column=0, sticky="nsew")
        self.tabs.rowconfigure(0, weight=1)
        self.tabs.columnconfigure(0, weight=1)
        self.packet_text = tk.Text(self.tabs, wrap="word")
        self.propeller_text = tk.Text(self.tabs, wrap="word")
        self.debug_text = tk.Text(self.tabs, wrap="word")
        self.tabs.add(self.packet_text, text="AI Strategy Packet")
        self.tabs.add(self.propeller_text, text="Propeller Settings (JSON)")
        self.tabs.add(self.debug_text, text="Debug")

        simulator = ttk.LabelFrame(detail_frame, text="Campaign Simulator")
        simulator.grid(row=4, column=0, sticky="ew", pady=(4, 0))

        self.budget_var = tk.StringVar(value="30")
        self.cpc_var = tk.StringVar(value="0.02")
        self.cr_var = tk.StringVar(value="0.8")
        self.expected_clicks_var = tk.StringVar(value="1500")
        self.expected_leads_var = tk.StringVar(value="12")
        self.revenue_var = tk.StringVar(value="36.9")
        self.net_var = tk.StringVar(value="6.9")

        grid_items = [
            ("Budget $", self.budget_var),
            ("CPC $", self.cpc_var),
            ("CR %", self.cr_var),
            ("Clicks", self.expected_clicks_var),
            ("Leads", self.expected_leads_var),
            ("Revenue $", self.revenue_var),
            ("Net $", self.net_var),
        ]

        for idx, (label, var) in enumerate(grid_items):
            ttk.Label(simulator, text=label).grid(row=idx // 2, column=(idx % 2) * 2, padx=4, pady=2, sticky="e")
            ttk.Entry(simulator, textvariable=var, width=12).grid(
                row=idx // 2, column=(idx % 2) * 2 + 1, padx=4, pady=2, sticky="w"
            )

        ttk.Button(simulator, text="Simulate", command=self._recalc_simulator).grid(
            row=4, column=0, columnspan=4, pady=4
        )

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
        self.reset_filters()

    def apply_filters(self) -> None:
        query = self.search_entry.get().strip().lower()
        offers = list(self.offers)
        if query:
            offers = [
                o
                for o in offers
                if query in o.name.lower() or (o.description or "").lower().find(query) >= 0
            ]
        risk = (self.risk_filter_var.get() or "all").lower()
        if risk != "all":
            offers = [o for o in offers if o.risk_level.lower() == risk]
        try:
            min_payout = float(self.min_payout_var.get())
        except (TypeError, ValueError):
            min_payout = 0.0
        if min_payout > 0:
            offers = [o for o in offers if o.payout_usd >= min_payout]
        if self.auto_sort_var.get():
            offers.sort(key=lambda o: o.score, reverse=True)
        self.filtered = offers
        self._refresh_tree()
        if self.filtered:
            self.tree.selection_set("0")
            self.on_select_offer(None)

    def auto_pick_top(self) -> None:
        if not self.offers:
            messagebox.showinfo("ТОП", "Сначала загрузите офферы")
            return
        try:
            top_n = max(1, int(self.top_n_var.get()))
        except (TypeError, ValueError):
            top_n = 50
        ranked = sorted(self.offers, key=lambda o: o.score, reverse=True)[:top_n]
        self.filtered = ranked
        self._refresh_tree()
        if self.filtered:
            self.tree.selection_set("0")
            self.on_select_offer(None)

    def reset_filters(self) -> None:
        self.search_entry.set("")
        self.risk_filter_var.set("all")
        self.min_payout_var.set(0.0)
        self.auto_sort_var.set(True)
        self.filtered = list(self.offers)
        self._refresh_tree()
        if self.filtered:
            self.tree.selection_set("0")
            self.on_select_offer(None)

    def _refresh_tree(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        offers = list(self.filtered)
        if self.sort_column and self.sort_column != "rank":
            offers.sort(key=self._sort_key, reverse=self.sort_reverse)
        self.displayed = offers
        self.offer_count_var.set(f"{len(offers)} / {len(self.offers)}")

        for idx, offer in enumerate(offers):
            geo_display = ",".join(offer.geo_allowed[:3])
            if len(offer.geo_allowed) > 3:
                geo_display += "+"
            risk_tag = f"risk_{offer.risk_level}"
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
                    offer.lp_type_guess or "?",
                    offer.traffic_fit,
                    f"{offer.score:.3f}",
                    offer.risk_level.upper(),
                ),
                tags=(risk_tag,),
            )

    def _sort_key(self, offer: OfferNormalized):
        mapping = {
            "offer_id": offer.offer_id,
            "title": offer.name,
            "geo": ",".join(offer.geo_allowed),
            "payout": offer.payout_usd,
            "conversion": offer.conversion_type or "",
            "lp_type": offer.lp_type_guess or "",
            "traffic_fit": offer.traffic_fit,
            "score": offer.score,
            "risk": offer.risk_level,
        }
        return mapping.get(self.sort_column or "score", offer.score)

    def sort_by(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = column
        self._refresh_tree()

    def on_select_offer(self, event: tk.Event | None) -> None:  # type: ignore[override]
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self.displayed):
            return
        offer = self.displayed[idx]
        self.current_offer = offer
        self._display_offer_packet(offer)

    def _display_offer_packet(self, offer: OfferNormalized) -> None:
        packet = build_strategy_packet(offer)
        self.strategy_json = packet
        self.set_packet_text(packet)

        self.detail_text.delete("1.0", tk.END)
        header = [
            f"Decision Score: {offer.score:.2f} ({offer.risk_level.upper()} risk)",
            f"Reason: {offer.risk_reason}",
            "Score breakdown:",
        ]
        for item in offer.score_breakdown:
            label = item.get("label", "")
            value = item.get("value", 0.0)
            sign = "+" if value >= 0 else "-"
            header.append(f"  {sign} {label}: {abs(value):.2f}")
        header.append("")
        self.detail_text.insert(tk.END, "\n".join(header))
        self.detail_text.insert(tk.END, "\n\n")
        self.detail_text.insert(tk.END, packet)
        self._recalc_simulator(offer)

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

    def generate_strategy_text(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Стратегия", "Выберите оффер")
            return
        idx = int(selection[0])
        if idx >= len(self.displayed):
            return
        offer = self.displayed[idx]
        lines = [
            f"Auto summary for {offer.name} (ID {offer.offer_id})",
            f"Traffic fit: {offer.traffic_fit} | LP: {offer.lp_type_guess or 'direct link'}",
            f"Risk: {offer.risk_level.upper()} ({offer.risk_reason})",
            f"Start with {offer.score_breakdown[0]['value'] if offer.score_breakdown else offer.score:.2f} score weight",
            "Suggested actions:",
            "- Launch test on PropellerAds with inpage/push split 70/30",
            "- Bid inside expected CPC range, cap zones after 1.5x breakeven clicks",
            "- Pause low CTR zones, duplicate winners with +20% bid",
        ]
        messagebox.showinfo("Generate Strategy", "\n".join(lines))

    def export_campaign_preset(self) -> None:
        if not self.strategy_json:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(self.strategy_json)
        messagebox.showinfo("Экспорт", f"Профиль кампании сохранен: {path}")

    def set_packet_text(self, packet: str) -> None:
        self.packet_text.delete("1.0", tk.END)
        self.packet_text.insert(tk.END, packet)

    def set_propeller_json(self, payload: dict | None) -> None:
        self.propeller_text.delete("1.0", tk.END)
        if payload:
            self.propeller_text.insert(tk.END, json.dumps(payload, ensure_ascii=False, indent=2))

    def set_debug_text(self, text: str | None) -> None:
        self.debug_text.delete("1.0", tk.END)
        if text:
            self.debug_text.insert(tk.END, text)

    def generate_strategy(self) -> None:
        self.strategy_bindings.on_generate()

    def copy_propeller_json(self) -> None:
        self.strategy_bindings.on_copy_propeller()

    def apply_to_form(self) -> None:
        self.strategy_bindings.on_apply_to_form()

    def export_preset(self) -> None:
        self.strategy_bindings.on_export_preset()

    def set_form_values(self, format_value: str, start_bid: str, daily_budget: str, geo_list: str) -> None:
        self.form_format.set(format_value)
        self.form_bid.set(start_bid)
        self.form_budget.set(daily_budget)
        self.form_geo.set(geo_list)

    def auto_strategy(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Auto Mode", "Выберите оффер для авто-стратегии")
            return
        idx = int(selection[0])
        if idx >= len(self.displayed):
            return
        offer = self.displayed[idx]
        packet = build_strategy_packet(offer)
        creatives = [
            "🔥 Limited-time bonus for new users!",
            "Claim your reward in 2 clicks",
            "Mobile-friendly landing, instant approval",
        ]
        checklist = [
            "Set up tracking macros (${SUBID}, ${ZONEID})",
            "Upload 3-5 creatives (push + inpage)",
            "Enable smart CPC optimization",
            "Monitor conversions every 50 clicks",
        ]
        auto_text = [
            "AUTO STRATEGY MODE",
            f"Offer: {offer.name} ({offer.offer_id})",
            f"Risk: {offer.risk_level.upper()} — {offer.risk_reason}",
            "\nJSON:",
            packet,
            "\nStrategy:",
            "- Start campaign with blended formats and device targeting from recommendations.",
            "- Use campaign simulator to keep CPA below payout/2.",
            "Creatives:",
            *[f"  • {c}" for c in creatives],
            "Checklist:",
            *[f"  • {item}" for item in checklist],
        ]
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, "\n".join(auto_text))
        self.strategy_json = packet

    def _toggle_api_visibility(self) -> None:
        self.api_key_entry.configure(show="" if self.api_key_visible.get() else "•")

    def save_openai_settings(self) -> None:
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showwarning("OpenAI", "Заполните API ключ")
            return
        try:
            temperature = round(float(self.api_temperature_var.get()), 2)
        except (TypeError, ValueError):
            temperature = 0.2
            self.api_temperature_var.set(temperature)
        config = load_app_config()
        config.update(
            {
                "OPENAI_API_KEY": key,
                "OPENAI_MODEL": self.api_model_var.get() or "gpt-4.1",
                "OPENAI_TEMPERATURE": temperature,
            }
        )
        save_app_config(config)
        self.openai_status_var.set("Сохранено")
        messagebox.showinfo("OpenAI", "Настройки сохранены в config.json")

    def test_openai_settings(self) -> None:
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showwarning("OpenAI", "Введите ключ для проверки")
            return
        status = f"{self.api_model_var.get()} | T={float(self.api_temperature_var.get()):.2f}"
        self.openai_status_var.set(status)
        messagebox.showinfo("OpenAI", "Настройки готовы. Генерация будет использовать эти параметры.")

    def _recalc_simulator(self, offer: OfferNormalized | None = None) -> None:
        try:
            budget = float(self.budget_var.get())
        except ValueError:
            budget = 30.0
        try:
            cpc = float(self.cpc_var.get())
        except ValueError:
            cpc = 0.02
        if offer:
            estimated_cr = offer.cr or 0.8
        else:
            try:
                estimated_cr = float(self.cr_var.get())
            except ValueError:
                estimated_cr = 0.8
        clicks = int(budget / max(cpc, 0.001))
        leads = round(clicks * (estimated_cr / 100), 2)
        payout = offer.payout_usd if offer else 3.0
        revenue = round(leads * payout, 2)
        net = round(revenue - budget, 2)

        self.cpc_var.set(f"{cpc:.3f}")
        self.cr_var.set(f"{estimated_cr:.2f}")
        self.expected_clicks_var.set(str(clicks))
        self.expected_leads_var.set(str(leads))
        self.revenue_var.set(f"{revenue:.2f}")
        self.net_var.set(f"{net:+.2f}")
