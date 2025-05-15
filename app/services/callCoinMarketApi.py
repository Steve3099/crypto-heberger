import json
import requests
from dotenv import load_dotenv
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent 
load_dotenv(BASE_DIR / ".env")
key = os.getenv("key_coin_market_cap")
# key = "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"

class CallCoinMarketApi():
    async def getFearAndGreed(self):
        url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest"
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key
        }
        response = requests.get(url,headers=headers)
        retour = json.loads(response.text)
        #  set fear and greed to json 
        with open("app/json/fearAndGreed/fearAndGreed.json","w") as f:
            f.write(json.dumps(retour.get("data",{})))
        return retour.get("data",{})
    
    async def get_liste_stablecoins(self):
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
        params = {
            "id": "604f2753ebccdd50cd175fc1"
        }
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key
        }
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        data  = data.get("data")
        liste_coin = data["coins"]
        
        liste_stablecoins = []
        for item in liste_coin:
            # put symbol to lower case  
            liste_stablecoins.append(item.get("symbol").lower())
        
        # put the liste symbole into csv
        # with open("app/csv/stablecoins/stablecoins.csv","w") as f:
        #     for symbol in liste_symbol:
        #         f.write(symbol + "\n")
        
        return liste_stablecoins
    
    def get_liste_symbole_by_id_categorie(self,id_Categorie):
        
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
        params = {
            "id": id_Categorie
        }
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"
        }
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        data = data.get("data")
        liste_coin = data["coins"]
        
        liste_stablecoins = []
        for item in liste_coin:
            # put symbol to lower case  
            liste_stablecoins.append(item.get("symbol").lower())
        
        # put the liste symbole into csv
        with open("app/csv/stablecoins/stablecoins.csv","w") as f:
            for symbol in liste_stablecoins:
                f.write(symbol + "\n")
        
        return liste_stablecoins
    
    async def get_list_cryptos(self,limit = 5000,start = 1):
        
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        params = {
            "start": start,
            "limit": limit
        }
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key
        }
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        data = data.get("data")
        # return data
        liste_crypto = []
        for item in data:
            crypto = {
                "id": item.get("slug"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                # "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png?1696501400",
                "current_price": item.get("quote").get("USD").get("price"),
                "market_cap": item.get("quote").get("USD").get("market_cap"),
                
                # "market_cap_rank": 1,
                "volume_24h": item.get("quote").get("USD").get("volume_24h"),
                "price_change_24h": item.get("quote").get("USD").get("percent_change_24h"),
                
            }
            liste_crypto.append(crypto)
        return liste_crypto
    
    async def get_liste_cypto_ufiltered(self):
        liste = await self.get_list_cryptos()
        liste += await self.get_list_cryptos(start = 5001)
        liste += await self.get_list_cryptos(start = 10001)
        return liste