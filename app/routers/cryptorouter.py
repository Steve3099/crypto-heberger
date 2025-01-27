import json
import math
from fastapi import APIRouter
from app.services.callApiService import callCoinGeckoListeCrypto,getHistorique,getSimpleGeckoApi
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi

cryptorouter  = APIRouter()
calculService = CalculService()
coinGeckoService = CoinGeckoService()
callCoinMArketApi = CallCoinMarketApi()
@cryptorouter.get("/listeCrypto")
def getListe():
    listeCoin = callCoinGeckoListeCrypto()
    retour = coinGeckoService.excludeStableCoin(listeCoin)
    retour = retour[:10]
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
    listevolatilite = calculService.getListeVolatilite( prices)
    if(len(listevolatilite) >0 ):
        
    
        volatiliteJ = listevolatilite[-1]
        volatiliteJ2 = listevolatilite[-2]
        variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2
    
        volatiliteMois = listevolatilite[-30]
        variationMois = (listevolatilite[-30] - listevolatilite[-31]) / listevolatilite[-31]
        
        # get rank
        detailCrypto = callCoinGeckoListeCrypto(coin)
        ranking = detailCrypto[0].get("market_cap_rank", 0)
        retour = {
            "id":coin,
            "rank":ranking,
            "volatiliteAnnuel" : volatiliteJ * math.sqrt(365),
            "volatiliteJournaliere": volatiliteJ,
            "volatiliteJ1": volatiliteJ2,
            "variationj1": variationJ1,
            "volatiliteMois": volatiliteMois, 
            "variationMois": variationMois,
            "historiquePrice":prices,
            "historiquevolatiliteJournaliere": listevolatilite,
        }
        
        return retour

@cryptorouter.get("/fearAndGreed") 
def getFearAndGreed():
    try:
        fearGred = callCoinMArketApi.getFearAndGreed()
        return fearGred
    except Exception as e:
        return str(e)
    # fearGred = callCoinMArketApi.getFearAndGreed()
    # return fearGred
    
@cryptorouter.get("/listeCryptoVolatilite")    
def getListeCryptoAvecVolatilite():
    listeCrypto = getListe()
    listeVolatilite = calculService.top5volatiliteJournaliere(listeCrypto)
    return listeVolatilite
    

@cryptorouter.get("/top10Volatilite") 
def getTop10VolatiliteJournaliere():
    listeCrypto = getListe()
    retour = calculService.top10volatiliteJournaliere(listeCrypto)
    
    return retour
    
@cryptorouter.get("/top5Bot5") 
def getTop5Corissance():
    listeCrypto = getListe()
    retour = calculService.top5CroissanceDevroissance(listeCrypto)
    
    return retour

@cryptorouter.get("/weights")  
def getListeCryptoAvecPoids():
    listeCrypto = getListe()
    listeWithWeight = coinGeckoService.getListeCryptoWithWeight(listeCrypto)
    # add volatilite to each listeWithWeight
    for el in listeWithWeight:
        resultat = getVolatiliteOneCrypto(el["id"])
        el["volatiliteJournaliere"] = resultat.get("volatiliteJournaliere",0)
        el['variationj1'] = resultat.get("variationj1")
        el["volatiliteAnnuel"] = resultat.get("volatiliteAnnuel")
        
    
    return listeWithWeight

@cryptorouter.get("/GraphWeights")  
def getGraphPoids():
    listeCrypto = getListeCryptoAvecPoids()
    return coinGeckoService.getGraphWeight(listeCrypto)
    
@cryptorouter.get("/VolatiliteGenerale")  
def getvaltilitePortefeuille():
    # obtenir la liste des crypto
    listeCrypto = getListe()
    
    listeCryptowithWeight = coinGeckoService.getListeCryptoWithWeight(listeCrypto)
    listePrix = calculService.getListePrix(listeCryptowithWeight)
    
    # getHistorique volatilite generale 
    historiqueVolatiliteGenerale = calculService.getHistoriqueVolatiliteGenerale(9,listeCryptowithWeight,listePrix)
    # print(historiqueVolatiliteGenerale)
    retour = {
        "volatiliteGenerale": historiqueVolatiliteGenerale[-1],
        "historiqueVolatiliteGenerale": historiqueVolatiliteGenerale
    }
    
    return retour

