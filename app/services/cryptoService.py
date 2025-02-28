import json
from app.services.coinGeckoService import CoinGeckoService
from fastapi import HTTPException

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
        
        