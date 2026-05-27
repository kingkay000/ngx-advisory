import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ngx_advisory_router import router as ngx_router, engine

app = FastAPI(
    title="NGX Advisory API Engine",
    version="1.0.0",
    description="Independent API Engine for n8n workflows and Zod / NGX Pulse reads."
)

# Enable CORS for public reading consumers like Zod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
