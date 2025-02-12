import datetime
from decimal import Decimal, getcontext
import json
import requests
import pandas as pd
import time

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
    def excludeStableCoin(self,data):
        # List of known stablecoin symbols to exclude
        filtered = []

        for coin in data:
            symbol = coin["symbol"].lower()
            price = coin["current_price"]
            price_change_24h = abs(coin["price_change_percentage_24h"])
            total_volume = coin["total_volume"]
            
            # Detect Stablecoins (Price around $1 and Low Volatility)
            is_stablecoin = (0.98 <= price <= 1.02 and price_change_24h < 0.5)

            # Detect Wrapped Tokens (Symbol starts with "w" or resembles a known pattern)
            is_wrapped = (symbol.startswith("w") and len(symbol) > 1) or "wrapped" in coin["id"] or  "wrapped" in coin["name"].lower()

            #  dectect those which were ceated less than 90 days ago th attribut is "atl_date": "2013-07-06T00:00:00.000Z",
            


            # Assuming coin["atl_date"] is in ISO 8601 format
            is_new = datetime.datetime.fromisoformat(coin["atl_date"].replace("Z", "")) > (datetime.datetime.now() - datetime.timedelta(days=90))

            # Filter only valid tokens
            if not is_stablecoin and not is_wrapped and total_volume >= 2_000_000 and not is_new:
                filtered.append(coin)

        return filtered[:80]
    
    def get_historical_prices(self,crypto, vs_currency='usd', days=90):
        
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

        except Exception as e:
            print(f"Error: {e}")
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
        retour = self.excludeStableCoin(retour)
        
        return retour
    
    async def set_historical_price_to_json(self,crypto, vs_currency='usd', days=90):
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
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['price'] = df['price'].round(8)
        
        # put historique on json file dans un fichier json
        with open('app/historique_prix_json/'+crypto+'_historique.json', 'w') as f:
            f.write(df.to_json(date_format="iso", orient="records", indent=4))
    
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
        liste_crypto = await self.callCoinGeckoListeCrypto()
        for i in range(0,len(liste_crypto)):
            await self.set_historical_price_to_json(liste_crypto[i].get('id'))
            print(f"historique {liste_crypto[i].get('id')} done")
            
            if i%10 == 0:
                # sleep 1 minute
                time.sleep(60)
    
    async def schedule_market_cap(self):
        liste_crypto = await self.callCoinGeckoListeCrypto()
        for i in range(0,len(liste_crypto)):
            await self.set_market_cap_to_json(liste_crypto[i].get('id'))
            print(f"market cap {liste_crypto[i].get('id')} done")
            
            if i%10 == 0:
                # sleep 1 minute
                time.sleep(60)
                