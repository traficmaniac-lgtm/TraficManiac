import re
from typing import Iterable, List


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def find_keywords(text: str, keywords: Iterable[str]) -> List[str]:
    text_lower = text.lower()
    hits = []
    for keyword in keywords:
        if keyword and keyword.lower() in text_lower:
            hits.append(keyword)
    return hits


def extract_geo_list(geo_raw: str) -> List[str]:
    matches = re.findall(r"[A-Z]{2}", geo_raw.upper())
    return list(dict.fromkeys(matches))
