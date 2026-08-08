# Vetty Crypto Market API

Async Python REST API built for the Vetty Python API Technical Exercise. It fetches
cryptocurrency market data from the [CoinGecko API](https://www.coingecko.com/en/api),
built with **FastAPI** and asynchronous HTTP calls via `httpx`.

## Requirements covered

- Python 3.12 (3.10+ required)
- Health, coins, categories, and market-data endpoints
- API-key authentication on every endpoint except `/health`
- Pagination (`page_num`, `per_page`) on all list endpoints
- Async CoinGecko integration via `httpx`
- Environment-based configuration (`pydantic-settings` + `.env`)
- In-memory, configurable TTL cache (default 60s)
- Webhook notification on non-cached market-data fetches
- Centralized exception handling with consistent error responses
- Structured (JSON) logging
- OpenAPI/Swagger documentation
- Unit and integration tests (pytest, 99% coverage)
- Ruff linting
- Dockerfile

## Project structure

```
vetty-crypto-api-task/
├── app/
│   ├── controller/controller.py   # FastAPI app, routes, exception handlers
│   ├── dependencies.py            # X-API-Key auth dependency
│   ├── exceptions.py              # ExternalServiceError / ExternalServiceTimeout
│   ├── logging_config.py          # structured JSON logging
│   ├── models/models.py           # Pydantic response models
│   ├── services/crypto_services.py  # caching + webhook orchestration
│   └── utils/
│       ├── cache.py               # in-memory TTL cache
│       ├── coingecko.py           # async CoinGecko HTTP client
│       └── webhook.py             # webhook POST notifier
├── config.py                      # pydantic-settings config
├── manage.py                      # local entrypoint (uvicorn + reload)
├── tests/                         # pytest suite
├── requirements.txt               # runtime dependencies
├── requirements-dev.txt           # + test/lint tooling
├── Dockerfile
└── .env.example
```

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Set a real `API_KEY` in `.env` (used to authenticate `/coins`, `/categories`,
`/markets`). `COINGECKO_API_KEY` and `WEBHOOK_URL` are optional — CoinGecko's
public endpoints work without a key, and if `WEBHOOK_URL` is unset the webhook
notifier silently no-ops.

Run:

```bash
python manage.py
```

Swagger UI: `http://localhost:8000/docs` (port comes from `settings.port`, default 8000).

## API

### Health

`GET /health` — no authentication required.

```json
{
  "status": "healthy",
  "application_version": "1.0.0",
  "cryptocurrency_service": "reachable",
  "cryptocurrency_service_version": null
}
```

### Coins

`GET /coins?page_num=1&per_page=10`
Header: `X-API-Key: <API_KEY>`

Returns paginated `{ id, name, symbol }` records for every CoinGecko coin.

### Categories

`GET /categories?page_num=1&per_page=10`
Header: `X-API-Key: <API_KEY>`

Returns paginated `{ id, name }` records for every CoinGecko category.

### Market data

`GET /markets?coin_id=bitcoin`
`GET /markets?category=decentralized-finance-defi`
`GET /markets?coin_id=bitcoin&category=decentralized-finance-defi`
Header: `X-API-Key: <API_KEY>`

At least one of `coin_id` / `category` is required (`400 VALIDATION_ERROR` otherwise).
Prices are returned in CAD. A successful, non-cached fetch fires a webhook POST to
`WEBHOOK_URL` with `{ event: "market_data_retrieved", source, coin_id, category }`.

### Pagination

All list endpoints accept `page_num` (default `1`) and `per_page` (default `10`,
max `100`) and respond with:

```json
{ "page_num": 1, "per_page": 10, "total": 123, "data": [...] }
```

### Errors

Responses use consistent shapes. Client errors (`400`, `401`, `422`) return
`{"detail": {"code": ..., "message": ...}}`; upstream/server failures return
`{"error": {"code": ..., "message": ...}}`:

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | `/markets` called without `coin_id` or `category` |
| 401 | `UNAUTHORIZED` | missing/invalid `X-API-Key` |
| 422 | — | query params fail validation (e.g. `per_page` > 100) |
| 502 | `EXTERNAL_SERVICE_ERROR` | CoinGecko returned an error |
| 504 | `EXTERNAL_TIMEOUT` | CoinGecko request timed out |
| 500 | `INTERNAL_SERVER_ERROR` | anything unhandled |

## Configuration

All settings are read via `pydantic-settings` from environment variables / `.env`
(see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `8000` | bind address |
| `API_KEY` | `change-me` | required `X-API-Key` value for protected endpoints |
| `COINGECKO_BASE_URL` | CoinGecko public API | upstream base URL |
| `COINGECKO_API_KEY` | unset | optional CoinGecko key |
| `COINGECKO_TIMEOUT_SECONDS` | `5` | upstream request timeout |
| `CACHE_TTL_SECONDS` | `60` | in-memory cache TTL |
| `WEBHOOK_URL` | unset | webhook target for market-data notifications |
| `WEBHOOK_TIMEOUT_SECONDS` | `3` | webhook POST timeout |
| `LOG_LEVEL` | `INFO` | root logger level |

`.env` is git-ignored; never commit real secrets.

## Testing

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov=config --cov-report=term-missing
```

33 tests, 99% coverage. External CoinGecko calls are mocked at the `httpx`/
`CoinGeckoClient` boundary — the suite never hits the real network.

## Linting

```bash
ruff check .
```

## Docker

```bash
docker build -t vetty-crypto-api-task .
docker run -d -p 8000:8000 --env-file .env vetty-crypto-api-task
```

Secrets are never baked into the image — they're injected at `docker run` time via
`--env-file`.
