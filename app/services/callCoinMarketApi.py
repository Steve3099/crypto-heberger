import json
import requests


class CallCoinMarketApi():
    def getFearAndGreed(self):
        url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest"
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"
        }
        response = requests.get(url,headers=headers)
        retour = json.loads(response.text)
        return retour.get("data",{})