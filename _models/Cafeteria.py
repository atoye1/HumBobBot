from sqlalchemy import Column, Integer, String, DateTime, Time, func
from database import Base 

class Cafeteria(Base):
    __tablename__ = "cafeteria"
    
    id = Column(Integer, primary_key=True)

    address = Column(String(length=200), nullable=False)
    location = Column(String(length=50), nullable=False)
    phone = Column(String(length=50), nullable=True)

    create_date = Column(DateTime, nullable=False,
                         default=func.now())
    update_date = Column(DateTime, nullable=False,
                         default=func.now(),
                         onupdate=func.now())

    breakfast_start_time = Column(Time, nullable=True)
    breakfast_end_time = Column(Time, nullable=True)
    lunch_start_time = Column(Time, nullable=True)
    lunch_end_time = Column(Time, nullable=True)
    dinner_start_time = Column(Time, nullable=True)
    dinner_end_time = Column(Time, nullable=True)