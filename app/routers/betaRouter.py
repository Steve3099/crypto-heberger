from app.services.betaService import BetaService
from fastapi import APIRouter
from datetime import datetime

betaService = BetaService()
betarouter  = APIRouter()

@betarouter.get("/{id}/beta")
async def get_beta(id):
    return await betaService.get_beta_on_crypto(id)
    return {"message":"beta"}
