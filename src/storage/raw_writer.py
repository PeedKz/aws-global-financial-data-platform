from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RawWriter:
    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path)

    def write_record(
        self,
        *,
        source: str,
        dataset: str,
        natural_keys: dict[str, str],
        request_params: dict[str, Any],
        raw_payload: Any,
        request_url: str | None = None,
        request_status_code: int | None = None,
        extraction_mode: str = "full_refresh",
        api_message_type: str | None = None,
        api_message: str | None = None,
        filename: str | None = None,
    ) -> Path:
        ingestion_ts = datetime.now(UTC)
        ingestion_date = ingestion_ts.strftime("%Y-%m-%d")

        envelope = {
            "source": source,
            "dataset": dataset,
            "ingestion_ts_utc": ingestion_ts.isoformat(),
            "ingestion_date": ingestion_date,
            "extraction_mode": extraction_mode,
            "request_params": request_params,
            "request_url": request_url,
            "request_status_code": request_status_code,
            "natural_keys": natural_keys,
            "api_message_type": api_message_type,
            "api_message": api_message,
            "raw_payload": self._serialize(raw_payload),
        }

        output_path = self._build_path(
            source=source,
            dataset=dataset,
            natural_keys=natural_keys,
            ingestion_date=ingestion_date,
            filename=filename or self._default_filename(dataset, natural_keys),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=True, default=str),
            encoding="utf-8",
        )
        return output_path

    def _build_path(
        self,
        *,
        source: str,
        dataset: str,
        natural_keys: dict[str, str],
        ingestion_date: str,
        filename: str,
    ) -> Path:
        path = self.root_path / f"source={source}" / f"dataset={dataset}"
        for key, value in natural_keys.items():
            path /= f"{key}={value}"
        path /= f"ingestion_date={ingestion_date}"
        return path / filename

    @staticmethod
    def _default_filename(dataset: str, natural_keys: dict[str, str]) -> str:
        if not natural_keys:
            return f"{dataset}.json"
        suffix = "_".join(str(value).replace("/", "_") for value in natural_keys.values())
        return f"{dataset}_{suffix}.json"

    @staticmethod
    def _serialize(value: Any) -> Any:
        if hasattr(value, "to_dict"):
            try:
                return value.to_dict(orient="records")
            except TypeError:
                return value.to_dict()
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return {key: RawWriter._serialize(val) for key, val in value.items()}
        if isinstance(value, list):
            return [RawWriter._serialize(item) for item in value]
        return value
