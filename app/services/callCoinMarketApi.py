import json
import requests

key = "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"

class CallCoinMarketApi():
    async def getFearAndGreed(self):
        url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest"
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key
        }
        response = requests.get(url,headers=headers)
        retour = json.loads(response.text)
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
        data  = data.get("data")
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