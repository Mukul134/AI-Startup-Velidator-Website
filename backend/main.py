import os
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import init_db
from app.routers import projects_router, public_router, payments_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API orchestrating LangGraph multi-agent startup validations.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from an absolute path so downloads work regardless of launch cwd.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register Routers
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(public_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)

# Database Startup Event
@app.on_event("startup")
async def startup_event():
    await init_db()

# --- Custom Global Error Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback handler to prevent raw traces escaping to user UI."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred processing your request.",
            "error_type": exc.__class__.__name__
        }
    )

@app.get("/health", tags=["health"])
async def health_check():
    """Simple API status query endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
