# app/core/metrics.py
from threading import Lock

class Metrics:
    def __init__(self):
        self._lock = Lock()
        self.requests = 0
        self.ingest_count = 0
        self.extract_count = 0
        self.ask_count = 0
        self.audit_count = 0

    def inc(self, name: str, n: int = 1):
        with self._lock:
            if hasattr(self, name):
                setattr(self, name, getattr(self, name) + n)

    def get_snapshot(self):
        with self._lock:
            return {
                "requests": self.requests,
                "ingest_count": self.ingest_count,
                "extract_count": self.extract_count,
                "ask_count": self.ask_count,
                "audit_count": self.audit_count
            }

METRICS = Metrics()
