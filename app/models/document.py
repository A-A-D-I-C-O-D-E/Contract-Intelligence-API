# app/models/document.py
from sqlalchemy import Column, String, Integer, Text, DateTime
from ..db import Base
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    num_pages = Column(Integer, default=0)
    path_pdf = Column(String, nullable=False)
    path_text = Column(String, nullable=False)
