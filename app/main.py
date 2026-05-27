import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ngx_advisory_router import router as ngx_router
from database.ngx_advisory_schema import init_db

# Define the lifespan manager to run before the app accepts requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite database schema tables dynamically
    init_db()
    yield
    # Shutdown logic goes here if needed (e.g., closing connections)

app = FastAPI(
    title="NGX Advisory API Engine",
    version="1.0.0",
    description="Independent API Engine for n8n workflows and Zod / NGX Pulse reads.",
    lifespan=lifespan  # Hook it into FastAPI here
)

# Enable CORS for public reading consumers

ALLOWED_ORIGINS = [
    "https://ngxpulse.ng",
    "https://www.ngxpulse.ng",
    "http://localhost:3000",  # Optional: For developer's local development if needed
    "http://localhost:5173",  # Optional: For Vite/React local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Fixed: False works perfectly with custom API headers
    allow_methods=["GET"],    # Public consumers only need read access
    allow_headers=["x-api-key", "Content-Type"], # Added Content-Type for standard compliance
)

# Build SQLite database schema tables dynamically if they don't exist on boot
@app.on_event("startup")
def on_startup():
    from database.ngx_advisory_schema import init_db
    init_db()

# Register the standalone router
app.include_router(ngx_router)

@app.get("/", include_in_schema=False)
def root():
    return {"message": "NGX Advisory API is live. Access /docs for API documentation."}

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
