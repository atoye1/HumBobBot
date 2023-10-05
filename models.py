from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, func
from sqlalchemy.orm import relationship
from database import Base

class Diet(Base):
    __tablename__ = "diets"
    
    id = Column(Integer, primary_key=True)
    img_url = Column(String(length=500), nullable=False)
    img_path = Column(String(length=500), nullable=False)

    post_title = Column(String(length=200), nullable=False)
    post_create_date = Column(DateTime, nullable=False)

    create_date = Column(DateTime, nullable=False,
                         default=func.now())
    update_date = Column(DateTime, nullable=False,
                         default=func.now(),
                         onupdate=func.now())
    start_date = Column(DateTime, nullable=False)

    cafeteria_id = Column(Integer, ForeignKey("cafeterias.id"))
    cafeteria = relationship("Cafeteria", backref="diets")

class Cafeteria(Base):
    __tablename__ = "cafeterias"
    
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
    
class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True)
    title = Column(String(length=100), nullable=False, unique=True)
    create_date = Column(DateTime, nullable=False)
    update_date = Column(DateTime, nullable=False)
    file_url = Column(String(length=200), nullable=False)
    html_url = Column(String(length=200), nullable=True)