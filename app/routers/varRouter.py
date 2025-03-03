from app.services.varService import VarService
from fastapi import APIRouter

varService = VarService()
varrouter  = APIRouter()

@varrouter.get("/var")
async def get_var():
    return await varService.get_var_portfeuille()
    return {"message":"var"}