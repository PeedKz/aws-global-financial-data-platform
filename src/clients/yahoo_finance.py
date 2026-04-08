from __future__ import annotations

from typing import Any

import yfinance as yf


def fetch_market_prices_daily(
    symbol: str,
    *,
    start: str,
    end: str,
    interval: str = "1d",
    auto_adjust: bool = False,
    actions: bool = True,
) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    history = ticker.history(
        start=start,
        end=end,
        interval=interval,
        auto_adjust=auto_adjust,
        actions=actions,
    )
    return {
        "request_params": {
            "start": start,
            "end": end,
            "interval": interval,
            "auto_adjust": auto_adjust,
            "actions": actions,
        },
        "raw_payload": history.reset_index().to_dict(orient="records"),
    }


def fetch_corporate_actions(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    payload = {
        "actions": ticker.actions.reset_index().to_dict(orient="records"),
        "dividends": ticker.dividends.reset_index().to_dict(orient="records"),
        "splits": ticker.splits.reset_index().to_dict(orient="records"),
    }
    return {
        "request_params": {"symbol": symbol},
        "raw_payload": payload,
    }


def fetch_company_metadata(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    payload = {
        "info": ticker.info,
        "fast_info": dict(ticker.fast_info),
    }
    return {
        "request_params": {"symbol": symbol},
        "raw_payload": payload,
    }
