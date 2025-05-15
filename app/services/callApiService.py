import aiohttp
import json
import asyncio

async def callApi(url: str, method: str, headers: dict, body: dict):
    """Make an async API request."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=body) as response:
                return await response.text()
    except Exception as e:
        print(f"Error in callApi: {e}")
        return None

async def getHistorique(days: int = 90, coin: str = "bitcoin"):
    """Fetch historical price data for a coin from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": "daily"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error in getHistorique: HTTP {response.status}")
                    return ""
    except Exception as e:
        print(f"Error in getHistorique: {e}")
        return ""

async def getSimpleGeckoApi():
    """Fetch simple price data for Bitcoin and Ethereum from CoinGecko."""
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error in getSimpleGeckoApi: HTTP {response.status}")
                    return {}
    except Exception as e:
        print(f"Error in getSimpleGeckoApi: {e}")
        return {}

async def getHistoriqueOneMonthAgo(coin: str = "bitcoin"):
    """Fetch 90 days of historical price data for a coin in EUR from CoinGecko."""
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
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error in getHistoriqueOneMonthAgo: HTTP {response.status}")
                    return ""
    except Exception as e:
        print(f"Error in getHistoriqueOneMonthAgo: {e}")
        return ""