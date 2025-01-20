import requests
import json

#coinGecko API 
# key = CG-uviXoVTxQUerBoCeZfuJ6c5y
# URL :
# . Coins List : https://api.coingecko.com/api/v3/coins/list
# . Coins List with Market Data : https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd
# . historiques : https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=5


def callApi(self, url: str, method: str, headers: dict, body: dict):
    try:
        response = requests.request(method, url, headers=headers, json=body)
        return response
    except Exception as e:
        print(e)
        return None
    
def callCoinGeckoListeCrypto():
    url = "https://api.coingecko.com/api/v3/coins/list"

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }

    response = requests.get(url, headers=headers)
    return response.text

def getHistorique(days: int = 30,coin:str ="bitcoin"):
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    
    params = {
        "vs_currency": "eur",
        "days": str(days),
        "interval": "daily"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }
    session = requests.Session()
    request = requests.Request('GET', url, headers=headers, params=params)
    prepared_request = session.prepare_request(request)

    response = session.send(prepared_request)
    return response.text

def getSimpleGeckoApi():
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }

    response = requests.get(url, headers=headers, params=params)
    #transform the result to json
    retour = json.loads(response.text)
    return retour

def getHistoriqueOneMonthAgo(self,coin:str ="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    
    params = {
        "vs_currency": "eur",
        "days": "90",
        "interval": "daily"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }
    session = requests.Session()
    request = requests.Request('GET', url, headers=headers, params=params)
    prepared_request = session.prepare_request(request)

    response = session.send(prepared_request)
    return response.text