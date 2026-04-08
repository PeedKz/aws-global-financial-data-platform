# Raw Data Model V1

## Objetivo

Este documento define a V1 da modelagem da camada `raw data` / `bronze` para a plataforma de dados financeiros.

A proposta foi derivada a partir das explorações feitas em:

- [01_yahoo_finance_exploration.ipynb](c:/Users/PedroRocha/Desktop/meuprojeto/notebooks/01_yahoo_finance_exploration.ipynb)
- [02_alpha_vantage_exploration.ipynb](c:/Users/PedroRocha/Desktop/meuprojeto/notebooks/02_alpha_vantage_exploration.ipynb)
- [arquitetura.xml](c:/Users/PedroRocha/Desktop/meuprojeto/draw/arquitetura.xml)

A intenção desta camada não é servir analytics diretamente. O objetivo é:

- preservar o payload bruto retornado pelas APIs
- registrar metadados de ingestão
- permitir replay e reprocessamento
- sustentar a normalização da camada `silver`

## Princípios da Bronze Layer

- O dado bruto deve ser armazenado o mais próximo possível da resposta original da API.
- Cada dataset raw deve incluir metadados de controle de ingestão.
- O particionamento deve facilitar reprocessamento por fonte, dataset e data de ingestão.
- A modelagem V1 deve priorizar estabilidade operacional, não otimização analítica.
- Sempre que possível, o campo `raw_payload` deve manter o JSON original da fonte.

## Escopo V1

Fontes incluídas:

- `yahoo_finance`
- `alpha_vantage`

Datasets V1:

- `market_prices_daily`
- `corporate_actions`
- `company_metadata`
- `stock_prices_daily`
- `company_overview`
- `income_statement`
- `balance_sheet`
- `fx_daily`
- `macro_real_gdp`

## Estratégia de Armazenamento

Formato recomendado de arquivo na bronze:

- `JSON`

Formato do conteúdo:

- 1 arquivo JSON por combinação de `source + dataset + natural key + ingestion_date`
- cada arquivo pode conter um envelope com metadados e o `raw_payload`

Exemplo de path:

```text
s3://financial-data/bronze/source=yahoo_finance/dataset=market_prices_daily/symbol=AAPL/ingestion_date=2026-03-24/file.json
```

Partições recomendadas:

- `source`
- `dataset`
- chave natural quando fizer sentido, por exemplo `symbol`, `from_symbol`, `to_symbol`
- `ingestion_date`

## Envelope Padrão de Ingestão

Todos os datasets raw devem seguir um envelope base parecido com este:

```json
{
  "source": "alpha_vantage",
  "dataset": "stock_prices_daily",
  "ingestion_ts_utc": "2026-03-24T12:00:00Z",
  "ingestion_date": "2026-03-24",
  "request_params": {
    "function": "TIME_SERIES_DAILY",
    "symbol": "IBM",
    "outputsize": "compact"
  },
  "request_url": "https://www.alphavantage.co/query?...",
  "request_status_code": 200,
  "natural_keys": {
    "symbol": "IBM"
  },
  "raw_payload": {}
}
```

Campos mínimos obrigatórios:

- `source`
- `dataset`
- `ingestion_ts_utc`
- `ingestion_date`
- `request_params`
- `natural_keys`
- `raw_payload`

Campos altamente recomendados:

- `request_url`
- `request_status_code`
- `extraction_mode`
- `api_message_type`
- `api_message`

## Catálogo de Tabelas Raw V1

### 1. `bronze.yahoo_finance.market_prices_daily`

Objetivo:
- armazenar o payload bruto de preços diários de mercado para ações e ETFs

Origem:
- `yfinance.Ticker().history(...)`
- `yf.download(...)`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=yahoo_finance`
- `dataset=market_prices_daily`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- série diária contendo `Date`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`, `Dividends`, `Stock Splits`

Uso futuro:
- base para `silver.stock_prices_daily`
- suporte a métricas de retorno, volume e volatilidade

### 2. `bronze.yahoo_finance.corporate_actions`

Objetivo:
- armazenar eventos corporativos ligados ao ativo

Origem:
- `Ticker.actions`
- `Ticker.dividends`
- `Ticker.splits`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=yahoo_finance`
- `dataset=corporate_actions`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- eventos de dividendos
- eventos de split

Uso futuro:
- enriquecimento de séries ajustadas
- validação de diferenças entre `close` e `adj_close`

### 3. `bronze.yahoo_finance.company_metadata`

Objetivo:
- armazenar atributos descritivos do ativo, companhia ou ETF

Origem:
- `Ticker.info`
- `Ticker.fast_info`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=yahoo_finance`
- `dataset=company_metadata`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `shortName`
- `longName`
- `quoteType`
- `sector`
- `industry`
- `country`
- `currency`
- `exchange`
- `marketCap`

Uso futuro:
- base para `dim_company`
- base para `dim_sector`

### 4. `bronze.alpha_vantage.stock_prices_daily`

Objetivo:
- armazenar preços diários de ações usando endpoint gratuito da Alpha Vantage

Origem:
- `TIME_SERIES_DAILY`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=alpha_vantage`
- `dataset=stock_prices_daily`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `Meta Data`
- `Time Series (Daily)`

Uso futuro:
- comparação e reconciliação com Yahoo Finance
- fallback ou enriquecimento da camada silver

Observação:
- em 24 de março de 2026 a exploração indicou que `TIME_SERIES_DAILY_ADJUSTED` exige plano premium, então a V1 usa o endpoint gratuito `TIME_SERIES_DAILY`

### 5. `bronze.alpha_vantage.company_overview`

Objetivo:
- armazenar overview fundamental da empresa

Origem:
- `OVERVIEW`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=alpha_vantage`
- `dataset=company_overview`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `Symbol`
- `Name`
- `Sector`
- `Industry`
- `Country`
- `Currency`
- `MarketCapitalization`
- múltiplos ratios e métricas fundamentalistas

Uso futuro:
- complemento de `dim_company`
- base para atributos financeiros analíticos

### 6. `bronze.alpha_vantage.income_statement`

Objetivo:
- armazenar demonstrações de resultado anuais e trimestrais

Origem:
- `INCOME_STATEMENT`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=alpha_vantage`
- `dataset=income_statement`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `symbol`
- `annualReports`
- `quarterlyReports`

Uso futuro:
- construção de métricas de margem, crescimento e lucratividade

### 7. `bronze.alpha_vantage.balance_sheet`

Objetivo:
- armazenar balanço patrimonial anual e trimestral

Origem:
- `BALANCE_SHEET`

Granularidade:
- 1 símbolo por arquivo de ingestão

Chave natural:
- `symbol`

Partições:
- `source=alpha_vantage`
- `dataset=balance_sheet`
- `symbol=<ticker>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `symbol`
- `annualReports`
- `quarterlyReports`

Uso futuro:
- construção de métricas de endividamento, liquidez e estrutura de capital

### 8. `bronze.alpha_vantage.fx_daily`

Objetivo:
- armazenar taxas de câmbio diárias

Origem:
- `FX_DAILY`

Granularidade:
- 1 par de moedas por arquivo de ingestão

Chave natural:
- `from_symbol`
- `to_symbol`

Partições:
- `source=alpha_vantage`
- `dataset=fx_daily`
- `from_symbol=<currency>`
- `to_symbol=<currency>`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `Meta Data`
- `Time Series FX (Daily)`

Uso futuro:
- dashboards globais
- normalização de valores monetários

### 9. `bronze.alpha_vantage.macro_real_gdp`

Objetivo:
- armazenar indicador macroeconômico de PIB real

Origem:
- `REAL_GDP`

Granularidade:
- 1 indicador por arquivo de ingestão

Chave natural:
- `indicator_name=REAL_GDP`

Partições:
- `source=alpha_vantage`
- `dataset=macro_real_gdp`
- `indicator_name=REAL_GDP`
- `ingestion_date=<yyyy-mm-dd>`

Payload esperado:
- `name`
- `interval`
- `unit`
- `data`

Uso futuro:
- cruzamento entre performance de mercado e contexto macroeconômico

## Modelo Conceitual da Bronze V1

```text
Data source
  -> raw dataset
  -> raw ingestion envelope
  -> raw payload

yahoo_finance
  -> market_prices_daily
  -> corporate_actions
  -> company_metadata

alpha_vantage
  -> stock_prices_daily
  -> company_overview
  -> income_statement
  -> balance_sheet
  -> fx_daily
  -> macro_real_gdp
```

## Relacionamento Conceitual com as Próximas Camadas

Bronze para Silver:

- `market_prices_daily` + `stock_prices_daily` -> `silver.stock_prices_daily`
- `corporate_actions` -> `silver.corporate_actions`
- `company_metadata` + `company_overview` -> `silver.company_reference`
- `income_statement` -> `silver.income_statement_quarterly`
- `balance_sheet` -> `silver.balance_sheet_quarterly`
- `fx_daily` -> `silver.fx_rates_daily`
- `macro_real_gdp` -> `silver.macro_real_gdp`

Silver para Gold:

- `silver.stock_prices_daily` -> `gold.fact_market_metrics`
- `silver.fx_rates_daily` -> `gold.fact_fx_rates`
- `silver.company_reference` -> `gold.dim_company`
- `silver.macro_real_gdp` -> `gold.dim_macro_indicator` ou apoio analítico

## Campos de Controle Recomendados

Além do payload bruto, vale padronizar estes campos em todos os datasets:

| Campo | Descrição |
|---|---|
| `source` | Fonte do dado |
| `dataset` | Nome lógico do dataset |
| `ingestion_ts_utc` | Timestamp UTC da captura |
| `ingestion_date` | Data de partição |
| `natural_keys` | Identificador funcional do payload |
| `request_params` | Parâmetros enviados à API |
| `request_url` | URL final chamada |
| `request_status_code` | Status HTTP |
| `api_message_type` | `information`, `note`, `error`, se existir |
| `api_message` | Mensagem da API se houver rate limit ou erro |
| `raw_payload` | JSON bruto retornado |

## Convenções de Nomenclatura

Datasets:

- usar nomes em `snake_case`
- nomes orientados ao domínio e não ao endpoint quando fizer sentido

Sugestão:

- `market_prices_daily`
- `stock_prices_daily`
- `company_overview`
- `income_statement`
- `balance_sheet`
- `fx_daily`
- `macro_real_gdp`

Partições:

- `source=<valor>`
- `dataset=<valor>`
- `symbol=<valor>`
- `from_symbol=<valor>`
- `to_symbol=<valor>`
- `indicator_name=<valor>`
- `ingestion_date=<yyyy-mm-dd>`

## Decisões de Modelagem da V1

- A V1 separa Yahoo Finance e Alpha Vantage em datasets independentes para preservar rastreabilidade de fonte.
- A V1 mantém um desenho orientado a envelope e payload bruto, sem tentar impor schema tabular rígido na bronze.
- A V1 não mistura preços e metadados no mesmo dataset.
- A V1 não unifica fundamentals na bronze; isso fica para a silver.
- A V1 trata macroeconomia como dataset independente por indicador.

## Riscos e Cuidados

- Yahoo Finance pode ter variabilidade maior de campos em `info`.
- Alpha Vantage free tem limitação de taxa e alguns endpoints premium.
- ETFs podem não preencher `sector`, `industry` e `country` da mesma forma que equities.
- Alguns payloads podem retornar mensagens de `Note`, `Information` ou `Error Message`; isso deve ser persistido.

## Recomendação de Próximo Passo

Com esta V1, o próximo passo ideal é implementar um writer de bronze local com esta interface lógica:

```python
write_raw_record(
    source="alpha_vantage",
    dataset="fx_daily",
    natural_keys={"from_symbol": "USD", "to_symbol": "BRL"},
    request_params={...},
    request_url="...",
    request_status_code=200,
    raw_payload=payload
)
```

Depois disso, podemos criar:

- `src/clients/`
- `src/ingestion/`
- `src/storage/raw_writer.py`
- `src/contracts/raw_datasets.py`

## Resumo Executivo

A modelagem V1 da bronze layer fica organizada em 9 datasets raw, separados por fonte e domínio de negócio, com particionamento por `source`, `dataset`, chave natural e `ingestion_date`. A decisão principal é manter o payload bruto intacto dentro de um envelope de ingestão padronizado, garantindo rastreabilidade, replay e preparo correto para a camada silver.
