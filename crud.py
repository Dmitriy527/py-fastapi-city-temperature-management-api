from collections.abc import Sequence

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