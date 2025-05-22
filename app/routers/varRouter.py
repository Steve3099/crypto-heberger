from app.services.varService import VarService
from fastapi import APIRouter
from datetime import datetime

varService = VarService()
varrouter  = APIRouter()

@varrouter.get("/var")
async def get_var():
    return await varService.get_var_portfeuille()
    return {"message":"var"}

@varrouter.get("/var/{id}/update")
async def update_var_historique(id):
    return await varService.update_var_historique(id)
    return {"message":"var"}

@varrouter.get("/{id}/var/historique")
async def get_var_historique(id):
    return await varService.get_var(id)
    return await varService.get_var_historique_one_crypto(id,date_debut,date_fin)