from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import requests


@dataclass(frozen=True)
class FXQuote:
    rate: float
    source: str


def fetch_live_rate(from_currency: str, to_currency: str) -> Optional[FXQuote]:
    """
    Fetch a live rate using a public endpoint.
    Returns None if the request fails for any reason.
    """
    fc = from_currency.strip().upper()
    tc = to_currency.strip().upper()
    if not fc or not tc or fc == tc:
        return FXQuote(rate=1.0, source="identity")

    # Frankfurter API (ECB reference rates). No API key.
    # https://www.frankfurter.app/
    try:
        resp = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": fc, "to": tc},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = float(data["rates"][tc])
        return FXQuote(rate=rate, source=f"live:frankfurter:{data.get('date','latest')}")
    except Exception:
        return None


def convert(amount: float, rate: float) -> float:
    return float(amount) * float(rate)

