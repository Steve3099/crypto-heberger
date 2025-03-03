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
    
    async def get_list_cryptos(self):
        
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        params = {
            "id": id_Categorie
        }
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key
        }
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        data = data.get("data")
        for item in data:
            crypto = {
                "id": item.get("slug"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                # "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png?1696501400",
                "current_price": item.get("quote").get("USD").get("price"),
                "market_cap": item.get("quote").get("USD").get("market_cap"),
                
                # "market_cap_rank": 1,
                
                "fully_diluted_valuation": 1698676356870,
                "total_volume": 24899411400,
                "high_24h": 86434,
                "low_24h": 84340,
                "price_change_24h": -348.3227308636415,
                "price_change_percentage_24h": -0.4048,
                "market_cap_change_24h": -8152368438.560791,
                "market_cap_change_percentage_24h": -0.47763,
                "circulating_supply": 19831121.0,
                "total_supply": 19831121.0,
                "max_supply": 21000000.0,
                "ath": 108786,
                "ath_change_percentage": -21.22906,
                "ath_date": "2025-01-20T09:11:54.494Z",
                "atl": 67.81,
                "atl_change_percentage": 126271.70206,
                "atl_date": "2013-07-06T00:00:00.000Z",
                "roi": null,
                "last_updated": "2025-03-02T05:05:55.856Z"
                
            }