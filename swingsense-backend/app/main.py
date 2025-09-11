from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, me, questions, plans, progress, resources

def create_app() -> FastAPI:
    app = FastAPI(
        title="SwingSense Backend",
        description="FastAPI backend for SwingSense application",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(me.router, prefix="/me", tags=["user"])
    app.include_router(questions.router, prefix="/questions", tags=["questions"])
    app.include_router(plans.router, prefix="/plans", tags=["plans"])
    app.include_router(progress.router, prefix="/progress", tags=["progress"])
    app.include_router(resources.router, prefix="/resources", tags=["resources"])
    
    @app.get("/")
    def root():
        return {"message": "SwingSense backend is running!"}


    return app

app = create_app()
