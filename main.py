from fastapi import FastAPI
from database import engine, Base
import models
from auth import router as auth_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Sprout API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}