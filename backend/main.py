from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, sync_engine
from app.api.v1.interviews import router as interviews_router
from app.api.v1.auth import router as auth_router

# Create database tables on startup
Base.metadata.create_all(bind=sync_engine)
print("✓ Database connected and tables created")

# Create FastAPI app
app = FastAPI(
    title="AI Interview Platform",
    description="AI-powered interview platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(interviews_router)


@app.get("/")
async def root():
    return {"message": "AI Interview Platform", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

