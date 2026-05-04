from __future__ import annotations

import re


def normalize_symbol(symbol: str) -> str:
    value = str(symbol or "").strip().upper()
    value = re.sub(r"\s+", "", value)
    return value


def detect_market(symbol: str) -> str:
    value = normalize_symbol(symbol)
    if re.fullmatch(r"\d{6}\.(SH|SZ)", value):
        return "CN"
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}\.US", value):
        return "US"
    if re.fullmatch(r"\d{1,5}\.HK", value):
        return "HK"
    return "UNKNOWN"


def to_yahoo_symbol(symbol: str) -> str:
    value = normalize_symbol(symbol)
    market = detect_market(value)
    if market == "HK":
        code = value.split(".")[0].zfill(4)
        return f"{code}.HK"
    if market == "US":
        return value.removesuffix(".US")
    if market == "CN":
        code, exchange = value.split(".")
        return f"{code}.SS" if exchange == "SH" else f"{code}.SZ"
    return value


def to_longbridge_symbol(symbol: str) -> str:
    value = normalize_symbol(symbol)
    market = detect_market(value)
    if market == "HK":
        code = value.split(".")[0].zfill(5)
        return f"{code}.HK"
    return value
