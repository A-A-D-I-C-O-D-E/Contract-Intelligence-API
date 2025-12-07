# app/db.py
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data/meta.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db():
    from .models.document import Document
    from .models.chunks import Chunk
    Base.metadata.create_all(bind=engine)

# initialize at import
init_db()
