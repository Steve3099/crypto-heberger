from decimal import Decimal, getcontext
import json
import requests
import pandas as pd

key = "CG-pq44GDj1HKecURw2UA1uUYz8"

class CoinGeckoService:
    def get_liste_crypto(self):
        url = "https://api.coingecko.com/api/v3/coins/markets"

        params = {
            "vs_currency": "usd",
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
    
        return retour
    def excludeStableCoin(self,listeCoin):
        # List of known stablecoin symbols to exclude
        stablecoin_symbols = {"usdt", "usdc", "busd", "dai", "tusd", "ust", "gusd", "pax", "eurs", "frax", "husd"}
        
        listeRetour = []
        for el in listeCoin:
            # Exclude known stablecoins by symbol
            if el.get("symbol", "").lower() in stablecoin_symbols:
                continue
            
            # Exclude assets with minimal price change (e.g., ±0.01% in 24h)
            price_change_percentage_24h = el.get("price_change_percentage_24h", 0)
            if abs(price_change_percentage_24h) < 0.01:
                continue
            # Add non-stablecoins to the result list
            listeRetour.append(el)
        
        return listeRetour
    
    def get_historical_prices(self,crypto, vs_currency='usd', days=90):
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
    
    def get_market_cap(self,crypto):
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        market_cap = data['market_data']['market_cap']['usd']
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
    
    def callCoinGeckoListeCrypto(self,ids = ''):
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
        return retour