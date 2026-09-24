from collections.abc import Sequence

import httpx
from sqlalchemy.orm import Session

import schemas
from db import models


def get_all_citys(db: Session) -> Sequence[models.DBCity]:
    return db.query(models.DBCity).all()

def create_city(db: Session, city: schemas.CityCreate) -> models.DBCity:
    db_city = models.DBCity(
        name=city.name,
        additional_info=city.additional_info,
    )
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

def delete_city(db: Session, city_id: int) -> None:
    db_city = db.query(models.DBCity).filter(models.DBCity.id == city_id).first()
    db.delete(db_city)
    db.commit()
    return


def get_all_temperatures(db: Session) -> Sequence[models.DBTemperature]:
    return db.query(models.DBTemperature).all()


async def fetch_city_temp(client, city):
    # 1. Get coordinates by city name
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    geocoding_params = {
        "name": city,
        "count": 1,
    }
    try:
        response = await client.get(
            geocoding_url,
            params=geocoding_params,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []

        if not results:
            return None

        longitude = results[0].get("longitude")
        latitude = results[0].get("latitude")

        if latitude is None or longitude is None:
            return None

    # 2. Get temperature by coordinates
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true"
        }
        response = await client.get(
            weather_url,
            params=weather_params,
        )
        response.raise_for_status()
        data = response.json()
        temperature = data.get("current_weather").get("temperature")

        if temperature is None:
            return None

        return temperature
    except httpx.HTTPError:
        return None
