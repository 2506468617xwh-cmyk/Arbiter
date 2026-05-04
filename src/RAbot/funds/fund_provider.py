from __future__ import annotations

from abc import ABC, abstractmethod

from RAbot.funds.fund_models import FundBar, FundInfo, FundQuote


class BaseFundProvider(ABC):
    source = "base"

    @abstractmethod
    def get_info(self, symbol: str) -> FundInfo:
        raise NotImplementedError

    @abstractmethod
    def get_quote(self, symbol: str) -> FundQuote:
        raise NotImplementedError

    @abstractmethod
    def get_history(self, symbol: str, period: str = "day", count: int = 500) -> list[FundBar]:
        raise NotImplementedError

    def search_fund(self, keyword: str) -> list[dict]:
        return []

