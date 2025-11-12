# OpenRouter Model Registry Setup

This package provides a modular pipeline for syncing OpenRouter models to a PostgreSQL database with full ZDR (Zero Downtime Routing) support.

## Architecture

The codebase has been refactored from a monolithic 1921-line file into a clean, modular structure:

```
setup/
├── __init__.py              # Main entry point with CLI
├── models/                  # Pydantic and SQLAlchemy models
│   ├── database.py         # SQLAlchemy database models
│   ├── openrouter.py       # OpenRouter API models
│   └── zdr.py              # ZDR endpoint models
├── fetchers/                # API data fetching
│   ├── cache.py            # Caching utilities
│   ├── openrouter.py       # OpenRouter API client
│   └── zdr.py              # ZDR API client
├── updaters/                # Database update functions
│   ├── architecture.py     # Architecture updates
│   ├── endpoints.py        # Endpoint updates
│   ├── llm_models.py       # Core model updates
│   ├── parameters.py       # Parameter updates
│   ├── pricing.py          # Pricing updates
│   └── providers.py        # Provider updates
├── inserters/               # Database insertion logic
│   └── bulk_insert.py      # New model insertion
└── utils/                   # Utilities
    ├── exports.py          # Data export functions
    └── validation.py       # Parameter validation
```

## Usage

### Command Line

```bash
# Run the sync pipeline
python -m setup --db-url postgresql://user:pass@host:5432/dbname

# Export data to files
python -m setup --db-url postgresql://user:pass@host:5432/dbname \
    --output-json models.json \
    --output-parquet models.parquet \
    --output-csv models.csv

# Skip cache and fetch fresh data
python -m setup --db-url postgresql://user:pass@host:5432/dbname --no-cache
```

### Programmatic Usage

```python
from setup import main_async

# Run the sync pipeline
await main_async(
    db_url="postgresql://user:pass@host:5432/dbname",
    output_json="models.json",
    no_cache=False
)
```

## Features

- **Full ZDR Support**: Zero Downtime Routing endpoint pricing and metadata
- **24-hour Caching**: Efficient API usage with automatic cache invalidation
- **Type Safety**: Strict Pydantic models and SQLAlchemy ORM
- **Modular Design**: Clean separation of concerns for easy maintenance
- **Smart Updates**: Only updates fields that have meaningful values
- **Parallel Processing**: Concurrent API requests for optimal performance
- **Data Exports**: JSON, Parquet, and CSV export capabilities

## Dependencies

- httpx (async HTTP client)
- sqlalchemy[asyncio] (database ORM)
- asyncpg (PostgreSQL driver)
- pydantic (data validation)
- polars (data processing)

## Migration from Legacy Script

The old `sync_openrouter_models.py` has been replaced by this modular package. All functionality is preserved, including:

- All 9 update functions with type-safe null checking
- ZDR integration with pricing precedence
- Bulk insertion with duplicate handling
- 24-hour caching for all API endpoints
- CLI interface compatibility

To migrate:
1. Replace `python sync_openrouter_models.py` with `python -m setup`
2. All command-line arguments remain the same
3. Functionality is identical