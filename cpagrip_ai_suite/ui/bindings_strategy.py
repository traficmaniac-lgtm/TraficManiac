from __future__ import annotations

import json
import os
import time
from pathlib import Path
from tkinter import messagebox

from ..core.ai.strategy_service import StrategyResult, StrategyService
from ..prompts.strategy_packet import build_strategy_packet


class StrategyBindings:
    def __init__(self, app, service: StrategyService | None = None):
        self.app = app
        self.service = service or StrategyService()
        self.last_result: StrategyResult | None = None

    def _update_status(self, text: str) -> None:
        self.app.strategy_status_var.set(text)

    def on_generate(self) -> None:
        offer = self.app.current_offer
        if not offer:
            messagebox.showinfo("Стратегия", "Сначала выберите оффер")
            return
        packet_str = build_strategy_packet(offer)
        self.app.set_packet_text(packet_str)
        ai_packet = json.loads(packet_str)
        self._update_status("Отправка…")
        result = self.service.generate(ai_packet, offer.offer_id, regenerate=self.app.force_regen_var.get())
        self.last_result = result
        if result.error:
            self._update_status("Ошибка")
            self.app.set_debug_text(result.debug or result.error)
            messagebox.showerror("Propeller", result.error)
            return
        self._update_status("Валидировано" if not result.from_cache else "Из кеша")
        self.app.set_propeller_json(result.data)
        self.app.set_debug_text(result.debug)

    def on_copy_propeller(self) -> None:
        if not self.last_result or not self.last_result.data:
            messagebox.showinfo("Буфер", "Нет настроек для копирования")
            return
        payload = json.dumps(self.last_result.data, ensure_ascii=False, indent=2)
        self.app.clipboard_clear()
        self.app.clipboard_append(payload)
        messagebox.showinfo("Буфер", "Propeller JSON скопирован")

    def on_apply_to_form(self) -> None:
        if not self.last_result or not self.last_result.data:
            messagebox.showinfo("Форма", "Нет данных")
            return
        data = self.last_result.data
        self.app.set_form_values(
            format_value=data.get("format", ""),
            start_bid=str(data.get("bidding", {}).get("start_bid", "")),
            daily_budget=str(data.get("caps", {}).get("daily_budget_usd", "")),
            geo_list=",".join(data.get("geo", [])),
        )

    def on_export_preset(self) -> None:
        if not self.last_result or not self.last_result.data or not self.app.current_offer:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта")
            return
        offer_id = self.app.current_offer.offer_id
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_dir = Path(os.getcwd()) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        json_path = export_dir / f"propeller_campaign_{offer_id}_{timestamp}.json"
        txt_path = export_dir / f"propeller_campaign_{offer_id}_{timestamp}.txt"
        payload = json.dumps(self.last_result.data, ensure_ascii=False, indent=2)
        json_path.write_text(payload, encoding="utf-8")
        checklist_lines = [
            f"Формат: {self.last_result.data.get('format')}",
            f"Стартовый бид: {self.last_result.data.get('bidding', {}).get('start_bid')}",
            f"Daily budget: {self.last_result.data.get('caps', {}).get('daily_budget_usd')}",
            f"Stop rules: {self.last_result.data.get('test_plan', {}).get('stop_rules')}",
        ]
        creatives = self.last_result.data.get("creatives", [])
        for idx, creative in enumerate(creatives[:3], 1):
            checklist_lines.append(f"Creative {idx}: {creative.get('title')} | {creative.get('text')}")
        txt_path.write_text("\n".join(checklist_lines), encoding="utf-8")
        messagebox.showinfo("Экспорт", f"Сохранено:\n{json_path}\n{txt_path}")
