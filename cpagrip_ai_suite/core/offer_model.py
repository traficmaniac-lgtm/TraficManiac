from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.geo import extract_geo_list, normalize_country_codes
from ..utils.text import split_csv
from .scoring import OfferScore, score_offer


@dataclass
class OfferRaw:
    offer_id: str
    name: str
    description: Optional[str]
    payout: float
    conversion_type: Optional[str]
    category: Optional[str]
    allowed_countries: List[str]
    forbidden_countries: List[str]
    device: List[str]
    os: List[str]
    traffic_allowed: List[str]
    traffic_forbidden: List[str]
    preview_url: Optional[str]
    tracking_template: Optional[str]
    epc: Optional[float]
    cr: Optional[float]
    cap: Optional[float]
    network_rules: Optional[str]
    incentive_allowed: Optional[bool]
    currency: Optional[str]
    offerlink: Optional[str]


@dataclass
class OfferNormalized:
    offer_id: str
    name: str
    description: Optional[str]
    geo_allowed: List[str]
    geo_restricted: List[str]
    payout_usd: float
    currency: Optional[str]
    epc: Optional[float]
    cr: Optional[float]
    cap_daily: Optional[float]
    conversion_type: Optional[str]
    category: Optional[str]
    incentive_allowed: Optional[bool]
    traffic_allowed: List[str]
    traffic_forbidden: List[str]
    devices: List[str]
    os: List[str]
    browser: List[str]
    connection: List[str]
    tracking_url: str
    preview_url: Optional[str]
    lp_type_guess: Optional[str]
    network_rules: Optional[str]
    risk_flag: bool
    risk_level: str
    risk_reason: str
    score: float
    score_breakdown: List[Dict[str, float]]
    score_notes: str
    missing_fields: List[str]
    traffic_fit: str
    raw_dump: Dict[str, Any]
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_strategy_offer(self) -> Dict[str, Any]:
        missing = list(self.missing_fields)
        offer_payload = {
            "geo": {"allowed": self.geo_allowed, "restricted": self.geo_restricted},
            "money": {
                "payout_usd": self.payout_usd,
                "currency": self.currency,
                "epc": self.epc,
                "cr": self.cr,
                "cap_daily": self.cap_daily,
            },
            "flow": {
                "conversion_type": self.conversion_type,
                "incentive_allowed": self.incentive_allowed,
                "kyc_required": _flag_from_rules(self.network_rules, "kyc"),
                "sms_pin": _flag_from_rules(self.conversion_type or "", "pin"),
            },
            "traffic": {
                "allowed_sources": self.traffic_allowed,
                "forbidden_sources": self.traffic_forbidden,
                "adult_ok": _flag_from_rules(self.network_rules, "adult"),
                "brand_bidding": _flag_from_rules(self.network_rules, "brand"),
            },
            "tech": {
                "device": self.devices,
                "os": self.os,
                "browser": self.browser,
                "connection": self.connection,
            },
            "links": {
                "tracking_url": self.tracking_url,
                "preview_url": self.preview_url,
                "lp_type_guess": self.lp_type_guess,
            },
            "meta": {
                "id": self.offer_id,
                "name": self.name,
                "category": self.category,
                "network": "CPAGrip",
                "updated_at": self.updated_at,
                "missing_fields": missing,
                "raw_dump": self.raw_dump,
                "score": self.score,
                "score_breakdown": self.score_breakdown,
                "risk": {"level": self.risk_level, "reason": self.risk_reason},
                "traffic_fit": self.traffic_fit,
            },
        }
        return offer_payload


@dataclass
class OfferNormalizationResult:
    offers: List[OfferNormalized]
    errors: List[str]


def normalize_offer(raw: OfferRaw, tracking_id_macro: str = "${SUBID}") -> OfferNormalized:
    missing_fields: List[str] = []
    geo_allowed = normalize_country_codes(raw.allowed_countries)
    geo_restricted = normalize_country_codes(raw.forbidden_countries)
    conversion_type = raw.conversion_type
    if conversion_type is None:
        missing_fields.append("conversion_type")
    payout_usd = raw.payout or 0.0
    currency = raw.currency or "USD"
    if raw.currency is None:
        missing_fields.append("currency")

    tracking_url = build_tracking_url(raw, tracking_id_macro)
    if tracking_url is None:
        missing_fields.append("tracking_url")
        tracking_url = ""

    preview_url = raw.preview_url or raw.offerlink
    if preview_url is None:
        missing_fields.append("preview_url")

    lp_type_guess = "direct_link"
    if preview_url and "smart" in preview_url.lower():
        lp_type_guess = "smartlink"

    score: OfferScore = score_offer(
        payout_usd=payout_usd,
        conversion_type=conversion_type,
        geo_allowed=geo_allowed,
        epc=raw.epc,
        cr=raw.cr,
        incentive_allowed=raw.incentive_allowed,
        traffic_forbidden=raw.traffic_forbidden,
        cap=raw.cap,
        offer_title=raw.name,
    )

    traffic_fit = _infer_traffic_fit(raw.traffic_allowed)

    return OfferNormalized(
        offer_id=raw.offer_id,
        name=raw.name,
        description=raw.description,
        geo_allowed=geo_allowed,
        geo_restricted=geo_restricted,
        payout_usd=payout_usd,
        currency=currency,
        epc=raw.epc,
        cr=raw.cr,
        cap_daily=raw.cap,
        conversion_type=conversion_type,
        category=raw.category,
        incentive_allowed=raw.incentive_allowed,
        traffic_allowed=raw.traffic_allowed,
        traffic_forbidden=raw.traffic_forbidden,
        devices=raw.device,
        os=raw.os,
        browser=[],
        connection=[],
        tracking_url=tracking_url,
        preview_url=preview_url,
        lp_type_guess=lp_type_guess,
        network_rules=raw.network_rules,
        risk_flag=score.risk_flag,
        risk_level=score.risk_level,
        risk_reason=score.risk_reason,
        score=score.score,
        score_breakdown=[{"label": label, "value": value} for label, value in score.breakdown],
        score_notes=score.notes,
        missing_fields=missing_fields,
        traffic_fit=traffic_fit,
        raw_dump=asdict(raw),
        updated_at=datetime.utcnow().isoformat() + "Z",
    )


def normalize_offers(raw_offers: List[OfferRaw | Dict[str, Any]], tracking_macro: str = "${SUBID}") -> OfferNormalizationResult:
    normalized: List[OfferNormalized] = []
    errors: List[str] = []
    for item in raw_offers:
        try:
            raw_item = item if isinstance(item, OfferRaw) else parse_offer(item)
            normalized.append(normalize_offer(raw_item, tracking_macro))
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
    normalized.sort(key=lambda off: off.score, reverse=True)
    return OfferNormalizationResult(offers=normalized, errors=errors)


def parse_offer(item: Dict[str, Any]) -> OfferRaw:
    allowed_countries = extract_geo_list(item.get("accepted_countries") or item.get("countries") or "")
    forbidden_countries = extract_geo_list(item.get("forbidden", ""))
    device = split_csv(item.get("device", ""))
    os_list = split_csv(item.get("os", ""))
    traffic_allowed = split_csv(item.get("traffic_allowed", item.get("traffic_source", "")))
    traffic_forbidden = split_csv(item.get("traffic_forbidden", ""))
    return OfferRaw(
        offer_id=str(item.get("id") or item.get("offer_id") or ""),
        name=item.get("title", "Без названия"),
        description=item.get("description"),
        payout=float(item.get("payout") or 0.0),
        conversion_type=item.get("type") or item.get("offer_type"),
        category=item.get("category") or item.get("vertical"),
        allowed_countries=allowed_countries,
        forbidden_countries=forbidden_countries,
        device=device,
        os=os_list,
        traffic_allowed=traffic_allowed,
        traffic_forbidden=traffic_forbidden,
        preview_url=item.get("offerphoto") or item.get("preview_url") or item.get("offerimage"),
        tracking_template=item.get("offerlink"),
        epc=_safe_float(item.get("epc")),
        cr=_safe_float(item.get("cr")),
        cap=_safe_float(item.get("cap")),
        network_rules=item.get("network_rules") or item.get("restrictions"),
        incentive_allowed=_safe_bool(item.get("incentive_allowed"), item.get("incent")),
        currency=item.get("currency"),
        offerlink=item.get("offerlink"),
    )


def _infer_traffic_fit(allowed_sources: List[str]) -> str:
    text = " ".join(allowed_sources).lower()
    has_push = "push" in text
    has_inpage = "inpage" in text or "in-page" in text
    if has_push and has_inpage:
        return "Both"
    if has_push:
        return "Push"
    if has_inpage:
        return "Inpage"
    return "Unknown"


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(*values: Any) -> Optional[bool]:
    for val in values:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            if val.lower() in {"1", "true", "yes", "allowed"}:
                return True
            if val.lower() in {"0", "false", "no", "not allowed"}:
                return False
    return None


def build_tracking_url(raw: OfferRaw, tracking_id_macro: str) -> Optional[str]:
    if raw.tracking_template:
        if "tracking_id=" in raw.tracking_template or "subid=" in raw.tracking_template:
            return raw.tracking_template.replace("${SUBID}", tracking_id_macro)
    if raw.offer_id:
        return f"https://www.cpagrip.com/show.php?offer_id={raw.offer_id}&tracking_id={tracking_id_macro}"
    return None


def _flag_from_rules(value: Optional[str], keyword: str) -> Optional[bool]:
    if value is None:
        return None
    text = value.lower()
    if keyword.lower() in text:
        return True
    return False
