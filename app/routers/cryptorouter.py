import json
import math
from xmlrpc.client import DateTime
from app.services.cryptoService import CryptoService
import numpy as np
from fastapi import APIRouter
from app.services.callApiService import getHistorique,getSimpleGeckoApi
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.indexService import IndexService
from app.services.voaltiliteService import VolatiliteService
from datetime import datetime

from fastapi import HTTPException

cryptorouter  = APIRouter()
calculService = CalculService()
coinGeckoService = CoinGeckoService()
callCoinMArketApi = CallCoinMarketApi()
indexService = IndexService()
volatiliteService = VolatiliteService()
cryptoService = CryptoService()
@cryptorouter.get("/listeCrypto")
async def getListe():
    retour = await cryptoService.get_liste_crypto_from_json()
    # retour = await coinGeckoService.get_liste_crypto_filtered()
    # retour = retour[:80]
    # retour = await coinGeckoService.get_liste_crypto(page = 1)
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
async def getVolatiliteOneCrypto(coin: str = "bitcoin", vs_currency='usd' ,days: int = 90):
    
    raise HTTPException(status_code=403, detail=f"this end point was abandoned and not working anymore")

@cryptorouter.get("/fearAndGreed") 
async def getFearAndGreed():
    try:
        fearGred = await callCoinMArketApi.getFearAndGreed()
        return fearGred
    except Exception as e:
        return str(e)
    
@cryptorouter.get("/listeCryptoVolatilite")    
async def getListeCryptoAvecVolatilite():
    listeCrypto = await getListe()
    listeVolatilite = calculService.top5volatiliteJournaliere(listeCrypto)
    return listeVolatilite
    

@cryptorouter.get("/top10Volatilite") 
async def getTop10VolatiliteJournaliere(vs_currency = 'usd', days ='90'):
    liste_crypto = await getListe()
    liste_prix = []
    for el in liste_crypto:
        historique = coinGeckoService.get_historical_prices(el.get('id'),vs_currency, days)
        liste_prix.append(historique)
    
    retour = []
    for i in range(len(liste_crypto)):
        volatiliteJournaliere = calculService.calculVolatilliteJournaliere(liste_prix[i])
        volatiliteAnnuel = volatiliteJournaliere * math.sqrt(365)
        retour.append({
            "coin":liste_crypto[i],
            "volatiliteJournaliere": volatiliteJournaliere,
            "volatiliteAnnuel": volatiliteAnnuel
        })
    # trier la liste decroissant selon la volatilite journaiere
    retour.sort(key=lambda x: x.get("volatiliteJournaliere",0),reverse=True)
    
    return retour[:10]
    
@cryptorouter.get("/top5Bot5") 
async def getTop5Corissance():
    listeCrypto = await getListe()
    retour = await calculService.top5CroissanceDevroissance(listeCrypto)
    return retour

@cryptorouter.get("/weights")  
async def getListeCryptoAvecPoids():
    val =await coinGeckoService.get_liste_crypto_with_weight()
    #  order val by weight descending
    val.sort(key=lambda x: x.get("weight",0),reverse=True)
    
    return val
    

@cryptorouter.get("/GraphWeights")  
async def getGraphPoids():
    listeCrypto = await getListeCryptoAvecPoids()
    return coinGeckoService.getGraphWeight(listeCrypto)

@cryptorouter.get("/Comparaison")  
async def comparer2Crypto(crypto1Id = "bitcoin",crypto2Id = "ethereum",vs_currency = "USD",days= 90):
    listeCrypto = await getListe()
    
    liste_crypto = ['','']
    for crypto in listeCrypto:
        if crypto.get("id") == crypto1Id:
            liste_crypto[0] = crypto
        elif crypto.get("id") == crypto2Id:
            liste_crypto[1] = crypto
    liste_prix = []
    for el in liste_crypto:
        historique = coinGeckoService.get_historical_prices(el.get('id'),vs_currency, days)
        liste_prix.append(historique)
    # return 0
    # get liste_weight
    liste_market_cap =[]
    for el in liste_crypto:
        market_cap = await coinGeckoService.get_market_cap(el.get("id"))
        liste_market_cap.append(market_cap)
        
    liste_weight = calculService.normalize_weights(liste_market_cap)
    liste_weight = calculService.round_weights(liste_weight)
    
    
    liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculService.calculate_statistics(liste_prix,liste_crypto,liste_weight)
    correlation_matrix = calculService.calculate_correlation_matrix(covariance_matrix)
    retour = {
        "matricecorrelation": correlation_matrix,
    }
    return retour

# api to get the index csv 
@cryptorouter.get("/index")
def getIndex():
    index = indexService.get_csv_index()
    return index

@cryptorouter.get("/stablecoin")
async def stablecoin():
    return await callCoinMArketApi.get_liste_stablecoins()

@cryptorouter.get("/grapheIndex")
async def grapheIndex(date_start="2025-02-18 09:19:33", date_end=None):
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return await indexService.get_liste_index_from_json_file(date_start, date_end)

@cryptorouter.get("/liste/nofilter")
async def getListeNoFilter():
    return await coinGeckoService.get_liste_crypto_nofilter()

@cryptorouter.get("/{id}/info")
async def get_info_crypto(id: str):
    return await cryptoService.get_on_crypto_from_liste_json(id)

    