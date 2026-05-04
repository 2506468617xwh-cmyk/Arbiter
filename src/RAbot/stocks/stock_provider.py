from __future__ import annotations

from abc import ABC, abstractmethod

from RAbot.stocks.stock_models import StockBar, StockQuote


class BaseStockProvider(ABC):
    source = "base"

    @abstractmethod
    def get_quote(self, symbol: str) -> StockQuote:
        raise NotImplementedError

    @abstractmethod
    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        raise NotImplementedError

    def search_symbol(self, keyword: str) -> list[dict]:
        return []
