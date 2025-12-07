# Use Python 3.11 slim
FROM python:3.11-slim

# Prevent .pyc files, force stdout flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker cache)
COPY requirements.txt /app/requirements.txt

# Install compatible numpy first to avoid faiss error
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir numpy==1.26.4

# Install rest of the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the full project
COPY . /app

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
