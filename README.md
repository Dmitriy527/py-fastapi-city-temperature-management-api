# Temperature Catalog API

A small FastAPI application that stores a list of cities and keeps a history of their
current temperatures. Temperatures are fetched from the free
[Open-Meteo](https://open-meteo.com/) APIs (no API key required) and saved to a local
SQLite database.

## How to run

### 1. Prerequisites

- Python 3.10+ (the code uses the `int | None` type syntax)
- Internet access (needed only for the temperature update endpoint)

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install fastapi "uvicorn[standard]" sqlalchemy alembic httpx pydantic
```

### 3. Apply migrations and start the server

From the project root (the folder containing `main.py`):

```bash
alembic upgrade head
uvicorn main:app --reload
```

The SQLite file `temperature_catalog.db` is created automatically. The database schema is
managed with Alembic; `Base.metadata.create_all` in `main.py` only creates missing tables
on startup.

### 4. Example usage

```bash
# Add a city
curl -X POST http://127.0.0.1:8000/cities/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Kyiv", "additional_info": "Capital of Ukraine"}'

# List cities
curl http://127.0.0.1:8000/cities/

# Fetch the current temperature for all cities and store it
curl -X POST http://127.0.0.1:8000/temperatures/update/

# Highest recorded temperature for every city
curl http://127.0.0.1:8000/temperatures/

# Highest recorded temperature for one city
curl http://127.0.0.1:8000/temperatures/1

# Delete a city (and its temperature history)
curl -X DELETE http://127.0.0.1:8000/cities/1
```

## API overview

| Method | Path                     | Description                                                      |
|--------|--------------------------|------------------------------------------------------------------|
| GET    | `/`                      | Health-check / hello message                                     |
| GET    | `/cities/`               | List all cities                                                  |
| POST   | `/cities/`               | Create a city (`name`, `additional_info`)                        |
| DELETE | `/cities/{city_id}`      | Delete a city and all of its temperature records                 |
| POST   | `/temperatures/update/`  | Fetch current temperatures for all cities and save them          |
| GET    | `/temperatures/`         | Record (highest) temperature for each city                       |
| GET    | `/temperatures/{city_id}`| Record (highest) temperature for a single city                   |

## Design choices

- **FastAPI + SQLAlchemy + SQLite.** FastAPI gives automatic data validation;
  SQLite keeps the project zero-setup (a single file, no database server).
- **Layered structure.** Endpoints live in `main.py`, database and external-API logic in
  `crud.py`, ORM models in `db/models.py`, and request/response validation in
  `schemas.py`. This keeps routes thin and makes each part easy to test or replace.
- **Alembic for migrations.** Database schema changes are versioned and applied with Alembic.
- **Separate Pydantic schemas** (`Base` / `Create` / read model) so that clients never
  send an `id`, while responses always include it. `from_attributes = True` lets
  responses be built directly from ORM objects.
- **Two tables with a foreign key.** `city` (unique name, optional extra info) and
  `temperature` (city_id, timestamp, value). Each update adds a new row, so the
  temperature history is preserved instead of overwritten.
- **Concurrent external calls.** `POST /temperatures/update/` uses `httpx.AsyncClient`
  with `asyncio.gather`, so all cities are fetched in parallel rather than one by one.
  `return_exceptions=True` ensures that one failing city does not break the whole update.
- **Two-step Open-Meteo lookup.** The city name is first converted to coordinates with
  the Open-Meteo Geocoding API, then the current weather is requested for those
  coordinates.
- **One DB session per request** via the `get_db` dependency, which always closes the
  session in a `finally` block.
- **Cascading delete done manually.** Deleting a city first removes its temperature
  rows, then the city itself, so no orphaned records remain.
- **Timestamps in UTC.** `datetime.now(timezone.utc)` is used when saving a measurement.

## Assumptions and simplifications

- **City names are resolved by Open-Meteo's geocoder, taking the first match.**
  Ambiguous names (e.g. "Springfield") may resolve to an unexpected location.
  City names must also be unique in the database.
- **Temperatures are in °C**, as returned by Open-Meteo by default.
- **Temperatures are only collected when `POST /temperatures/update/` is called.** There
  is no background scheduler; call the endpoint manually or from cron to build up history.
- **Failures are skipped silently.** If a city cannot be geocoded or the API request
  fails, that city is skipped (logged with `print`) and the rest are still saved. The
  response reports how many were updated (`updated` / `total`).
- **"Record temperature" means the highest recorded value** for a city across all stored
  measurements.
- **No authentication, pagination, or rate limiting.** All endpoints are public and
  return full lists.
- **No automated tests** are included.
- **SQLite with `check_same_thread=False`** is used for simplicity; for production use
  a server database such as PostgreSQL.
