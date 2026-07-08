from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base


class AdminUser(Base):
    __tablename__ = "admin_user"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    __tablename__ = "booking"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    location = Column(String(150), nullable=False)
    shoot_type = Column(String(50), nullable=False)
    event_date = Column(String(20))
    message = Column(Text)
    status = Column(String(20), default="New")
    created_at = Column(DateTime, default=datetime.utcnow)


class GalleryItem(Base):
    __tablename__ = "gallery_item"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)
    title = Column(String(150))
    created_at = Column(DateTime, default=datetime.utcnow)
