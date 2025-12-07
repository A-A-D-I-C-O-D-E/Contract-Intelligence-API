# app/core/config.py
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "data", "uploads")
TEXT_DIR = os.path.join(BASE_DIR, "..", "data", "texts")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "..", "data", "faiss.index")
FAISS_META_PATH = FAISS_INDEX_PATH + ".meta.json"

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", None)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "..", "data"), exist_ok=True)
