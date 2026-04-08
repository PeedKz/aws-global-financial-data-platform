from __future__ import annotations

import os
from typing import Any

import requests


BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageClient:
    def __init__(self, api_key: str | None = None, *, timeout: int = 30) -> None:
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not found.")

    def call(self, **params: Any) -> dict[str, Any]:
        request_params = {**params, "apikey": self.api_key}
        response = requests.get(BASE_URL, params=request_params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        api_message_type = None
        api_message = None
        for key, message_type in (
            ("Information", "information"),
            ("Note", "note"),
            ("Error Message", "error"),
        ):
            if key in payload:
                api_message_type = message_type
                api_message = payload[key]
                break

        return {
            "request_params": params,
            "request_url": self._redact_api_key(response.url),
            "request_status_code": response.status_code,
            "api_message_type": api_message_type,
            "api_message": api_message,
            "raw_payload": payload,
        }

    def _redact_api_key(self, url: str) -> str:
        return url.replace(self.api_key, "***REDACTED***")

    def fetch_stock_prices_daily(self, symbol: str, *, outputsize: str = "compact") -> dict[str, Any]:
        return self.call(function="TIME_SERIES_DAILY", symbol=symbol, outputsize=outputsize)

    def fetch_company_overview(self, symbol: str) -> dict[str, Any]:
        return self.call(function="OVERVIEW", symbol=symbol)

    def fetch_income_statement(self, symbol: str) -> dict[str, Any]:
        return self.call(function="INCOME_STATEMENT", symbol=symbol)

    def fetch_balance_sheet(self, symbol: str) -> dict[str, Any]:
        return self.call(function="BALANCE_SHEET", symbol=symbol)

    def fetch_fx_daily(self, from_symbol: str, to_symbol: str, *, outputsize: str = "compact") -> dict[str, Any]:
        return self.call(
            function="FX_DAILY",
            from_symbol=from_symbol,
            to_symbol=to_symbol,
            outputsize=outputsize,
        )

    def fetch_macro_real_gdp(self) -> dict[str, Any]:
        return self.call(function="REAL_GDP")
