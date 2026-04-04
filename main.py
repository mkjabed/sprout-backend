from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from auth import router as auth_router
from routers.guardian import router as guardian_router
from routers.children import router as children_router
from routers.tasks import router as tasks_router
from routers.daily import router as daily_router
from routers.rewards import router as rewards_router
from scheduler import start_scheduler

app = FastAPI(title="Sprout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(guardian_router)
app.include_router(children_router)
app.include_router(tasks_router)
app.include_router(daily_router)
app.include_router(rewards_router)

start_scheduler()

@app.get("/")
async def root():
    return {"message": "Sprout API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}