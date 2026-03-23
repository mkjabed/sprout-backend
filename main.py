from fastapi import FastAPI
from database import engine, Base
import models

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Sprout API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}