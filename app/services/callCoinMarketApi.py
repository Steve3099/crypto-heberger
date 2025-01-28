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