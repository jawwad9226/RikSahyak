from fastapi import FastAPI, APIRouter
from app.core.config import API_PREFIX, API_VERSION
from app.api.v1 import endpoints, websocket
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="RikSahayak API",
    description="Auto Rickshaw Booking System for Malkapur",
    version=API_VERSION,
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(endpoints.router, prefix=API_PREFIX)
app.include_router(endpoints.admin_router, prefix=API_PREFIX)
app.include_router(endpoints.operator_router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": "RikSahayak",
        "version": API_VERSION,
        "status": "running",
        "message": "Welcome to RikSahayak API",
    }


@app.get("/health")
async def health():
    """Health check for monitoring"""
    return {"status": "healthy"}


@app.get(f"{API_PREFIX}/health")
async def api_health():
    """Health check for API - at /api/v1/health"""
    return {"status": "healthy", "api_version": API_VERSION}


@app.get(f"{API_PREFIX}/status")
async def api_status():
    """Check API status"""
    return {
        "api_version": API_VERSION,
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
