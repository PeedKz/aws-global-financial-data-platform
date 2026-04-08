from src.contracts.raw_datasets import RAW_DATASETS


def test_raw_datasets_are_defined() -> None:
    assert RAW_DATASETS
    assert "yahoo_market_prices_daily" in RAW_DATASETS
    assert "alpha_stock_prices_daily" in RAW_DATASETS


def test_raw_dataset_names_are_unique() -> None:
    seen = {(definition.source, definition.dataset) for definition in RAW_DATASETS.values()}
    assert len(seen) == len(RAW_DATASETS)
