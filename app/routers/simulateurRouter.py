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
    id: str
    
class CryptoSimulationRequest(BaseModel):
    id: str
    periode: int = 90
    nombre_simulation: int = 20

@simulateurRouter.post("/simulate_volatility/{id}")
async def simuler_volatilite(id: str, request: VolatiliteRequest):
    return await simulateurService.simulateur_volatilite(id, request.valeur)

@simulateurRouter.post("/simulate_var")
async def simuler_var(request: SimulerVarRequest):
    
    value = await simulateurService.simulate_var(request.id)
    return value

@simulateurRouter.post("/simulate_crypto_price")
async def simulate_crypto_price(request: CryptoSimulationRequest):
    return await simulateurService.run_similation_cupro_price(
        request.id, request.periode, request.nombre_simulation
    )
    
@simulateurRouter.get("/simulate_loss/{id}")
async def simulate_loss(id: str,quantite:float = 100):
    return await simulateurService.simulation_potential_loss(id,quantite)