from pydantic import BaseModel
from app.services.simulateurService import SimulateurService
from fastapi import APIRouter

simulateurService = SimulateurService()
simulateurRouter  = APIRouter()

# @simulateurRouter.post("/simulate_volatility/{id}")
# async def simuler_volatilite(id:str, valeur:list):
#     return await simulateurService.simulateur_volatilite(id, valeur)


class VolatiliteRequest(BaseModel):
    valeur: list

class SimulerVarRequest(BaseModel):
    valeur: float

@simulateurRouter.post("/simulate_volatility/{id}")
async def simuler_volatilite(id: str, request: VolatiliteRequest):
    return await simulateurService.simulateur_volatilite(id, request.valeur)

@simulateurRouter.post("/simulate_var/{id}")
async def simuler_var(id: str, request: SimulerVarRequest):
    return await simulateurService.simulateur_var(id, request.valeur)