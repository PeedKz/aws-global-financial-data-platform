# Raw Data Model V1

## Purpose

This document defines the V1 data model for the `raw data` / `bronze` layer of the Global Financial Data Platform.

The goal of this layer is not to serve analytics directly. Its purpose is to preserve source data with maximum fidelity, enrich each extraction with operational metadata, and provide a stable replayable base for the future `silver` and `gold` layers.

This V1 was designed from:

- exploratory analysis in the notebooks
- implementation choices already materialized in `src/`
- real files already generated in `data/bronze/`
- the lakehouse architecture proposed for the project

Reference artifacts:

- [01_yahoo_finance_exploration.ipynb](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/notebooks/01_yahoo_finance_exploration.ipynb)
- [02_alpha_vantage_exploration.ipynb](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/notebooks/02_alpha_vantage_exploration.ipynb)
- [03_bronze_layer_build_journal.ipynb](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/notebooks/03_bronze_layer_build_journal.ipynb)
- [raw_datasets.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/contracts/raw_datasets.py)
- [raw_writer.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/storage/raw_writer.py)
- [run_bronze_ingestion.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/ingestion/run_bronze_ingestion.py)
- [arquitetura.xml](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/draw/arquitetura.xml)

## Architectural Position

The bronze layer is the first persistent data layer after extraction.

Logical flow:

```text
External APIs
  -> Python ingestion
  -> Bronze / Raw JSON envelopes
  -> Silver normalization
  -> Gold analytical models
  -> Athena / BI / downstream consumers
```

In the architecture of this project, the bronze layer is responsible for:

- preserving source payloads
- registering extraction metadata
- keeping lineage by source and dataset
- enabling replay and reprocessing
- isolating the instability of external APIs from downstream models

It is intentionally not responsible for:

- business-friendly schemas
- analytical aggregations
- conformed dimensions
- star schema facts

Those concerns belong to `silver` and `gold`.

## Design Principles

The following principles guided the V1 model:

1. Preserve raw payloads with minimal transformation.
2. Separate datasets by source and business domain.
3. Partition data in a lake-friendly way.
4. Store extraction metadata next to payloads.
5. Make the structure replayable and auditable.
6. Avoid over-modeling the bronze layer.
7. Keep downstream normalization explicit in the silver layer.

Practical implications:

- raw files are stored as JSON
- payloads are wrapped in a standardized ingestion envelope
- source-specific structures are preserved instead of flattened aggressively
- each ingestion run creates a new partition by ingestion date

## Scope of V1

### Sources included

- `yahoo_finance`
- `alpha_vantage`

### Datasets included

- `market_prices_daily`
- `corporate_actions`
- `company_metadata`
- `stock_prices_daily`
- `company_overview`
- `income_statement`
- `balance_sheet`
- `fx_daily`
- `macro_real_gdp`

### Current sample entities already ingested

Yahoo Finance:

- `AAPL`
- `MSFT`
- `PETR4.SA`

Alpha Vantage:

- `IBM`
- `USD/BRL`
- `REAL_GDP`

### Existing raw partitions already materialized

At the time of this document update, the repository already contains at least:

- `ingestion_date=2026-03-25`
- `ingestion_date=2026-03-27`

These partitions exist under [data/bronze](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/data/bronze).

## Storage Strategy

### Physical format

Recommended bronze storage format:

- `JSON`

Reason:

- payload fidelity is more important than columnar efficiency in the bronze layer
- JSON is a natural fit for nested API responses
- JSON keeps debugging and reprocessing easy

### File strategy

V1 stores one JSON file per combination of:

- `source`
- `dataset`
- natural key
- `ingestion_date`

This means the bronze layer is modeled as raw envelopes, not as immediately query-optimized tables.

### Path convention

Base pattern:

```text
data/bronze/
  source=<source>/
    dataset=<dataset>/
      <natural_key_1>=<value>/
        <natural_key_2>=<value>/
          ingestion_date=<yyyy-mm-dd>/
            <file>.json
```

Example:

```text
data/bronze/source=alpha_vantage/dataset=fx_daily/from_symbol=USD/to_symbol=BRL/ingestion_date=2026-03-27/fx_daily_USD_BRL.json
```

Equivalent S3-oriented pattern for future cloud deployment:

```text
s3://financial-data/bronze/source=alpha_vantage/dataset=fx_daily/from_symbol=USD/to_symbol=BRL/ingestion_date=2026-03-27/fx_daily_USD_BRL.json
```

## Ingestion Envelope Standard

All raw datasets must follow a common ingestion envelope.

### Canonical envelope

```json
{
  "source": "alpha_vantage",
  "dataset": "stock_prices_daily",
  "ingestion_ts_utc": "2026-03-27T02:49:14.620326+00:00",
  "ingestion_date": "2026-03-27",
  "extraction_mode": "full_refresh",
  "request_params": {
    "function": "TIME_SERIES_DAILY",
    "symbol": "IBM",
    "outputsize": "compact"
  },
  "request_url": "https://www.alphavantage.co/query?...&apikey=***REDACTED***",
  "request_status_code": 200,
  "natural_keys": {
    "symbol": "IBM"
  },
  "api_message_type": null,
  "api_message": null,
  "raw_payload": {}
}
```

### Envelope field definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | Logical source identifier |
| `dataset` | string | yes | Logical raw dataset name |
| `ingestion_ts_utc` | string | yes | UTC timestamp when the file was written |
| `ingestion_date` | string | yes | UTC date used for partitioning |
| `extraction_mode` | string | yes | Current execution mode, V1 uses `full_refresh` |
| `request_params` | object | yes | Parameters sent to the source call |
| `request_url` | string or null | recommended | Request URL with secrets redacted |
| `request_status_code` | integer or null | recommended | HTTP status code when available |
| `natural_keys` | object | yes | Natural identifiers for the payload |
| `api_message_type` | string or null | recommended | `information`, `note`, `error` when returned by source |
| `api_message` | string or null | recommended | API-side diagnostic message |
| `raw_payload` | object or array | yes | Original source payload preserved as raw data |

### Why this envelope matters

This structure provides:

- observability
- lineage
- recoverability
- stable interfaces for downstream normalization

Without this envelope, raw data quickly becomes difficult to audit and reprocess.

## Partitioning Strategy

### Partition columns

V1 currently uses the following partition dimensions:

- `source`
- `dataset`
- natural key fields such as `symbol`, `from_symbol`, `to_symbol`, `indicator_name`
- `ingestion_date`

### Why `ingestion_date` exists

`ingestion_date` tracks when the system captured the payload, not the business date inside the payload.

This distinction is essential because:

- sources may revise old data
- replay needs to preserve extraction history
- the same business entity may be extracted multiple times
- the raw layer should model capture events, not just business facts

### UTC note

The implementation currently partitions by UTC date.

This can produce a situation where:

- local date in `America/Sao_Paulo` is still one day
- partition date in UTC has already rolled to the next day

That is expected behavior in the current V1 and is reflected in the real generated partitions.

## Source-by-Source Modeling

## Yahoo Finance

Yahoo Finance is used in V1 primarily for:

- daily prices
- dividends and splits
- instrument/company metadata

### 1. `bronze.yahoo_finance.market_prices_daily`

#### Purpose

Store daily market price history for equities and ETFs.

#### Source access pattern

- `yfinance.Ticker(symbol).history(...)`
- optionally `yf.download(...)`

#### Business grain

- one symbol per raw file
- one ingestion event per partition

#### Natural key

- `symbol`

#### Partitions

- `source=yahoo_finance`
- `dataset=market_prices_daily`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload shape

Observed columns from exploration:

- `Date`
- `Open`
- `High`
- `Low`
- `Close`
- `Adj Close`
- `Volume`
- `Dividends`
- `Stock Splits`

#### Modeling notes

- `Date` is business date from market history
- `Adj Close` is important for total-return aware use cases
- dividend and split values are included in the same series payload when requested with `actions=True`

#### Downstream role

Feeds:

- `silver.stock_prices_daily`
- return calculations
- volatility metrics
- price trend analysis

#### Known caveats

- timezone varies with exchange
- Yahoo output can differ by market and instrument type
- the raw payload should be preserved before any timezone harmonization

### 2. `bronze.yahoo_finance.corporate_actions`

#### Purpose

Persist corporate action events explicitly for each symbol.

#### Source access pattern

- `Ticker.actions`
- `Ticker.dividends`
- `Ticker.splits`

#### Business grain

- one symbol per raw file
- action events nested under that symbol

#### Natural key

- `symbol`

#### Partitions

- `source=yahoo_finance`
- `dataset=corporate_actions`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

The raw payload currently stores:

- `actions`
- `dividends`
- `splits`

Each substructure keeps the source-oriented form returned by `yfinance`.

#### Downstream role

Feeds:

- `silver.corporate_actions`
- adjusted-price validation
- reconciliation against Alpha Vantage free daily prices

#### Known caveats

- some symbols may have sparse or empty action histories
- event timing and timezone must be normalized later in silver

### 3. `bronze.yahoo_finance.company_metadata`

#### Purpose

Persist descriptive instrument and company metadata.

#### Source access pattern

- `Ticker.info`
- `Ticker.fast_info`

#### Business grain

- one symbol per raw file

#### Natural key

- `symbol`

#### Partitions

- `source=yahoo_finance`
- `dataset=company_metadata`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

The V1 raw payload stores both:

- `info`
- `fast_info`

This is intentional because field availability differs across instruments and markets.

#### Fields often useful later

- short name
- long name
- quote type
- sector
- industry
- country
- currency
- exchange
- market cap

#### Downstream role

Feeds:

- `silver.company_reference`
- `gold.dim_company`
- `gold.dim_sector`

#### Known caveats

- ETFs may lack sector or country
- some values vary in completeness by symbol
- metadata may change over time, so raw snapshots matter

## Alpha Vantage

Alpha Vantage is used in V1 primarily for:

- daily stock prices using free endpoints
- structured fundamentals
- FX data
- macroeconomic series

### Free-plan design note

During exploration, `TIME_SERIES_DAILY_ADJUSTED` was found to be premium-only. Therefore V1 uses the free endpoint `TIME_SERIES_DAILY`.

This is a key V1 design decision.

### 4. `bronze.alpha_vantage.stock_prices_daily`

#### Purpose

Store daily stock prices from the free Alpha Vantage stock endpoint.

#### Source access pattern

- `TIME_SERIES_DAILY`

#### Business grain

- one symbol per raw file

#### Natural key

- `symbol`

#### Partitions

- `source=alpha_vantage`
- `dataset=stock_prices_daily`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

- `Meta Data`
- `Time Series (Daily)`

#### Relevant nested fields

Within `Time Series (Daily)`:

- `1. open`
- `2. high`
- `3. low`
- `4. close`
- `5. volume`

#### Downstream role

Feeds:

- reconciliation with Yahoo price data
- `silver.stock_prices_daily`
- fallback price source for equities

#### Known caveats

- no adjusted close in the free endpoint
- no corporate actions embedded like Yahoo history with `actions=True`
- rate limiting must be handled carefully

### 5. `bronze.alpha_vantage.company_overview`

#### Purpose

Persist descriptive and financial overview attributes for companies.

#### Source access pattern

- `OVERVIEW`

#### Business grain

- one symbol per raw file

#### Natural key

- `symbol`

#### Partitions

- `source=alpha_vantage`
- `dataset=company_overview`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Important fields commonly observed

- `Symbol`
- `Name`
- `Sector`
- `Industry`
- `Country`
- `Currency`
- `MarketCapitalization`
- valuation ratios
- dividend information
- 52-week range

#### Downstream role

Feeds:

- `silver.company_reference`
- `gold.dim_company`
- fundamentals-enriched analytical views

#### Known caveats

- field presence may vary by ticker
- numeric fields arrive as strings and should not be coerced in bronze

### 6. `bronze.alpha_vantage.income_statement`

#### Purpose

Persist annual and quarterly income statement data.

#### Source access pattern

- `INCOME_STATEMENT`

#### Business grain

- one symbol per raw file

#### Natural key

- `symbol`

#### Partitions

- `source=alpha_vantage`
- `dataset=income_statement`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

- `symbol`
- `annualReports`
- `quarterlyReports`

#### Downstream role

Feeds:

- `silver.income_statement_quarterly`
- profitability and growth metrics
- gross margin and net margin analyses

#### Known caveats

- fields are numerous and mostly string-valued
- missing values may appear as strings or null-like representations
- field harmonization belongs to silver

### 7. `bronze.alpha_vantage.balance_sheet`

#### Purpose

Persist annual and quarterly balance sheet data.

#### Source access pattern

- `BALANCE_SHEET`

#### Business grain

- one symbol per raw file

#### Natural key

- `symbol`

#### Partitions

- `source=alpha_vantage`
- `dataset=balance_sheet`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

- `symbol`
- `annualReports`
- `quarterlyReports`

#### Downstream role

Feeds:

- `silver.balance_sheet_quarterly`
- leverage metrics
- liquidity metrics
- capital structure analysis

#### Known caveats

- same type-normalization concern as income statements
- fiscal date fields should be standardized only in silver

### 8. `bronze.alpha_vantage.fx_daily`

#### Purpose

Persist daily FX rates to support global use cases.

#### Source access pattern

- `FX_DAILY`

#### Business grain

- one currency pair per raw file

#### Natural keys

- `from_symbol`
- `to_symbol`

#### Partitions

- `source=alpha_vantage`
- `dataset=fx_daily`
- `from_symbol=<currency>`
- `to_symbol=<currency>`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

- `Meta Data`
- `Time Series FX (Daily)`

#### Downstream role

Feeds:

- `silver.fx_rates_daily`
- normalization of monetary values
- global dashboarding

#### Known caveats

- market day conventions differ from equity markets
- FX time zone in metadata may differ from stock datasets

### 9. `bronze.alpha_vantage.macro_real_gdp`

#### Purpose

Persist the Real GDP macroeconomic series.

#### Source access pattern

- `REAL_GDP`

#### Business grain

- one indicator per raw file

#### Natural key

- `indicator_name=REAL_GDP`

#### Partitions

- `source=alpha_vantage`
- `dataset=macro_real_gdp`
- `indicator_name=REAL_GDP`
- `ingestion_date=<yyyy-mm-dd>`

#### Expected payload structure

- `name`
- `interval`
- `unit`
- `data`

#### Downstream role

Feeds:

- `silver.macro_real_gdp`
- macro context enrichment for gold-layer analytics

#### Known caveats

- indicator frequency differs from daily market data
- joining this data to market facts requires date-grain decisions in silver or gold

## Canonical Dataset Catalog

| Source | Dataset | Natural Keys | Core Purpose |
|---|---|---|---|
| `yahoo_finance` | `market_prices_daily` | `symbol` | Daily OHLCV plus adjusted close and actions in price series |
| `yahoo_finance` | `corporate_actions` | `symbol` | Dividends and split events |
| `yahoo_finance` | `company_metadata` | `symbol` | Instrument and company descriptive metadata |
| `alpha_vantage` | `stock_prices_daily` | `symbol` | Daily stock prices from free endpoint |
| `alpha_vantage` | `company_overview` | `symbol` | Structured company overview and ratios |
| `alpha_vantage` | `income_statement` | `symbol` | Annual and quarterly income statements |
| `alpha_vantage` | `balance_sheet` | `symbol` | Annual and quarterly balance sheets |
| `alpha_vantage` | `fx_daily` | `from_symbol`, `to_symbol` | Daily FX rates |
| `alpha_vantage` | `macro_real_gdp` | `indicator_name` | Macroeconomic GDP series |

## Mapping to the Current Implementation

The current codebase already reflects this model.

### Dataset definitions

Logical dataset definitions live in:

- [raw_datasets.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/contracts/raw_datasets.py)

### Envelope writer

Physical raw file generation is handled by:

- [raw_writer.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/storage/raw_writer.py)

### Source clients

Source-specific extraction logic lives in:

- [yahoo_finance.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/clients/yahoo_finance.py)
- [alpha_vantage.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/clients/alpha_vantage.py)

### Ingestion orchestration

Execution orchestration lives in:

- [run_bronze_ingestion.py](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/src/ingestion/run_bronze_ingestion.py)

## Relationship to Silver and Gold

The bronze layer is intentionally source-centric. The silver layer will become entity-centric and analysis-ready.

### Bronze to Silver mapping

- `market_prices_daily` + `stock_prices_daily`
  -> `silver.stock_prices_daily`
- `corporate_actions`
  -> `silver.corporate_actions`
- `company_metadata` + `company_overview`
  -> `silver.company_reference`
- `income_statement`
  -> `silver.income_statement_quarterly`
- `balance_sheet`
  -> `silver.balance_sheet_quarterly`
- `fx_daily`
  -> `silver.fx_rates_daily`
- `macro_real_gdp`
  -> `silver.macro_real_gdp`

### Silver to Gold mapping

- `silver.stock_prices_daily`
  -> `gold.fact_market_metrics`
- `silver.fx_rates_daily`
  -> `gold.fact_fx_rates`
- `silver.company_reference`
  -> `gold.dim_company`
- `silver.macro_real_gdp`
  -> macro context dimension or analytical helper tables

## Naming Conventions

### Dataset names

Rules:

- use `snake_case`
- prefer business-oriented names over endpoint-oriented names
- keep names stable even if implementation details change

Examples:

- `market_prices_daily`
- `company_metadata`
- `company_overview`
- `income_statement`
- `macro_real_gdp`

### Partition names

Rules:

- `source=<value>`
- `dataset=<value>`
- natural keys as `key=value`
- `ingestion_date=<yyyy-mm-dd>`

### File names

V1 default file naming:

- `<dataset>_<natural_key_values>.json`

Examples:

- `market_prices_daily_AAPL.json`
- `stock_prices_daily_IBM.json`
- `fx_daily_USD_BRL.json`

## Operational Considerations

### Replayability

Because bronze files are stored by ingestion date, historical snapshots can be replayed.

This supports:

- backfills
- debugging
- incident recovery
- source comparison over time

### Auditability

The envelope preserves:

- what was requested
- when it was requested
- from which source
- with which business identity

This is essential in data engineering projects that aim to demonstrate production thinking.

### Source instability

External APIs are unstable by nature. V1 isolates this instability by:

- preserving source responses
- storing API-side diagnostic messages
- masking credentials in URLs
- avoiding premature flattening

### Security

API keys must not leak into persisted raw files.

Current V1 behavior:

- Alpha Vantage URLs are stored with the API key redacted
- credentials are loaded from `.env`
- `.gitignore` excludes `.env`

### Rate limits

Alpha Vantage free-plan constraints are a real modeling concern because they influence:

- ingestion frequency
- retry behavior
- orchestration timing
- dataset freshness expectations

These constraints do not change the bronze schema itself, but they do affect operational scheduling.

## Risks and Caveats

### Yahoo Finance

- not an official enterprise-grade contract in the same sense as paid market feeds
- metadata variability across symbols
- timezone variation by exchange
- possible payload shape differences across instruments

### Alpha Vantage

- free endpoint limitations
- premium-only endpoints for some richer price variants
- rate limiting
- many numeric fields arriving as strings

### Cross-source issues

- same entity may differ in naming across sources
- business date and ingestion date are not the same thing
- field semantics may not perfectly align between Yahoo and Alpha Vantage

These are not defects in V1. They are exactly the reasons why silver normalization exists.

## Why Bronze Is Not a Star Schema

One common mistake in data engineering projects is forcing warehouse-style modeling too early.

This project intentionally avoids that in bronze.

Bronze should answer:

- what did the source return
- when did we capture it
- how did we ask for it

Bronze should not answer:

- what is the final conformed company dimension
- what is the canonical daily fact table
- what is the trusted analytical metric

Those answers belong to later layers.

## Recommended Evolution Path

From this V1, the most natural next steps are:

1. Build `silver.stock_prices_daily`.
2. Build `silver.company_reference`.
3. Build `silver.fx_rates_daily`.
4. Add tests for raw envelopes and normalization logic.
5. Add orchestration and data quality checks.

## Summary

The V1 bronze model is organized around nine raw datasets separated by source and business domain. Each ingestion event is stored as a JSON envelope containing extraction metadata, natural keys, request details, and the raw payload itself. The model prioritizes fidelity, lineage, replayability, and cloud-ready partitioning over analytical convenience.

This is the correct tradeoff for a modern data engineering project: keep bronze raw, make silver reliable, and make gold analytical.
