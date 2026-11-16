from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import (
    auth_router,
    menu_router,
    feedback_router,
    complaints_router,
    polls_router,
    suggestions_router,
    dashboard_router
)

app = FastAPI(
    title="HostelHub API",
    description="Smart Hostel Management System - REST API for Weekly Menu, Feedback, Complaints, Polls, Suggestions, and Admin Dashboard.",
    version="1.0.0"
)

# Enable CORS for local and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(menu_router.router)
app.include_router(feedback_router.router)
app.include_router(complaints_router.router)
app.include_router(polls_router.router)
app.include_router(suggestions_router.router)
app.include_router(dashboard_router.router)

@app.get("/")
async def root():
    return {
        "app": "HostelHub API",
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
