from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .webhooks import router as webhooks_router
from .analytics import router as analytics_router

app = FastAPI(
    title="DeepTrace API",
    description="CI/CD failure intelligence platform API",
    version="0.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks_router)
app.include_router(analytics_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to DeepTrace API",
        "status": "healthy"
    }
