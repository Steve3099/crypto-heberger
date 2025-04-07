from fastapi import APIRouter
from datetime import datetime
import numpy as np
from app.services.voaltiliteService import VolatiliteService
from app.services.cryptoService import CryptoService
volatiliterouter  = APIRouter()
volatiliteService = VolatiliteService()
cryptoService = CryptoService()

@volatiliterouter.get("/volatilite/generale/historique")
async def get_historique_volatilite_generale(date_start ="2024-11-25T00:00:00.000", date_end =None):
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    
    return await volatiliteService.get_historique_volatilite_from_json(date_start, date_end)

@volatiliterouter.get("/volatilite/generale")
async def get_volatilite_generale():
    return await volatiliteService.get_last_volatilite_from_json()

@volatiliterouter.get("/volatilite/{id}/data")
async def get_Data_volatilite_one_crypto(id):
    date_start="2024-11-29T00:00:00.000"
    date_end= None
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    
    historique_volatilite = await volatiliteService.get_historique_volatilite_crypto_from_json(id,date_start,date_end)
    
    ranking = await cryptoService.get_crypto_rankings(id)  
    
    volatiliteJ = historique_volatilite[-1]["value"]
    volatiliteAnuel = volatiliteJ * np.sqrt(365)
    
    volatiliteJ2 = historique_volatilite[-2]["value"]
    variationJ1 = (volatiliteJ/volatiliteJ2) -1
    
    volatiliteJ7 = historique_volatilite[-8]["value"]
    variationJ7 = (volatiliteJ/volatiliteJ7)-1
    
    volatiliteMois = historique_volatilite[-31]["value"]
    variationMois = (volatiliteJ/volatiliteMois) -1
    
    retour = {
            "id":id,
            "rank":ranking,
            "volatiliteAnnuel" : volatiliteAnuel,
            "volatiliteJournaliere": volatiliteJ,
            "volatiliteJ1": volatiliteJ2,
            "variationj1": variationJ1,
            "volatiliteJ7": volatiliteJ7, 
            "variationj7": variationJ7,
            "volatiliteMois": volatiliteMois, 
            "variationMois": variationMois
        }
    
    return retour

@volatiliterouter.get("/volatilite/{id}/history")
async def get_historique_volatilite_one_crypto(id,date_start="2024-11-29T00:00:00.000",date_end= None):
    
    # check date format
    try:
        datetime.strptime(date_start, "%Y-%m-%dT%H:%M:%S.%f")
        #datetime.strptime(date_end, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return {"error": "Invalid date format for date_start or date end. Use YYYY-MM-DDTHH:MM:SS.sss"}
    
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    historique_volatilite = await volatiliteService.get_historique_volatilite_crypto_from_json(id,date_start,date_end)
    return historique_volatilite

@volatiliterouter.get("/volatilite/top10")
async def get_top10_volatilite():
    return await volatiliteService.get_top_10_volatilite_crypto()

@volatiliterouter.get("/volatilite/generale/annuel/historique")
async def get_historique_volatilite_generale():
    return await volatiliteService.get_volatilite_annuel_data()

@volatiliterouter.get("/volatiliteAnnuel/{id}/historique")
async def get_historique_volatilite_annuel_one_crypto(id,date_start,date_end):
    return await volatiliteService.get_volatilite_annuel_for_one_crypto(id,date_start,date_end)