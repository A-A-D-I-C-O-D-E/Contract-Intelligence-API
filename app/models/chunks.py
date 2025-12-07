# app/models/chunks.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from ..db import Base

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, index=True)
    page_no = Column(Integer)
    char_start = Column(Integer)
    char_end = Column(Integer)
    text = Column(Text)
