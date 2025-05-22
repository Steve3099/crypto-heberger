import asyncio
import datetime
from decimal import Decimal, getcontext
import json
import aiohttp
import aiofiles
import pandas as pd
import numpy as np
import time
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.calculService import CalculService
# from app.services.cryptoService import CryptoService
from fastapi import HTTPException
import os
from pathlib import Path

coinMarketApi = CallCoinMarketApi()
calculService = CalculService()
# cryptoService = CryptoService()

# Load environment variables
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
key = os.getenv("key_coin_gecko")

class CoinGeckoService:
    async def get_liste_crypto(self, categorie_id="layer-1", page=1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "per_page": 250,
            # "category": categorie_id,
            "page": page,
            "order": "market_cap_desc",
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                df = await response.json()
        
        return df

    async def get_liste_crypto_no_filtre(self, categorie_id="layer-1", page=1, order="volume_desc"):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "per_page": 250,
            "page": page,
            "order": order,
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                df = await response.json()
        
        return df

    async def excludeStableCoin(self, data):
        id_Stable_Coin = "604f2753ebccdd50cd175fc1"
        id_Wrapped_Token = "6053df7b6be1bf5c15e865ed"
        stablecoins = await coinMarketApi.get_stable_coins_from_json()
        wrapped_tokens = await coinMarketApi.get_wrapped_tokens_from_json()

        filtered = [
            coin for coin in data
            if (coin["symbol"].lower() not in stablecoins and
                coin["symbol"].lower() not in wrapped_tokens and
                coin["current_price"] is not None and
                coin["market_cap"] > 0 and
                coin["price_change_percentage_24h"] is not None 
                and (coin["total_volume"] is not None and coin["total_volume"] >= 2000000)
                )
        ]
        
        return filtered

    async def get_liste_crypto_filtered(self):
        list_crypto_page_1 = await self.get_liste_crypto(page=1)
        list_crypto_page_2 = await self.get_liste_crypto(page=2)
        list_crypto_page_3 = await self.get_liste_crypto(page=3)
        list_crypto_page_4 = await self.get_liste_crypto(page=4)
        list_crypto = list_crypto_page_1 + list_crypto_page_2 + list_crypto_page_3 + list_crypto_page_4 

        list_crypto = await self.excludeStableCoin(list_crypto)
        
        return list_crypto

    async def get_historical_prices(self, crypto, vs_currency='usd', days=90):
        try:
            async with aiofiles.open(f'app/historique_prix_json/{crypto}_historique.json', 'r') as f:
                historique = json.loads(await f.read())
            df = pd.DataFrame(historique)
            
            df["price"] = df["price"].astype(float)
            df["date"] = df["date"].astype(str)
            
            last_date = pd.to_datetime(df["date"].iloc[-1])
            today = datetime.datetime.now()
            dif = (today - last_date).days
            if dif >= 2:
                raise FileNotFoundError("File outdated")
            
            return df[['date', 'price']]

        except FileNotFoundError:
            await self.set_historical_price_to_json(crypto, vs_currency, days)
            async with aiofiles.open(f'app/historique_prix_json/{crypto}_historique.json', 'r') as f:
                historique = json.loads(await f.read())
            df = pd.DataFrame(historique)
            
            df["price"] = df["price"].astype(float)
            df["date"] = df["date"].astype(str)
            
            return df[['date', 'price']]

    async def get_prix_one_crypto(self, crypto, intervale="", vs_currency="usd", days=90):
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': intervale,
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['price'] = df['price']
        
        return df[['date', 'price']]

    async def get_market_cap(self, crypto):
        try:
            async with aiofiles.open(f'app/market_cap_json/{crypto}_market_cap.json', 'r') as f:
                market_cap = json.loads(await f.read())
            return market_cap['market_cap']
        except Exception:
            url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
            headers = {
                "accept": "application/json",
                "x-cg-demo-api-key": key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            market_cap = data['market_data']['market_cap']['usd']
            
            market_cap_data = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "market_cap": market_cap,
            }
            async with aiofiles.open(f'app/market_cap_json/{crypto}_market_cap.json', 'w') as f:
                await f.write(json.dumps(market_cap_data, indent=4))
            
            return market_cap

    def getGraphWeight(self, listeCrypto):
        weightOther = 0
        listeRetourOther = []
        for el in listeCrypto:
            if el.get("weight") < 0.01:
                weightOther += el.get("weight")
            else:
                listeRetourOther.append({"coin": el.get("name"), "weight": el["weight"]})
        listeRetourOther.append({"coin": "other", "weight": weightOther})
        
        sommeweight = 0
        for el in listeRetourOther:
            el["weight"] = round(Decimal(el.get("weight")), 2)
            sommeweight += el["weight"]
        if sommeweight != 100.00:
            listeRetourOther[-1]["weight"] = round(Decimal(listeRetourOther[-1]["weight"]) + 1 - Decimal(sommeweight), 2)
            
        return listeRetourOther

    async def callCoinGeckoListeCrypto(self, ids=''):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids,
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                retour = await response.json()
        
        retour = await self.excludeStableCoin(retour)
        return retour

    async def set_historical_price_to_json(self, crypto, vs_currency='usd', days=90):
        try:
            url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
            params = {
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'daily',
            }
            headers = {
                "accept": "application/json",
                "x-cg-demo-api-key": key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            prices = data['prices']
            market_caps = data['market_caps']
            volumes = data['total_volumes']
            
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price']
            
            lf = pd.DataFrame(market_caps, columns=['timestamp', 'market_cap'])
            lf['date'] = pd.to_datetime(lf['timestamp'], unit='ms')
            lf['market_cap'] = lf['market_cap']
            
            volume = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
            volume['date'] = pd.to_datetime(volume['timestamp'], unit='ms')
            volume['volume'] = volume['volume']
            
            async with aiofiles.open(f'app/historique_prix_json/{crypto}_historique.json', 'w') as f:
                await f.write(df.to_json(date_format="iso", orient="records", indent=4))
            
            async with aiofiles.open(f'app/json/crypto/market_cap/{crypto}_market_cap.json', 'w') as f:
                await f.write(lf.to_json(date_format="iso", orient="records", indent=4))
                
            async with aiofiles.open(f'app/json/crypto/volume/{crypto}_volume.json', 'w') as f:
                await f.write(volume.to_json(date_format="iso", orient="records", indent=4))
        except Exception as e:
            # sleep time(5)
            await asyncio.sleep(60)
            await self.set_historical_price_to_json(crypto, vs_currency, days)

    async def set_market_cap_to_json(self, crypto):
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
        
        market_cap = data['market_data']['market_cap']['usd']
        
        market_cap_data = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "market_cap": market_cap,
        }
        async with aiofiles.open(f'app/market_cap_json/{crypto}_market_cap.json', 'w') as f:
            await f.write(json.dumps(market_cap_data, indent=4))

    async def schedule_historique_prix(self):
        liste_crypto = await self.get_liste_crypto_filtered()
        liste_crypto = liste_crypto[:100]
        for i, crypto in enumerate(liste_crypto):
            await self.set_historical_price_to_json(crypto.get('id'))
            print(f"historique {crypto.get('id')} done")
            
            if i % 20 == 0 and i != 0:
                await asyncio.sleep(60)

    async def schedule_market_cap(self):
        liste_crypto = await self.get_liste_crypto_filtered()
        liste_crypto = liste_crypto[:100]
        for i, crypto in enumerate(liste_crypto):
            await self.set_market_cap_to_json(crypto.get('id'))
            print(f"market cap {crypto.get('id')} done")
            
            if i % 20 == 0 and i != 0:
                await asyncio.sleep(60)

    async def schedule_liste_crypto_with_weight_volatility(self):
        listeCrypto = await self.get_liste_crypto_filtered()
        # return len(listeCrypto)
        # oreder by market cap
        listeCrypto = sorted(listeCrypto, key=lambda x: x['market_cap'], reverse=True)
        listeCrypto = listeCrypto[:80]
        liste_market_cap = []
        i=0
        for el in listeCrypto:
            if i%20 == 0 and i != 0:
                await asyncio.sleep(60)
            market_cap = await self.get_market_cap(el.get("id"))
            liste_market_cap.append(market_cap)
            i+=1
        
        liste_weight = await calculService.normalize_weights(liste_market_cap)
        liste_weight = await calculService.round_weights(liste_weight)
        
        liste_new = []
        for i in range(len(listeCrypto)):
            if i % 20 == 0 and i != 0:
                await asyncio.sleep(60)
            historique = await self.get_historical_prices(listeCrypto[i]["id"], "usd", 90)
            
            # if len(historique) > 90 and listeCrypto[i]["market_cap"] > 0:
            liste_volatilite = await calculService.getListeVolatilite(historique)
            volatiliteJ = liste_volatilite[1]
            volatiliteJ2 = liste_volatilite[2]
            variationJ1 = (volatiliteJ - volatiliteJ2) / volatiliteJ2
            
            listeCrypto[i]["volatiliteJournaliere"] = volatiliteJ
            listeCrypto[i]['variationj1'] = variationJ1
            listeCrypto[i]["volatiliteAnnuel"] = volatiliteJ * np.sqrt(365)
            listeCrypto[i]['weight'] = str(liste_weight[i])
            liste_new.append(listeCrypto[i])
        
        async with aiofiles.open('app/json/liste_crypto/listeCryptoWithWeight.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_new, indent=4))
        # return len(liste_new)
        return liste_new

    async def get_liste_crypto_with_weight(self):
        async with aiofiles.open('app/json/liste_crypto/listeCryptoWithWeight.json', 'r', encoding='utf-8') as f:
            liste = json.loads(await f.read())
        
        liste_no_filter = await self.get_liste_crypto_nofilter()
        
        for el in liste:
            
            for el2 in liste_no_filter:
                if el['id'] == el2['id']:
                    
                    el['volume_24h'] = el2['volume_24h']
                    el['current_price'] = el2['current_price']
                    # el['current_price'] = el2['current_price']
                    el['price_change_percentage_24h'] = el2['price_change_percentage_24h']
                    # try:
                    #     liste_binance = await cryptoService.get_liste_price_binance_from_json(id)
                    #     laste_price = liste_binance.tail(1)
                    #     price = laste_price.iloc[0]['price']
                    #     el['current_price'] = price
                    # except Exception as e:
                    #     price = el2['current_price']
                    
                    # break
        
        return liste

    async def set_liste_no_folter_to_json(self):
        liste_crypto = []
        i = 1
        while i <= 61:
            try:
                temp = await self.get_liste_crypto_no_filtre(page=i)
                if temp:
                    liste_crypto += temp
                    i += 1
                else:
                    break
                if i % 20 == 0 and i != 0:
                    await asyncio.sleep(60)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        async with aiofiles.open('app/json/liste_crypto/listeCryptoNoFiltre.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_crypto, indent=4))
        
        return liste_crypto

    async def get_liste_crypto_nofilter(self):
        async with aiofiles.open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
            liste = json.loads(await f.read())
        return liste

    async def get_global_data(self):
        url = "https://api.coingecko.com/api/v3/global"
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
        
        return data

    async def set_global_data_to_json(self):
        print("set global data to json")
        data = await self.get_global_data()
        market_cap = data['data']['total_market_cap']['usd']
        volume = data['data']['total_volume']['usd']
        
        global_data = {
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "market_cap": market_cap,
            "volume": volume,
        }
        
        try:
            async with aiofiles.open('app/json/global_data/global_data.json', 'r') as f:
                existing_data = json.loads(await f.read())
        except FileNotFoundError:
            existing_data = []
        
        existing_data.append(global_data)
        async with aiofiles.open('app/json/global_data/global_data.json', 'w') as f:
            await f.write(json.dumps(existing_data, indent=4))

    async def get_global_data_from_json(self):
        async with aiofiles.open('app/json/global_data/global_data.json', 'r') as f:
            existing_data = json.loads(await f.read())
        return existing_data

    async def get_last_Data(self, id):
        url = f'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': id,
            'vs_currencies': 'usd',
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        return data

    async def get_prix_one_crypto_2(self, crypto, intervale="", vs_currency="usd", days=90):
        url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': intervale,
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        
        # prices = data['prices']
        # market_caps = data['market_caps']
        # df = pd.DataFrame(prices, columns=['timestamp', 'price','market_cap'])
        # df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        # df['price'] = df['price']
        # df['market_cap'] = data['market_caps']
        
        return data