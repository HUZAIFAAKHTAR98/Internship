
from sqlalchemy import Column, Date, Integer, String

from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    course = Column(String(100), nullable=True)
    address = Column(String(250), nullable=True)
    enrollment_date = Column(Date, nullable=True)
