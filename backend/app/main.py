from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, routes
from app.core.config import settings
from app.data.seed import seed
from app.infrastructure.database import Base, SessionLocal, engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(routes.router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
