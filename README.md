# Adaptive Model Registry

Postgres-backed [Fiber](https://gofiber.io) service written in Go 1.25 for registering model metadata.

## Prerequisites

- Go 1.25 or newer
- Postgres instance reachable via a DSN string

## Environment

The service reads the connection string from `DATABASE_URL`, for example:

```bash
export DATABASE_URL='postgres://user:pass@localhost:5432/adaptive_models?sslmode=disable'
```

## Run locally

```bash
cd adaptive-model-registry
go mod tidy           # downloads Fiber, GORM, and the Postgres driver
go run ./cmd/api
```

The server listens on `http://localhost:3000`.

### API

- `GET /` – service metadata and docs link.
- `GET /healthz` – checks database connectivity and returns `200 OK`.
- `GET /models` – lists all models persisted in Postgres; supports optional `provider`, `model_name`, and `openrouter_id` query parameters for filtering.
- `GET /models/:name` – fetches the first model matching `model_name` (names may appear under multiple providers).
- `GET /models/openrouter/:id` – fetches a model by its canonical `openrouter_id`.
- `POST /models` – inserts or updates a model (upsert on `model_name`). Example body:

```json
{
  "model_name": "openai/gpt-5-pro-2025-10-06",
  "openrouter_id": "gpt-5-pro-2025-10-06",
  "provider": "openai",
  "display_name": "OpenAI: GPT-5 Pro",
  "description": "Latest OpenAI frontier model",
  "context_length": 400000,
  "pricing": {
    "prompt": "0.000015",
    "completion": "0.00012"
  },
  "architecture": {
    "modality": "text+image->text"
  },
  "supported_parameters": [
    "max_tokens",
    "tools"
  ],
  "default_parameters": {
    "temperature": null
  },
  "endpoints": [
    {
      "name": "OpenAI | openai/gpt-5-pro-2025-10-06",
      "provider_name": "OpenAI"
    }
  ]
}
```
