import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

import crud
import schemas
from crud import get_all_citys, get_all_temperatures_by_city
from db import models
from db.engine import SessionLocal
from db.models import DBCity
from db.engine import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/cities/", response_model=list[schemas.City])
def read_all_cities(db: Session = Depends(get_db)):
    return crud.get_all_citys(db)


@app.get("/temperatures/", response_model=list[schemas.Temperature])
def read_all_temperatures(db: Session = Depends(get_db)):
    cities = get_all_citys(db)
    record_temperetarutre_by_city = []
    for city in cities:
        all_temperatures_by_city = get_all_temperatures_by_city(db, city)
        city_record = 0.0
        for temperature in all_temperatures_by_city:
            if temperature.temperature > city_record:
                city_record = temperature.temperature
                record_temperetarutre_by_city.append(temperature)
    return record_temperetarutre_by_city



@app.get("/temperatures/{city_id}", response_model=schemas.Temperature)
def read_temperature_by_city(city_id: int, db: Session = Depends(get_db)):
    all_temperatures_by_city = crud.get_all_temperatures_by_id_city(db=db, city_id=city_id)
    city_record = 0.0
    need_temperature = None
    for temperature in all_temperatures_by_city:
        if temperature.temperature > city_record:
            city_record = temperature.temperature
            need_temperature = temperature
    return need_temperature

@app.post("/cities/", response_model=schemas.City)
def create_city(
    city: schemas.CityCreate,
    db: Session = Depends(get_db)
) -> DBCity:
    return crud.create_city(db=db, city=city)

@app.delete("/cities/{city_id}", response_model=str)
def delete_city(city_id: int, db: Session = Depends(get_db)):
    crud.delete_city(db=db, city_id=city_id)
    return f"deleted city {city_id}"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/temperatures/update/")
async def update_temps(db: Session = Depends(get_db)):
    cities = db.query(models.DBCity).all()
    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient() as client:
        tasks = [crud.fetch_city_temp(client, city.name) for city in cities]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    updated = 0
    for city, temp in zip(cities, results):
        if temp is None or isinstance(temp, Exception):
            print(f"skip {city.name}: {temp!r}")
            continue

        temp_rec = models.DBTemperature(
            city_id=city.id,
            date_time=now,
            temperature=temp,
        )
        db.add(temp_rec)
        updated += 1

    db.commit()
    return {"updated": updated, "total": len(cities)}
