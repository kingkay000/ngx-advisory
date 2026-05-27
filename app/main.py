from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ngx_advisory_router import router as ngx_router
from database.ngx_advisory_schema import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="NGX Advisory API Engine",
    version="1.0.0",
    description="Independent API Engine for n8n workflows and Zod / NGX Pulse reads.",
    lifespan=lifespan
)

ALLOWED_ORIGINS = [
    "https://ngxpulse.ng",
    "https://www.ngxpulse.ng",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["x-api-key", "Content-Type"],
)

app.include_router(ngx_router)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "NGX Advisory API is live. Access /docs for API documentation."}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
