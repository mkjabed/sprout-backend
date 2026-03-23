from fastapi import FastAPI
from database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/health")
async def health():
    return {"status": "ok"}