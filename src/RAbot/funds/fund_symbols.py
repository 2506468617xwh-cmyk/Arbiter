from __future__ import annotations

import re


def normalize_fund_symbol(symbol: str) -> str:
    value = str(symbol or "").strip().upper()
    return re.sub(r"\s+", "", value)


def detect_fund_market(symbol: str) -> str:
    value = normalize_fund_symbol(symbol)
    if re.fullmatch(r"\d{6}\.(SH|SZ|OF)", value):
        return "CN"
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}\.US", value):
        return "US"
    if re.fullmatch(r"\d{1,5}\.HK", value):
        return "HK"
    return "UNKNOWN"


def detect_fund_type(symbol: str) -> str:
    value = normalize_fund_symbol(symbol)
    if re.fullmatch(r"\d{6}\.(SH|SZ)", value):
        return "CN_ETF"
    if re.fullmatch(r"\d{6}\.OF", value):
        return "CN_MUTUAL_FUND"
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}\.US", value):
        return "US_ETF"
    if re.fullmatch(r"\d{1,5}\.HK", value):
        return "HK_ETF"
    return "UNKNOWN"


def to_yahoo_fund_symbol(symbol: str) -> str:
    value = normalize_fund_symbol(symbol)
    market = detect_fund_market(value)
    if market == "US":
        return value.removesuffix(".US")
    if market == "HK":
        return f"{value.split('.')[0].zfill(4)}.HK"
    if market == "CN":
        code, exchange = value.split(".")
        if exchange == "SH":
            return f"{code}.SS"
        if exchange == "SZ":
            return f"{code}.SZ"
    return value


def to_longbridge_fund_symbol(symbol: str) -> str:
    value = normalize_fund_symbol(symbol)
    if detect_fund_market(value) == "HK":
        return f"{value.split('.')[0].zfill(5)}.HK"
    return value

