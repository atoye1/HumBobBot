from typing import List
import datetime
from sqlalchemy.orm import Session

from models import Cafeteria

def get_cafeteria_id(db: Session, location: str) -> int:
    cafeteria = db.query(Cafeteria).filter_by(location = location).one()
    return cafeteria.id

def get_operation_times(db:Session, cafeteria_id: int) -> List[datetime.datetime]:
    cafeteria : Cafeteria = db.query(Cafeteria).get(cafeteria_id).one()
    return [cafeteria.breakfast_start_time, cafeteria.breakfast_end_time,
            cafeteria.lunch_start_time, cafeteria.lunch_end_time,
            cafeteria.dinner_start_time, cafeteria.dinner_end_time]