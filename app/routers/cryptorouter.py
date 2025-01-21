import json
import math
from fastapi import APIRouter
from app.services.callApiService import callCoinGeckoListeCrypto,getHistorique,getSimpleGeckoApi
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService

cryptorouter  = APIRouter()
calculService = CalculService()
coinGeckoService = CoinGeckoService()
@cryptorouter.get("/listeCrypto")
def getListe():
    
    listeCoin = callCoinGeckoListeCrypto()

    retour = coinGeckoService.excludeStableCoin(listeCoin)
    
    return retour
@cryptorouter.get("/volatilite")
def getHistoriques():
    #testonBitcoin
    listeCrypto = ["bitcoin","ethereum"]
    listeRetour = []
    for el in listeCrypto:
        
        historique = getHistorique(coin = el)
        
        historique_data = json.loads(historique)
        
        # Extract prices
        prices = historique_data.get("prices", [])
        
        #calcul volatilite
        volatilite = calculService.calculVolatilliteJournaliere(5, prices)
        
        retour = {
            "id":el,
            "volatiliteJournaliere": volatilite,
            "historiquePrice": prices,
            "volatiliteAnnuel" : volatilite * math.sqrt(365)
        }
        listeRetour.append(retour)
    
    return listeRetour

@cryptorouter.get("/infoCripto")
def getSimpleListe():
    return getSimpleGeckoApi()

@cryptorouter.get("/VolatiliteOneCripto")
def getVolatiliteOneCrypto(coin: str = "bitcoin", days: int = 90):
    historique = getHistorique(coin = coin,days = days)
    
    historique_data = json.loads(historique)
        
    # Extract prices 
    prices = historique_data.get("prices", [])
    # Extract only the second value in each list
    prices = [price[1] for price in prices]

    # liste volatilite
    listevolatilite = calculService.getListeVolatilite(days, prices)
    
    volatiliteJ = listevolatilite[0]
    volatiliteJ2 = listevolatilite[1]
    variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2
    
    volatiliteMois = listevolatilite[59]
    variationMois = (listevolatilite[59] - listevolatilite[29]) / listevolatilite[29]
    
    retour = {
        "id":coin,
        "volatiliteAnnuel" : volatiliteJ * math.sqrt(365),
        "volatiliteJournaliere": volatiliteJ,
        "volatiliteJ1": volatiliteJ2,
        "variationj1": variationJ1,
        "volatiliteMois": volatiliteMois, 
        "variationMois": variationMois,
        "historiquevolatiliteJournaliere": listevolatilite,
    }
    
    return retour
    
    
    
    
    