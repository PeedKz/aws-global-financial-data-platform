from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawDatasetDefinition:
    source: str
    dataset: str
    key_fields: tuple[str, ...]
    description: str


RAW_DATASETS: dict[str, RawDatasetDefinition] = {
    "yahoo_market_prices_daily": RawDatasetDefinition(
        source="yahoo_finance",
        dataset="market_prices_daily",
        key_fields=("symbol",),
        description="Daily OHLCV market prices from Yahoo Finance.",
    ),
    "yahoo_corporate_actions": RawDatasetDefinition(
        source="yahoo_finance",
        dataset="corporate_actions",
        key_fields=("symbol",),
        description="Dividend and stock split events from Yahoo Finance.",
    ),
    "yahoo_company_metadata": RawDatasetDefinition(
        source="yahoo_finance",
        dataset="company_metadata",
        key_fields=("symbol",),
        description="Company and instrument metadata from Yahoo Finance.",
    ),
    "alpha_stock_prices_daily": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="stock_prices_daily",
        key_fields=("symbol",),
        description="Daily stock prices from Alpha Vantage free endpoint.",
    ),
    "alpha_company_overview": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="company_overview",
        key_fields=("symbol",),
        description="Company overview and ratios from Alpha Vantage.",
    ),
    "alpha_income_statement": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="income_statement",
        key_fields=("symbol",),
        description="Income statement payload from Alpha Vantage.",
    ),
    "alpha_balance_sheet": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="balance_sheet",
        key_fields=("symbol",),
        description="Balance sheet payload from Alpha Vantage.",
    ),
    "alpha_fx_daily": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="fx_daily",
        key_fields=("from_symbol", "to_symbol"),
        description="Daily FX rates from Alpha Vantage.",
    ),
    "alpha_macro_real_gdp": RawDatasetDefinition(
        source="alpha_vantage",
        dataset="macro_real_gdp",
        key_fields=("indicator_name",),
        description="Real GDP macroeconomic indicator from Alpha Vantage.",
    ),
}
