from typing import List
import datetime
from models import Cafeteria
from sqlalchemy.orm import Session

def get_cafeteria_id(db: Session, utterance: str) -> int:
    cafeteria = db.query(Cafeteria).filter_by(Cafeteria.location == utterance).one()
    return cafeteria.id

def get_operation_times(db:Session, cafeteria_id: int) -> List[datetime.datetime]:
    cafeteria : Cafeteria = db.query(Cafeteria).get(cafeteria_id).one()
    return [cafeteria.breakfast_start_time, cafeteria.breakfast_end_time,
            cafeteria.lunch_start_time, cafeteria.lunch_end_time,
            cafeteria.dinner_start_time, cafeteria.dinner_end_time]