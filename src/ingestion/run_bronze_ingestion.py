from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.clients.alpha_vantage import AlphaVantageClient
from src.clients.yahoo_finance import (
    fetch_company_metadata,
    fetch_corporate_actions,
    fetch_market_prices_daily,
)
from src.storage.raw_writer import RawWriter


def ingest_yahoo_samples(writer: RawWriter) -> list[Path]:
    outputs: list[Path] = []
    end_date = datetime.now(UTC).date()
    start_date = end_date - timedelta(days=180)

    for symbol in ("AAPL", "MSFT", "PETR4.SA"):
        try:
            prices = fetch_market_prices_daily(
                symbol,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
            )
            outputs.append(
                writer.write_record(
                    source="yahoo_finance",
                    dataset="market_prices_daily",
                    natural_keys={"symbol": symbol},
                    request_params=prices["request_params"],
                    raw_payload=prices["raw_payload"],
                )
            )

            actions = fetch_corporate_actions(symbol)
            outputs.append(
                writer.write_record(
                    source="yahoo_finance",
                    dataset="corporate_actions",
                    natural_keys={"symbol": symbol},
                    request_params=actions["request_params"],
                    raw_payload=actions["raw_payload"],
                )
            )

            metadata = fetch_company_metadata(symbol)
            outputs.append(
                writer.write_record(
                    source="yahoo_finance",
                    dataset="company_metadata",
                    natural_keys={"symbol": symbol},
                    request_params=metadata["request_params"],
                    raw_payload=metadata["raw_payload"],
                )
            )
        except Exception as exc:
            print(f"Yahoo Finance ingestion failed for {symbol}: {exc}")

    return outputs


def ingest_alpha_samples(writer: RawWriter) -> list[Path]:
    outputs: list[Path] = []
    client = AlphaVantageClient()

    stock_symbol = "IBM"
    for dataset, fetcher in (
        ("stock_prices_daily", lambda: client.fetch_stock_prices_daily(stock_symbol)),
        ("company_overview", lambda: client.fetch_company_overview(stock_symbol)),
        ("income_statement", lambda: client.fetch_income_statement(stock_symbol)),
        ("balance_sheet", lambda: client.fetch_balance_sheet(stock_symbol)),
    ):
        try:
            result = fetcher()
            outputs.append(
                writer.write_record(
                    source="alpha_vantage",
                    dataset=dataset,
                    natural_keys={"symbol": stock_symbol},
                    request_params=result["request_params"],
                    request_url=result["request_url"],
                    request_status_code=result["request_status_code"],
                    api_message_type=result["api_message_type"],
                    api_message=result["api_message"],
                    raw_payload=result["raw_payload"],
                )
            )
        except Exception as exc:
            print(f"Alpha Vantage ingestion failed for {dataset}: {exc}")

    try:
        fx_result = client.fetch_fx_daily("USD", "BRL")
        outputs.append(
            writer.write_record(
                source="alpha_vantage",
                dataset="fx_daily",
                natural_keys={"from_symbol": "USD", "to_symbol": "BRL"},
                request_params=fx_result["request_params"],
                request_url=fx_result["request_url"],
                request_status_code=fx_result["request_status_code"],
                api_message_type=fx_result["api_message_type"],
                api_message=fx_result["api_message"],
                raw_payload=fx_result["raw_payload"],
            )
        )
    except Exception as exc:
        print(f"Alpha Vantage ingestion failed for fx_daily: {exc}")

    try:
        macro_result = client.fetch_macro_real_gdp()
        outputs.append(
            writer.write_record(
                source="alpha_vantage",
                dataset="macro_real_gdp",
                natural_keys={"indicator_name": "REAL_GDP"},
                request_params=macro_result["request_params"],
                request_url=macro_result["request_url"],
                request_status_code=macro_result["request_status_code"],
                api_message_type=macro_result["api_message_type"],
                api_message=macro_result["api_message"],
                raw_payload=macro_result["raw_payload"],
            )
        )
    except Exception as exc:
        print(f"Alpha Vantage ingestion failed for macro_real_gdp: {exc}")

    return outputs


def main() -> None:
    load_dotenv()
    writer = RawWriter(Path("data") / "bronze")
    outputs = []
    outputs.extend(ingest_yahoo_samples(writer))
    outputs.extend(ingest_alpha_samples(writer))

    print("Files written:")
    for output in outputs:
        print(output.as_posix())


if __name__ == "__main__":
    main()
