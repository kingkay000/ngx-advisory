FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for SQLite performance management
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Layer 1 Cache: Copy requirements and install them first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2 Cache: Copy the rest of the application files
COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
