import json
import aiohttp
import aiofiles
import os

class BinanceService:
    async def get_binance_symbols(self):
        """Fetch trading USDT pairs from Binance API and save to JSON."""
        url = 'https://api.binance.com/api/v3/exchangeInfo'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Only keep symbols where quoteAsset is USDT and status is TRADING
                    usd_pairs = [
                        {
                            "symbol": symbol["symbol"],
                            "baseAsset": symbol["baseAsset"],
                            "quoteAsset": symbol["quoteAsset"]
                        }
                        for symbol in data['symbols']
                        if symbol["quoteAsset"] == "USDT" and symbol["status"] == "TRADING"
                    ]

                    # Ensure directory exists and save as JSON
                    os.makedirs("app/json/binance", exist_ok=True)
                    async with aiofiles.open("app/json/binance/symbols.json", "w", encoding='utf-8') as f:
                        await f.write(json.dumps(usd_pairs, indent=4, ensure_ascii=False))

                    return len(usd_pairs)
                else:
                    print(f"Error: {response.status}")
                    return 0

    async def get_symbols_from_json(self):
        """Read Binance symbols from JSON file."""
        try:
            async with aiofiles.open("app/json/binance/symbols.json", "r", encoding='utf-8') as f:
                data = json.loads(await f.read())
            return data
        except FileNotFoundError:
            print("Error: symbols.json not found")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return []