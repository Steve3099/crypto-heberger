import json
import math
import numpy as np
from fastapi import APIRouter
from app.services.callApiService import getHistorique,getSimpleGeckoApi
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.indexService import IndexService

cryptorouter  = APIRouter()
calculService = CalculService()
coinGeckoService = CoinGeckoService()
callCoinMArketApi = CallCoinMarketApi()
indexService = IndexService()
@cryptorouter.get("/listeCrypto")
async def getListe():
    retour = await coinGeckoService.callCoinGeckoListeCrypto()
    # retour = retour[0:75]
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
    historique = coinGeckoService.get_historical_prices(coin,vs_currency, days)
    
    liste_volatilite = calculService.getListeVolatilite(historique)
    # return liste_volatilite
    volatiliteJ = liste_volatilite[1]
    volatiliteJ2 = liste_volatilite[2]
    variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2

    volatiliteMois = liste_volatilite[31]
    variationMois = (liste_volatilite[31] - liste_volatilite[1]) / liste_volatilite[31]
    
    volatiliteJ7 = liste_volatilite[8]
    variationJ7 = (liste_volatilite[8] - liste_volatilite[1]) / liste_volatilite[8]
    
    # get rank
    detailCrypto = await coinGeckoService.callCoinGeckoListeCrypto(coin)
    ranking = detailCrypto[0].get("market_cap_rank", 0)    
    
    retour = {
            "id":coin,
            "rank":ranking,
            "volatiliteAnnuel" : volatiliteJ * np.sqrt(365),
            "volatiliteJournaliere": volatiliteJ,
            "volatiliteJ1": volatiliteJ2,
            "variationj1": variationJ1,
            "volatiliteJ7": volatiliteJ7, 
            "variationj7": variationJ7,
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
    retour = calculService.top5CroissanceDevroissance(listeCrypto)
    return retour

@cryptorouter.get("/weights")  
async def getListeCryptoAvecPoids():
    listeCrypto = await getListe()
    liste_market_cap =[]
    for el in listeCrypto:
        market_cap = await coinGeckoService.get_market_cap(el.get("id"))
        liste_market_cap.append(market_cap)
        
    liste_weight = calculService.normalize_weights(liste_market_cap)
    liste_weight = calculService.round_weights(liste_weight)
    # add volatilite to each listeWithWeight
    for i in range(len(listeCrypto)):
        resultat = await getVolatiliteOneCrypto(listeCrypto[i]["id"])
        listeCrypto[i]["volatiliteJournaliere"] = resultat.get("volatiliteJournaliere",0)
        listeCrypto[i]['variationj1'] = resultat.get("variationj1")
        listeCrypto[i]["volatiliteAnnuel"] = resultat.get("volatiliteAnnuel")
        listeCrypto[i]['weight'] = liste_weight[i]
        
    
    return listeCrypto

@cryptorouter.get("/GraphWeights")  
async def getGraphPoids():
    listeCrypto = await getListeCryptoAvecPoids()
    return coinGeckoService.getGraphWeight(listeCrypto)
    
@cryptorouter.get("/VolatiliteGenerale")  
async def getvaltilitePortefeuille(vs_currency = 'usd',days =90):
    # obtenir la liste des crypto
    liste_crypto = await getListe()
    # return len(liste_crypto)
    # get liste de prix
    liste_prix = []
    for el in liste_crypto:
        historique = coinGeckoService.get_historical_prices(el.get('id'),vs_currency, days)
        liste_prix.append(historique)
    
    # get liste_weight
    liste_market_cap =[]
    for el in liste_crypto:
        market_cap = await coinGeckoService.get_market_cap(el.get("id"))
        liste_market_cap.append(market_cap)
    
    liste_weight = calculService.normalize_weights(liste_market_cap)
    liste_weight = calculService.round_weights(liste_weight)
    liste_volatilite_portefeuille = []
    
    for i in range(len(liste_prix[0])-3):
        liste_prix_utiliser = []
        for el in liste_prix:
            test = []
            if i!= 0:
                test = el.iloc[:-i] 
            else:
                test =  el
            liste_prix_utiliser.append(test)
        
        liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculService.calculate_statistics(liste_prix_utiliser,liste_crypto,liste_weight)
        liste_volatilite_portefeuille.append(portfolio_volatility_mat)
    
    retour = {
        "volatiliteGenerale": liste_volatilite_portefeuille[1],
        "historiqueVolatiliteGenerale": liste_volatilite_portefeuille[1:],
    }
    
    return retour

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
    
    # get liste_weight
    liste_market_cap =[]
    for el in liste_crypto:
        market_cap = await coinGeckoService.get_market_cap(el.get("id"))
        liste_market_cap.append(market_cap)
        
    liste_weight = calculService.normalize_weights(liste_market_cap)
    liste_weight = calculService.round_weights(liste_weight)
    
    
    liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculService.calculate_statistics(liste_prix,liste_crypto,liste_weight)
    return covariance_matrix
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