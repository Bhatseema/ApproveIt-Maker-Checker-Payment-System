
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
from app.config import USERS_FILE
from app.models import User
from app.routers.payments import router as payments_router


def seed_users():
    if not USERS_FILE.exists():
        raise RuntimeError(f"Users file not found: {USERS_FILE}")

    with USERS_FILE.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    # Load users from the candidate pack
    users = payload["users"] if isinstance(payload, dict) else payload

    with SessionLocal() as db:
        for item in users:
            user_id = item.get("id", item.get("user_id"))

            existing = db.get(User, user_id)

            if existing:
                existing.name = item["name"]
                existing.roles = item["roles"]
            else:
                db.add(
                    User(
                        user_id=user_id,
                        name=item["name"],
                        roles=item["roles"]
                    )
                )

        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_users()
    yield


app = FastAPI(
    title="ApproveIt - Maker Checker Payment Approval Service",
    description="A simulated payment approval workflow with maker-checker controls and audit trail.",
    version="1.0.0",
    lifespan=lifespan
)


# Register payment API routes
app.include_router(payments_router)


# Frontend folder path
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# Serve the frontend at /ui
app.mount(
    "/ui",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)


@app.get("/")
def root():
    return {
        "message": "ApproveIt API is running",
        "docs": "/docs",
        "frontend": "/ui/"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
