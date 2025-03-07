import json
from app.services.coinGeckoService import CoinGeckoService
from fastapi import HTTPException
from datetime import datetime
coinGeckoService = CoinGeckoService()

class CryptoService:
    async def get_crypto_rankings(self,id):
        # read listecrypto from json file
        list_crypto = await coinGeckoService.get_liste_crypto_nofilter()
        for crypto in list_crypto:
            if crypto["id"] == id:
                return crypto["market_cap_rank"]
            
    async def get_liste_crypto_from_json(self):
        # read the json file
        with open('app/json/liste_crypto/liste_crypto.json', 'r') as f:
            
            data = f.read()
            # return as a json
            
            return json.loads(data)
        
    async def get_on_crypto_from_liste_json(self,id):
        liste = await self.get_liste_crypto_from_json()
        # liste = json.loads(liste)
        
        for item in liste:
            if item["id"] == id:
                return item
        
        # tell tha there is no crypto with that id and 404*
        
        raise HTTPException(status_code=404, detail=f"Crypto with ID '{id}' not found")
    
    async def get_liste_prix_from_json(self,id):
        return await coinGeckoService.get_historical_prices(id)
    
    async def get_liste_prix_between_2_dates(self,id,date_start,date_end):
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        liste = await self.get_liste_prix_from_json(id)
        # transform liste which is a data frame to json
        
        # transform liste which is a dictionary to a list of dictionaries
        liste = [{"date": liste["date"][i], "price": liste["price"][i]} for i in range(len(liste["date"]))]
        
        # get prix between 2 date
        liste = [price for price in liste if price["date"] >= date_start and price["date"] <= date_end]
        
        return liste
    
    async def get_price_range(self,id,date_start,date_end):
        
        
        # check if date_start < date_end
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        liste = await self.get_liste_prix_from_json(id)
        # transform liste which is a data frame to json
        
        # transform liste which is a dictionary to a list of dictionaries
        liste = [{"date": liste["date"][i], "price": liste["price"][i]} for i in range(len(liste["date"]))]
        
        # get prix between 2 date
        liste = [price for price in liste if price["date"] >= date_start and price["date"] <= date_end]
        
        # get max price and min price
        max_price = 0
        min_price = 1000000000000
        for price in liste:
            if price["price"] > max_price:
                max_price = price["price"]
            if price["price"] < min_price:
                min_price = price["price"]
        
        return {
            "max_price":max_price,
            "min_price":min_price
        }
    
    async def get_historique_market_cap(self,id,date_start,date_end):
        
        # check if date_start < date_end
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        # read json file
        try:
            with open('app/json/crypto/market_cap/'+id+'_market_cap.json', 'r') as f:
                
                data = f.read()
                # return as a json
                
                liste = json.loads(data)
                liste_market_cap = []
                for item in liste:
                    if item["date"] >= date_start and item["date"] <= date_end:
                        liste_market_cap.append(item)
                
                return liste_market_cap
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Market cap for crypto with ID '{id}' not found")
        
        return liste
        
        