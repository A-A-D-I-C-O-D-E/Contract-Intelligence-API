# app/core/logger.py
import logging
logger = logging.getLogger("contract_intel")
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
logger.setLevel(logging.INFO)
