from fastapi import FastAPI
from app.routers.cryptorouter import cryptorouter


app = FastAPI()

# Include routers

@app.get("/")
def read_root():
   return {"message": "Welcome to FastAPI!"}
   
app.include_router(cryptorouter)