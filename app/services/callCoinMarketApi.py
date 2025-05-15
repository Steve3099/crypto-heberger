import asyncio
import json
import aiohttp
import aiofiles
from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
key = os.getenv("key_coin_market_cap_1")


class CallCoinMarketApi:
    async def fetch(self, url, headers=None, params=None):
        """Fetch JSON data from a URL asynchronously."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()  # Raise exception for HTTP errors
                try:
                    return await response.json()
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse JSON response: {e}")

    async def getFearAndGreed(self):
        """Retrieve the latest Fear and Greed index and save to JSON."""
        url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest"
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key,
        }
        try:
            data = await self.fetch(url, headers)
            result = data.get("data", {})

            # Ensure directory exists
            os.makedirs("app/json/fearAndGreed", exist_ok=True)
            async with aiofiles.open("app/json/fearAndGreed/fearAndGreed.json", "w") as f:
                await f.write(json.dumps(result, indent=4))
            return result
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch Fear and Greed index: {e}")

    async def get_liste_stablecoins(self):
        """Retrieve list of stablecoin symbols."""
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
        params = {"id": "604f2753ebccdd50cd175fc1"}
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key,
        }
        try:
            data = await self.fetch(url, headers, params)
            coins = data.get("data", {}).get("coins", [])
            return [coin.get("symbol", "").lower() for coin in coins]
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch stablecoins: {e}")

    async def set_liste_stable_wrapped_tokens(self):
        """Save stablecoins and wrapped tokens to JSON files."""
        id_Stable_Coin = "604f2753ebccdd50cd175fc1"
        id_Wrapped_Token = "6053df7b6be1bf5c15e865ed"
        await asyncio.gather(
            self.set_liste_symbole_by_id_categorie(id_Stable_Coin, "stablecoins"),
            self.set_liste_symbole_by_id_categorie(id_Wrapped_Token, "wrapped_tokens"),
        )

    async def set_liste_symbole_by_id_categorie(self, id_Categorie, category_name="stablecoins"):
        """Save symbols for a given category ID to JSON."""
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
        params = {"id": id_Categorie}
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key,
        }
        try:
            data = await self.fetch(url, headers, params)
            coins = data.get("data", {}).get("coins", [])
            symbols = [coin.get("symbol", "").lower() for coin in coins]

            # Ensure directory exists
            os.makedirs("app/json/other", exist_ok=True)
            async with aiofiles.open(f"app/json/other/{category_name}.json", "w") as f:
                await f.write(json.dumps(symbols, indent=4))
            return symbols
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch category {category_name}: {e}")

    async def get_stable_coins_from_json(self):
        """Load stablecoin symbols from JSON file."""
        try:
            async with aiofiles.open("app/json/other/stablecoins.json", "r") as f:
                content = await f.read()
            return json.loads(content)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse stablecoins JSON: {e}")

    async def get_wrapped_tokens_from_json(self):
        """Load wrapped token symbols from JSON file."""
        try:
            async with aiofiles.open("app/json/other/wrapped_tokens.json", "r") as f:
                content = await f.read()
            return json.loads(content)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse wrapped tokens JSON: {e}")

    async def get_list_cryptos(self, limit=5000, start=1):
        """Retrieve a list of cryptocurrencies with market data."""
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        params = {
            "start": start,
            "limit": limit,
        }
        headers = {
            "accept": "application/json",
            "X-CMC_PRO_API_KEY": key,
        }
        try:
            data = await self.fetch(url, headers, params)
            cryptos = []
            for item in data.get("data", []):
                quote = item.get("quote", {}).get("USD", {})
                cryptos.append({
                    "id": item.get("slug"),
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "current_price": quote.get("price"),
                    "market_cap": quote.get("market_cap"),
                    "volume_24h": quote.get("volume_24h"),
                    "price_change_24h": quote.get("percent_change_24h"),
                })
            return cryptos
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch cryptocurrencies: {e}")

    async def get_liste_crypto_unfiltered(self):
        """Retrieve an unfiltered list of cryptocurrencies by combining multiple API calls."""
        try:
            results = await asyncio.gather(
                self.get_list_cryptos(),
                self.get_list_cryptos(start=5001),
                self.get_list_cryptos(start=10001),
                return_exceptions=True,
            )
            # Flatten results and handle potential errors
            combined = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"Warning: API call failed with error: {result}")
                    continue
                combined.extend(result)
            return combined
        except Exception as e:
            raise RuntimeError(f"Failed to fetch unfiltered crypto list: {e}")