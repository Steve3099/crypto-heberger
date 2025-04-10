import json
import requests

class BinanceService:
    async def get_binance_symbols(self):
        url = 'https://api.binance.com/api/v3/exchangeInfo'
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

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

            # Save as JSON
            with open("app/json/binance/symbols.json", "w") as f:
                json.dump(usd_pairs, f, indent=4)

            return len(usd_pairs)
        else:
            print(f"Error: {response.status_code}")
            return []
    
    async def get_symbols_from_json(self):
        with open("app/json/binance/symbols.json", "r") as f:
            data = json.load(f)
        return data

    # symbols = get_binance_symbols()
    # print(symbols)