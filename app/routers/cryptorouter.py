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
async def getListe():
    listeCoin = await callCoinGeckoListeCrypto()
    retour = coinGeckoService.excludeStableCoin(listeCoin)
    retour = retour[:10]
    return retour

@cryptorouter.get("/volatilite")
async def getHistoriques():
    #testonBitcoin
    listeCrypto = ["bitcoin","ethereum"]
    listeRetour = []
    for el in listeCrypto:
        
        historique = await getHistorique(coin = el)
        
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
async def getVolatiliteOneCrypto(coin: str = "bitcoin", days: int = 90):
    historique = await getHistorique(coin = coin,days = days)
    
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
        detailCrypto = await callCoinGeckoListeCrypto(coin)
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
async def getFearAndGreed():
    try:
        fearGred = await callCoinMArketApi.getFearAndGreed()
        return fearGred
    except Exception as e:
        return str(e)
    
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
async def getListeCryptoAvecPoids():
    listeCrypto = await getListe()  # Assuming this is an async function
    listeWithWeight = coinGeckoService.getListeCryptoWithWeight(listeCrypto)  # Assuming this is async
    
    # Add volatility to each element in listeWithWeight
    for el in listeWithWeight:
        resultat = await getVolatiliteOneCrypto(el["id"])  # Assuming this is async
        el["volatiliteJournaliere"] = resultat.get("volatiliteJournaliere", 0)
        el["variationj1"] = resultat.get("variationj1")
        el["volatiliteAnnuel"] = resultat.get("volatiliteAnnuel")
    
    return listeWithWeight

@cryptorouter.get("/GraphWeights")  
async def getGraphPoids():
    listeCrypto = await getListeCryptoAvecPoids()
    return coinGeckoService.getGraphWeight(listeCrypto)
    
@cryptorouter.get("/VolatiliteGenerale")  
async def getvaltilitePortefeuille():
    # obtenir la liste des crypto
    listeCrypto = await getListe()
    
    listeCryptowithWeight = coinGeckoService.getListeCryptoWithWeight(listeCrypto)
    listePrix = await calculService.getListePrix(listeCryptowithWeight)
    
    # getHistorique volatilite generale 
    historiqueVolatiliteGenerale = calculService.getHistoriqueVolatiliteGenerale(9,listeCryptowithWeight,listePrix)
    # print(historiqueVolatiliteGenerale)
    retour = {
        "volatiliteGenerale": historiqueVolatiliteGenerale[-1],
        "historiqueVolatiliteGenerale": historiqueVolatiliteGenerale
    }
    
    return retour

@cryptorouter.get("/Comparaison")  
async def comparer2Crypto(crypto1Id = "bitcoin",crypto2Id = "ethereum"):
    listeCrypto = await getListe()
    
    listeFinale = ['','']
    for crypto in listeCrypto:
        if crypto.get("id") == crypto1Id:
            listeFinale[0] = crypto
        elif crypto.get("id") == crypto2Id:
            listeFinale[1] = crypto
    listeFinale = coinGeckoService.getListeCryptoWithWeight(listeFinale)
    historique1 = await getHistorique(coin = crypto1Id)
    historique_data1 = json.loads(historique1)
    prices1 = historique_data1.get("prices", [])
    prices1 = [price[1] for price in prices1]
    # listeVolatilite1 = calculService.getListeVolatilite(prices1)
    # volatilite1 = listeVolatilite1[-1]
    
    historique2 = await getHistorique(coin = crypto2Id)
    historique_data2 = json.loads(historique2)
    prices2 = historique_data2.get("prices", [])
    prices2 = [price[1] for price in prices2]
    # listeVolatilite2 = calculService.getListeVolatilite(prices2)
    # volatilite2 = listeVolatilite2[-1]
    print(listeFinale)
    listePrix = [prices1,prices2]
    volatilite,matriceCovariance = calculService.getvolatilitePortefeuil(listeFinale, listePrix)
    
    retour = {
        "crypto1":crypto1Id,
        # "volatiliteJournaliere1": volatilite1,
        "crypto2":crypto2Id,
        # "volatiliteJournaliere2": volatilite2,
        
        "matricecovarance": matriceCovariance,
    }
    return retour