from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

import crud
import schemas
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


@app.post("/cities/", response_model=schemas.City)
def create_city(
    city: schemas.CityCreate,
    db: Session = Depends(get_db)
) -> DBCity:
    return crud.create_city(db=db, city=city)

@app.get("/")
async def root():
    return {"message": "Hello World"}
