import datetime
from decimal import Decimal, getcontext
import http
import json
import requests
import pandas as pd
import numpy as np
import time
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.calculService import CalculService
from fastapi import HTTPException
import os
from pathlib import Path
coinMarketApi  = CallCoinMarketApi()
calculService = CalculService()

# get the key from the environnement variable or .env file
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent 
load_dotenv(BASE_DIR / ".env")
key = os.getenv("key_coin_gecko")

# key = "CG-pq44GDj1HKecURw2UA1uUYz8"
# key = "CG-uviXoVTxQUerBoCeZfuJ6c5y"
class CoinGeckoService:
    async def get_liste_crypto(self,categorie_id="layer-1",page=1):
        url = "https://api.coingecko.com/api/v3/coins/markets"

        params = {
            "vs_currency": "usd",
            "per_page": 250,
            "category": categorie_id,
            "page":page,
            "order": "market_cap_desc"
            # "order": "volume_desc"
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }

        response = requests.get(url, headers=headers,params=params)
        df = json.loads(response.text)
        
        retour = []
        for i in range(len(df)):
            retour.append(df[i])
        
        return df
    
    async def get_liste_crypto_no_filtre(self,categorie_id="layer-1",page=1):
        url = "https://api.coingecko.com/api/v3/coins/markets"

        params = {
            "vs_currency": "usd",
            "per_page": 250,
            # "category": categorie_id,
            "page":page,
            # "order": "volume_desc"
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }

        response = requests.get(url, headers=headers,params=params)
        df = json.loads(response.text)
        
        retour = []
        for i in range(len(df)):
            retour.append(df[i])
        
        return df
    async def excludeStableCoin(self,data):
        # List of known stablecoin symbols to exclude
        id_Stable_Coin = "604f2753ebccdd50cd175fc1"
        id_Wrapped_Token = "6053df7b6be1bf5c15e865ed"
        stablecoins = coinMarketApi.get_liste_symbole_by_id_categorie(id_Stable_Coin)
        wrapped_tokens = coinMarketApi.get_liste_symbole_by_id_categorie(id_Wrapped_Token)
        
        filtered = [coin for coin in data if 
                    coin["symbol"].lower() not in stablecoins and 
                    coin["symbol"].lower() not in wrapped_tokens and 
                    coin["current_price"] is not None and 
                    coin["market_cap"]  > 0 and
                    coin["price_change_percentage_24h"] is not None and
                    (coin["total_volume"]  is not  None or coin["total_volume"] >= 2000000)]
        
        return filtered
    
    async def get_liste_crypto_filtered(self):
        list_crypto_page_1 = await self.get_liste_crypto(page = 1)
        
        list_crypto_page_2 = await self.get_liste_crypto(page = 2)

        list_crypto = list_crypto_page_1 + list_crypto_page_2

        list_crypto = await self.excludeStableCoin(list_crypto)
        
        return list_crypto
            
    async def get_historical_prices(self,crypto, vs_currency='usd', days=90):
        
        #  check if crypto+_historique.json exist
        try:
            # Load JSON
            with open('app/historique_prix_json/'+crypto + "_historique.json") as f:
                historique = json.load(f)
            df = pd.DataFrame(historique)  
            
            # 🔹 Convert `numpy` data types to standard Python types
            df["price"] = df["price"].astype(float)  # Convert to Python float
            df["date"] = df["date"].astype(str) 
            
            return df[['date', 'price']]  # Return only date and price

        except FileNotFoundError:
            url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
            params = {
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'daily'
            }
            headers = {
                "accept": "application/json",
                "x-cg-demo-api-key": 'CG-pq44GDj1HKecURw2UA1uUYz8'
            }
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            prices = data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price'].round(2)
            
            # put historique on json file dans un fichier json
            with open('app/historique_prix_json/'+crypto+'_historique.json', 'w') as f:
                f.write(df.to_json(date_format="iso", orient="records", indent=4))
            
            return df[['date', 'price']]

    def getListeCryptoWithWeight(self, listeCrypto):

        # Augmenter la précision des calculs pour réduire les erreurs
        getcontext().prec = 28  

        listeRetour = []
        somme = Decimal(0)

        # Calculer la somme totale de la capitalisation boursière
        for el in listeCrypto:
            somme += Decimal(el.get("current_price", "")) * Decimal(el.get("circulating_supply", ""))

        # Calculer les poids bruts sans les arrondir
        poids_bruts = []
        for el in listeCrypto:
            poids_brut = (Decimal(el.get("current_price", "")) * Decimal(el.get("circulating_supply", ""))) / somme * 100
            poids_bruts.append(poids_brut)
            el["weight"] = poids_brut  # Stockage temporaire sans arrondi
            listeRetour.append(el)

        # Calcul de l'erreur cumulée d'arrondi
        somme_arrondie = Decimal(0)
        for el in listeRetour:
            el["weight"] = round(el["weight"], 2)
            somme_arrondie += el["weight"]

        # Redistribution proportionnelle de l'erreur
        erreur_totale = Decimal(100) - somme_arrondie
        sommett = 0
        for el in listeRetour:
            el["weight"] += round(el["weight"] / somme_arrondie * erreur_totale, 2)
            sommett += el["weight"]
        return listeRetour
    
    async def get_market_cap(self,crypto):
        
        # chexk if market cap is already in json file
        try:
            with open('app/market_cap_json/'+crypto+'_market_cap.json') as f:
                market_cap = json.load(f)
            return market_cap['market_cap']
        except Exception as e:
            url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
            headers = {
                "accept": "application/json",
                "x-cg-demo-api-key": key
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            market_cap = data['market_data']['market_cap']['usd']
            
            # put market cap in json with date
            market_cap_data = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "market_cap": market_cap
            }
            with open('app/market_cap_json/'+crypto+'_market_cap.json', 'w') as f:
                f.write(json.dumps(market_cap_data, indent=4))
            
            return market_cap

    def getGraphWeight(self,listeCrypto):
        # if wieght < 1% we put all of then in a coin labeed other and add all thier weight together
        weightOther = 0
        listeRetourOther = []
        for el in listeCrypto:
            if el.get("weight") < 0.01:
                weightOther += el.get("weight")
            else:
                listeRetourOther.append({ "coin":el.get("name"),"weight":el["weight"]})
        listeRetourOther.append({ "coin":"other","weight":weightOther})
        
        #  arrondier weght to 2 decimal
        sommeweight =0
        for el in listeRetourOther:
            el["weight"] = round(Decimal(el.get("weight")),2)
            sommeweight +=el["weight"]
        if sommeweight != 100.00:
            print(sommeweight)
            listeRetourOther[-1]["weight"] = round(Decimal(listeRetourOther[-1]["weight"]) + 1 - Decimal(sommeweight),2)
            
        return listeRetourOther
    
    async def callCoinGeckoListeCrypto(self,ids = ''):
        url = "https://api.coingecko.com/api/v3/coins/markets"

        params = {
            "vs_currency": "usd",
            "ids": ids
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }

        response = requests.get(url, headers=headers,params=params)
        retour = json.loads(response.text)
        retour = await self.excludeStableCoin(retour)
        
        return retour
    
    async def set_historical_price_to_json(self,crypto, vs_currency='usd', days=90):
        # print(os.environ)
        # print(key)
        # return key
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': 'daily'
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        prices = data['prices']
        market_cap = data['market_caps']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['price'] = df['price'].round(8)
        
        lf = pd.DataFrame(market_cap, columns=['timestamp', 'market_cap'])
        lf['date'] = pd.to_datetime(lf['timestamp'], unit='ms')
        lf['market_cap'] = lf['market_cap'].round(2)
        
        # put historique on json file dans un fichier json
        with open('app/historique_prix_json/'+crypto+'_historique.json', 'w') as f:
            f.write(df.to_json(date_format="iso", orient="records", indent=4))
        
        with open('app/json/crypto/market_cap/'+crypto+'_market_cap.json', 'w') as f:
            f.write(lf.to_json(date_format="iso", orient="records", indent=4))
    
    async def set_market_cap_to_json(self,crypto):
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        market_cap = data['market_data']['market_cap']['usd']
        
        # put market cap in json with date
        market_cap_data = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "market_cap": market_cap
        }
        with open('app/market_cap_json/'+crypto+'_market_cap.json', 'w') as f:
            f.write(json.dumps(market_cap_data, indent=4))
    
    async def schedule_historique_prix(self):
        liste_crypto = await self.get_liste_crypto_filtered()
        liste_crypto = liste_crypto[:100]
        for i in range(0,len(liste_crypto)):
            await self.set_historical_price_to_json(liste_crypto[i].get('id'))
            print(f"historique {liste_crypto[i].get('id')} done")
            
            if i%20 == 0 and i!= 0:
                # sleep 1 minute
                time.sleep(60)
    
    async def schedule_market_cap(self):
        liste_crypto = await self.get_liste_crypto_filtered()
        liste_crypto = liste_crypto[:100]
        for i in range(0,len(liste_crypto)):
            await self.set_market_cap_to_json(liste_crypto[i].get('id'))
            print(f"market cap {liste_crypto[i].get('id')} done")
            
            if i%20 == 0 and i!= 0:
                # sleep 1 minute
                time.sleep(60)
    async def schedule_liste_crypto_with_weight_volatility(self):
        listeCrypto = await self.get_liste_crypto_filtered()
        # listeCrypto = listeCrypto[247:]
        liste_market_cap =[]
        for el in listeCrypto:
            market_cap = await self.get_market_cap(el.get("id"))
            liste_market_cap.append(market_cap)
        
        # return listeCrypto,liste_market_cap
        
        liste_weight = calculService.normalize_weights(liste_market_cap)
        liste_weight = calculService.round_weights(liste_weight)
        # add volatilite to each listeWithWeight
        liste_new = []
        for i in range(len(listeCrypto)):
            historique = await self.get_historical_prices(listeCrypto[i]["id"],"usd", 90)
            
            if len(historique) > 90 and listeCrypto[i]["market_cap"] > 0:
                
                # liste_prix.append(historique)
            
                # resultat = calculService.getVolatiliteOneCrypto(listeCrypto[i]["id"])
                liste_volatilite = await calculService.getListeVolatilite(historique)
                volatiliteJ = liste_volatilite[1]
                volatiliteJ2 = liste_volatilite[2]
                variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2
                
                listeCrypto[i]["volatiliteJournaliere"] = volatiliteJ
                listeCrypto[i]['variationj1'] = variationJ1
                listeCrypto[i]["volatiliteAnnuel"] = volatiliteJ * np.sqrt(365)
                listeCrypto[i]['weight'] = str(liste_weight[i])
                liste_new.append(listeCrypto[i])
                
        # put liste crypto into json file
        with open('app/json/liste_crypto/listeCryptoWithWeight.json', 'w', encoding='utf-8') as f:
            json.dump(liste_new, f, indent=4)
        # print(liste_new)
        return liste_new
    
    async def get_liste_crypto_with_weight(self):
        with open('app/json/liste_crypto/listeCryptoWithWeight.json', 'r', encoding='utf-8') as f:
            liste = json.load(f)
        
        liste_no_filter = await self.get_liste_crypto_nofilter()
        liste_no_filter = liste_no_filter
        
        for el in liste:
            for el2 in liste_no_filter:
                if el['id'] == el2['id']:
                    
                    el['volume_24h'] = el2['volume_24h']
                    # el['symbol'] = el2['symbol']
                    break
        
        return liste
                
    async def set_liste_no_folter_to_json(self):
        liste_crypto = []
        i = 1
        t = True
        while i <= 61:
            try:
                temp = await self.get_liste_crypto_no_filtre(page=i)
                print("page " + str(i)   )
                print("temp " + str(len(temp)))
                if len(temp) > 0 or temp != None:
                    liste_crypto += temp
                    i += 1
                elif len(temp) == 0: 
                    # stop the while loop
                    t = False
                    break
                if i%20 ==0 and i!= 0:
                    time.sleep(60)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        return liste_crypto
        
        with open('app/json/liste_crypto/listeCryptoNoFiltre.json', 'w', encoding='utf-8') as f:
            json.dump(liste_crypto, f, indent=4)
        return liste_crypto
    
    async def get_liste_crypto_nofilter(self):
        with open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
            liste = json.load(f)
        return liste
    
    