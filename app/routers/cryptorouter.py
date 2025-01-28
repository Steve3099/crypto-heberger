import json
import math
import numpy as np
from fastapi import APIRouter
from app.services.callApiService import getHistorique,getSimpleGeckoApi
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi

cryptorouter  = APIRouter()
calculService = CalculService()
coinGeckoService = CoinGeckoService()
callCoinMArketApi = CallCoinMarketApi()
@cryptorouter.get("/listeCrypto")
def getListe():
    listeCoin = coinGeckoService.callCoinGeckoListeCrypto()
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
def getVolatiliteOneCrypto(coin: str = "bitcoin", vs_currency='usd' ,days: int = 90):
    
    historique = coinGeckoService.get_historical_prices(coin,vs_currency, days)
    
    # volatilite journaliere
    # volatilite = calculService.calculVolatilliteJournaliere(historique)
    
    # historique volatilite journlaiere
    liste_volatilite = calculService.getListeVolatilite(historique)
    
    volatiliteJ = liste_volatilite[0]
    volatiliteJ2 = liste_volatilite[1]
    variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2

    volatiliteMois = liste_volatilite[30]
    variationMois = (liste_volatilite[30] - liste_volatilite[60]) / liste_volatilite[60]
    
    # get rank
    detailCrypto = coinGeckoService.callCoinGeckoListeCrypto(coin)
    ranking = detailCrypto[0].get("market_cap_rank", 0)
    
    
    retour = {
            "id":coin,
            "rank":ranking,
            "volatiliteAnnuel" : volatiliteJ * np.sqrt(365),
            "volatiliteJournaliere": volatiliteJ,
            "volatiliteJ1": volatiliteJ2,
            "variationj1": variationJ1,
            "volatiliteMois": volatiliteMois, 
            "variationMois": variationMois,
            # "historiquePrice":historique,
            "historiquevolatiliteJournaliere": liste_volatilite,
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
def getListeCryptoAvecPoids():
    listeCrypto = getListe()
    liste_market_cap =[]
    for el in listeCrypto:
        market_cap = coinGeckoService.get_market_cap(el.get("id"))
        liste_market_cap.append(market_cap)
        
    liste_weight = calculService.normalize_weights(liste_market_cap)
    
    # listeWithWeight = coinGeckoService.getListeCryptoWithWeight(listeCrypto)
    # add volatilite to each listeWithWeight
    for i in range(len(listeCrypto)):
        resultat = getVolatiliteOneCrypto(listeCrypto[i]["id"])
        listeCrypto[i]["volatiliteJournaliere"] = resultat.get("volatiliteJournaliere",0)
        listeCrypto[i]['variationj1'] = resultat.get("variationj1")
        listeCrypto[i]["volatiliteAnnuel"] = resultat.get("volatiliteAnnuel")
        listeCrypto[i]['weight'] = liste_weight[i]
        
    
    return listeCrypto

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
    historiqueVolatiliteGenerale = calculService.getHistoriqueVolatiliteGenerale(90,listeCryptowithWeight,listePrix)
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