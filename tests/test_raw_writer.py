import json
from pathlib import Path

from src.storage.raw_writer import RawWriter


def test_raw_writer_creates_expected_partitioned_file(tmp_path: Path) -> None:
    writer = RawWriter(tmp_path / "bronze")

    output = writer.write_record(
        source="alpha_vantage",
        dataset="fx_daily",
        natural_keys={"from_symbol": "USD", "to_symbol": "BRL"},
        request_params={"function": "FX_DAILY"},
        request_url="https://example.com?apikey=***REDACTED***",
        request_status_code=200,
        raw_payload={"payload": "ok"},
    )

    assert output.exists()
    assert "source=alpha_vantage" in output.as_posix()
    assert "dataset=fx_daily" in output.as_posix()
    assert "from_symbol=USD" in output.as_posix()
    assert "to_symbol=BRL" in output.as_posix()

    envelope = json.loads(output.read_text(encoding="utf-8"))
    assert envelope["source"] == "alpha_vantage"
    assert envelope["dataset"] == "fx_daily"
    assert envelope["natural_keys"] == {"from_symbol": "USD", "to_symbol": "BRL"}
    assert envelope["request_status_code"] == 200
    assert envelope["raw_payload"] == {"payload": "ok"}


def test_raw_writer_generates_default_filename(tmp_path: Path) -> None:
    writer = RawWriter(tmp_path / "bronze")

    output = writer.write_record(
        source="yahoo_finance",
        dataset="market_prices_daily",
        natural_keys={"symbol": "AAPL"},
        request_params={"interval": "1d"},
        raw_payload=[],
    )

    assert output.name == "market_prices_daily_AAPL.json"
