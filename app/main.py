from fastapi import FastAPI
from app.routers.cryptorouter import cryptorouter
from fastapi.middleware.cors import CORSMiddleware
import app.scheduler as scheduler

app = FastAPI()

# Include routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with a list of specific origins for production
    allow_credentials=True,
    allow_methods=["*"],  # You can limit this to specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # You can limit this to specific headers if needed
)

@app.get("/")
def read_root():
   return {"message": "Welcome to FastAPI!"}
   
app.include_router(cryptorouter)