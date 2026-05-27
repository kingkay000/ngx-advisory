FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for SQLite performance management
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install required framework dependencies directly
RUN pip install --no-cache-dir \
    fastapi>=0.110.0 \
    uvicorn[standard]>=0.28.0 \
    sqlalchemy>=2.0.0 \
    pydantic>=2.0.0

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]