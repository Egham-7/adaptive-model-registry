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
- `GET /healthz` – checks database connectivity and returns health status as JSON.
- `GET /models` – lists all models persisted in Postgres with comprehensive filtering support:

  **Basic Filters:**
  - `author` - Filter by author(s): `?author=openai&author=anthropic`
  - `model_name` - Filter by model name(s): `?model_name=gpt-4&model_name=claude-3`
  - `endpoint_tag` - Filter by endpoint tag(s): `?endpoint_tag=openai&endpoint_tag=anthropic`
  - `provider` - Filter by provider name(s): `?provider=OpenAI`

  **Advanced Filters:**
  - `input_modality` - Filter by input modality: `?input_modality=text&input_modality=image`
  - `output_modality` - Filter by output modality: `?output_modality=text`
  - `min_context_length` - Minimum context window: `?min_context_length=128000`
  - `max_prompt_cost` - Maximum prompt cost: `?max_prompt_cost=0.00001`
  - `max_completion_cost` - Maximum completion cost: `?max_completion_cost=0.00003`
  - `supported_param` - Required parameters: `?supported_param=tools&supported_param=vision`
  - `status` - Endpoint status (0=active): `?status=0`
  - `quantization` - Model quantization: `?quantization=fp16`

  **Examples:**
  ```bash
  # Find OpenAI models with vision support
  GET /models?author=openai&supported_param=vision

  # Find models with 128k+ context under $0.01/1M tokens
  GET /models?min_context_length=128000&max_prompt_cost=0.00001

  # Find active text-to-text models
  GET /models?input_modality=text&output_modality=text&status=0
  ```
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
