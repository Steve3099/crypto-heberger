import json
import os
import aiofiles
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.binanceService import BinanceService
from fastapi import HTTPException
from datetime import datetime

coinGeckoService = CoinGeckoService()
callCoinMarketApi = CallCoinMarketApi()
binanceService = BinanceService()

class CryptoService:
    async def get_crypto_rankings(self, id):
        """Retrieve market cap rank for a given crypto ID."""
        list_crypto = await coinGeckoService.get_liste_crypto_nofilter()
        for crypto in list_crypto:
            if crypto["id"] == id:
                return crypto["market_cap_rank"]
        raise HTTPException(status_code=404, detail=f"Crypto with ID '{id}' not found")

    async def get_liste_crypto_from_json(self):
        """Read crypto list from JSON file asynchronously."""
        try:
            async with aiofiles.open('app/json/liste_crypto/liste_crypto.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            return json.loads(data)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Crypto list file not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse crypto list: {e}")

    async def get_on_crypto_from_liste_json(self, id):
        """Retrieve a single crypto by ID from JSON list."""
        liste = await self.get_liste_crypto_from_json()
        for item in liste:
            if item["id"] == id:
                return item
        raise HTTPException(status_code=404, detail=f"Crypto with ID '{id}' not found")

    async def get_liste_prix_from_json(self, id):
        """Read price history for a crypto from JSON file."""
        try:
            async with aiofiles.open(f'app/json/crypto/prix/{id}_prix.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            return json.loads(data)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Price data for crypto with ID '{id}' not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse price data: {e}")

    async def get_liste_prix_between_2_dates(self, id, date_start, date_end):
        """Retrieve price history for a crypto between two dates."""
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        crypto = await self.check_if_crypto_in_binance(id)
        # if crypto:
        #     liste = await self.get_liste_price_binance_from_json(crypto)
        # else:
        liste =  await self.get_liste_prix_from_json(id)

        return [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]

    async def get_price_range(self, id, date_start, date_end):
        """Retrieve max and min prices for a crypto between two dates."""
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        liste = await self.get_liste_prix_from_json(id)
        liste = [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]

        if not liste:
            return {"max_price": 0, "min_price": 0}

        max_price = max(item["price"] for item in liste)
        min_price = min(item["price"] for item in liste)

        return {"max_price": max_price, "min_price": min_price}

    async def get_historique_market_cap(self, id, date_start, date_end):
        """Retrieve market cap history for a crypto between two dates."""
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        try:
            async with aiofiles.open(f'app/json/crypto/market_cap/{id}_market_cap.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            liste = json.loads(data)
            return [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Market cap for crypto with ID '{id}' not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse market cap data: {e}")

    async def set_historique_market_cap_generale(self):
        """Calculate and save total market cap history for all cryptos."""
        liste_crypto = await self.get_liste_crypto_from_json()
        liste_market_cap_history = []
        liste_crypto_used = []

        for crypto in liste_crypto:
            try:
                async with aiofiles.open(f'app/json/crypto/market_cap/{crypto["id"]}_market_cap.json', 'r', encoding='utf-8') as f:
                    data = await f.read()
                liste = json.loads(data)
                if len(liste) >= 90:
                    liste_crypto_used.append(crypto)
                    liste_market_cap_history.append(liste)
            except (FileNotFoundError, json.JSONDecodeError):
                continue

        if not liste_market_cap_history:
            return "No valid market cap data found"

        liste_somme_market_cap = []
        for i in range(len(liste_market_cap_history[0])):
            market_cap = 0
            date = liste_market_cap_history[0][i]["date"]
            if date.split("T")[1] != "00:00:00.000":
                continue
            for j in range(len(liste_crypto_used)):
                market_cap += liste_market_cap_history[j][i]["market_cap"]
            liste_somme_market_cap.append({"date": date, "market_cap": market_cap})

        os.makedirs('app/json/crypto/market_cap/generale', exist_ok=True)
        async with aiofiles.open('app/json/crypto/market_cap/generale/historique_market_cap_generale.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_somme_market_cap, indent=4, ensure_ascii=False))

        return "market_cap generale done"

    async def set_historique_volume_generale(self):
        """Calculate and save total volume history for all cryptos."""
        liste_crypto = await self.get_liste_crypto_from_json()
        liste_volume_history = []
        liste_crypto_used = []

        for crypto in liste_crypto:
            try:
                async with aiofiles.open(f'app/json/crypto/volume/{crypto["id"]}_volume.json', 'r', encoding='utf-8') as f:
                    data = await f.read()
                liste = json.loads(data)
                if len(liste) >= 90:
                    liste_crypto_used.append(crypto)
                    liste_volume_history.append(liste)
            except (FileNotFoundError, json.JSONDecodeError):
                continue

        if not liste_volume_history:
            return "No valid volume data found"

        liste_somme_volume = []
        for i in range(len(liste_volume_history[0])):
            volume = 0
            date = liste_volume_history[0][i]["date"]
            if date.split("T")[1] != "00:00:00.000":
                continue
            for j in range(len(liste_crypto_used)):
                volume += liste_volume_history[j][i]["volume"]
            liste_somme_volume.append({"date": date, "volume": volume})

        os.makedirs('app/json/crypto/volume/generale', exist_ok=True)
        async with aiofiles.open('app/json/crypto/volume/generale/historique_volume_generale.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_somme_volume, indent=4, ensure_ascii=False))

        return "volume generale done"

    async def get_volume_generale_between_2_date(self, date_start, date_end):
        """Retrieve total volume history between two dates."""
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        try:
            async with aiofiles.open('app/json/crypto/volume/generale/historique_volume_generale.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            liste = json.loads(data)
            return [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="General volume data not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse volume data: {e}")

    async def get_marketcap_generale_between_2_date(self, date_start, date_end):
        """Retrieve total market cap history between two dates."""
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        try:
            async with aiofiles.open('app/json/crypto/market_cap/generale/historique_market_cap_generale.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            liste = json.loads(data)
            return [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="General market cap data not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse market cap data: {e}")

    async def set_info_one_crypto(self, id, info):
        """Save info for a single crypto to JSON."""
        os.makedirs('app/json/crypto/info', exist_ok=True)
        async with aiofiles.open(f'app/json/crypto/info/{id}_info.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(info, indent=4, ensure_ascii=False))
        return f"info {id} done"

    async def set_info_crypto(self):
        """Combine CoinGecko and CoinMarketCap data and save to JSON."""
        liste_coin_gecko = await coinGeckoService.set_liste_no_folter_to_json()
        liste_coin_market_cap = await callCoinMarketApi.get_liste_crypto_unfiltered()
        liste_coin_with_weight = await coinGeckoService.get_liste_crypto_with_weight()
        
        for item in liste_coin_with_weight:
            for item2 in liste_coin_gecko:
                if item["id"] == item2["id"]:
                    item["market_cap"] = item2["market_cap"]
                    item["price_change_percentage_24h"] = item2["price_change_percentage_24h"]
                    break
        
        
        async with aiofiles.open('app/json/liste_crypto/listeCryptoWithWeight.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_coin_with_weight, indent=4))

        liste_crypto = []
        for item in liste_coin_gecko:
            for item2 in liste_coin_market_cap:
                if item["name"].lower() == item2["name"].lower() or item["symbol"].lower() == item2["symbol"].lower():
                    item["volume_24h"] = item2["volume_24h"]
                    liste_crypto.append(item)
                    break

        liste_crypto = list({v['id']: v for v in liste_crypto}.values())
        
        os.makedirs('app/json/crypto/info', exist_ok=True)
        async with aiofiles.open('app/json/crypto/info/crypto.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_crypto, indent=4, ensure_ascii=False))

    async def get_liste_crypto_nofilter(self, page, quantity):
        """Retrieve paginated list of cryptos ordered by market cap."""
        try:
            async with aiofiles.open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
                liste = json.loads(await f.read())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Crypto info file not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse crypto info: {e}")

        # liste = sorted(liste, key=lambda x: x.get("market_cap", 0), reverse=True)
        # liste = sorted(liste, key=lambda x: (x["market_cap"] is None, x["market_cap"] or 0), reverse=True)
        liste = sorted(liste, key=lambda x: (x["market_cap"] is None, x["market_cap"] if x["market_cap"] is not None else 0), reverse=True)

    
        quantite_de_donnees = len(liste)
        nombre_de_page = -(-len(liste) // quantity)
        liste = liste[(page - 1) * quantity:page * quantity]

        return {
            "quantite_de_donnees": quantite_de_donnees,
            "nombre_de_page": nombre_de_page,
            "page": page,
            "liste": liste,
        }

    async def get_fear_and_greed_from_json(self):
        """Read Fear and Greed index from JSON file."""
        try:
            async with aiofiles.open('app/json/fearAndGreed/fearAndGreed.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            return json.loads(data)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Fear and Greed data not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Fear and Greed data: {e}")

    async def search_crypto_by_text(self, text, page, quantity):
        """Search cryptos by name or symbol with pagination."""
        try:
            liste  = await self.get_liste_crypto_updated()
            # return liste[:10]
            # async with aiofiles.open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
            #     liste = json.loads(await f.read())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Crypto info file not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse crypto info: {e}")

        # Apply filtering first
        if text:
            liste = [item for item in liste if text.lower() in item["name"].lower() or text.lower() in item["symbol"].lower()]

        # Separate by market_cap presence
        with_market_cap = [coin for coin in liste if coin["market_cap"] is not None]
        without_market_cap = [coin for coin in liste if coin["market_cap"] is None]

        # Sort only the ones with market_cap
        with_market_cap.sort(key=lambda x: x["market_cap"], reverse=True)

        # Combine with market cap coins first, then those without
        liste = with_market_cap + without_market_cap

        quantite_de_donnees = len(liste)
        nombre_de_page = -(-quantite_de_donnees // quantity)
        liste = liste[(page - 1) * quantity:page * quantity]

        # update price of liste from historique of each crypto
        for item in liste:
            if self.check_if_crypto_in_binance != False:
                break
            
            try:
                async with aiofiles.open(f'app/json/crypto/prix/{item["id"]}_prix.json', 'r', encoding='utf-8') as f:
                    data = await f.read()
                data = json.loads(data)
                if data:
                    item["current_price"] = data[-1]["price"]
            except (FileNotFoundError, json.JSONDecodeError):
                item["current_price"] = 0
        
        return {
            "quantite_de_donnees": quantite_de_donnees,
            "nombre_de_page": nombre_de_page,
            "page": page,
            "liste": liste,
        }


    async def refresh_price_one_crypto(self, crypto, liste_crypto_nofilter):
        """Update price for a single crypto and append to price history."""
        price = -1
        for item in liste_crypto_nofilter:
            if crypto["name"].lower() == item["name"].lower() or crypto["symbol"].lower() == item["symbol"].lower():
                crypto["current_price"] = item["current_price"]
                price = item["current_price"]
                break

        if price <= 0:
            return crypto

        new_data = {
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "price": price,
        }

        file_path = f'app/json/crypto/prix/{crypto["id"]}_prix.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(new_data)
        os.makedirs('app/json/crypto/prix', exist_ok=True)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))
        return True

    async def refresh_price_crypto(self):
        """Refresh prices for all cryptos."""
        liste_crypto = await callCoinMarketApi.get_liste_crypto_unfiltered()
        liste_crypto_nofilter = (await self.get_liste_crypto_nofilter(1, 15000))["liste"]

        
        liste_non_maj = []
        for item in liste_crypto_nofilter:
            result = await self.refresh_price_one_crypto(item, liste_crypto)
            if result is not True:
                liste_non_maj.append(item)

        await self.update_price_for_liste_Not_Maj(liste_non_maj)

        os.makedirs('app/json/crypto/info', exist_ok=True)
        async with aiofiles.open('app/json/crypto/info/crypto.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_crypto_nofilter, indent=4, ensure_ascii=False))

        print("crypto price updated")
        return "crypto price updated"

    async def update_price_for_liste_Not_Maj(self, liste):
        """Update prices for a list of cryptos not updated in initial refresh."""
        numberRequest = (len(liste) // 250) + 1
        for i in range(numberRequest):
            start = i * 250
            end = min(start + 250, len(liste))
            liste_used = liste[start:end]
            listeIds = ','.join(item["id"] for item in liste_used)

            liste_data = await coinGeckoService.get_last_Data(listeIds)
            for item in liste_used:
                price = liste_data.get(item["id"], {}).get("usd")
                if price:
                    item["current_price"] = price
                    await self.update_price(price, item["id"])

    async def update_price(self, price, id):
        """Append a new price entry for a crypto."""
        new_data = {
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "price": price,
        }

        file_path = f'app/json/crypto/prix/{id}_prix.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(new_data)
        os.makedirs('app/json/crypto/prix', exist_ok=True)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def set_crypto_coin_gecko_correled_with_binance(self):
        """Correlate CoinGecko cryptos with Binance symbols and save to JSON."""
        liste_coin_gecko = await coinGeckoService.get_liste_crypto_nofilter()
        liste_coin_gecko = list({v['id']: v for v in liste_coin_gecko}.values())
        liste_binance = await binanceService.get_symbols_from_json()

        liste_crypto = []
        for item in liste_coin_gecko:
            for item2 in liste_binance[:]:  # Copy to allow removal
                if item["symbol"].lower() == item2["baseAsset"].lower():
                    liste_crypto.append(item)
                    liste_binance.remove(item2)
                    break

        os.makedirs('app/json/crypto/info', exist_ok=True)
        async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_crypto, indent=4, ensure_ascii=False))
        return liste_crypto

    async def get_liste_crypto_binance(self):
        """Retrieve list of cryptos available on Binance."""
        try:
            async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'r', encoding='utf-8') as f:
                liste = json.loads(await f.read())
            return sorted(liste, key=lambda x: x["market_cap"], reverse=True)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Binance crypto list not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Binance crypto list: {e}")

    async def check_if_crypto_in_binance(self, id):
        """Check if a crypto is available on Binance."""
        liste_binance = await self.get_liste_crypto_binance()
        for crypto in liste_binance:
            if crypto["id"] == id:
                return crypto
        return False

    async def get_liste_price_binance_from_json(self, crypto):
        """Read Binance price history for a crypto from JSON."""
        symbole = crypto.get("symbol", "").lower()
        try:
            async with aiofiles.open(f'app/json/crypto/websocket_price/{symbole}usdt_price.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            return json.loads(data)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Binance price data for {symbole} not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Binance price data: {e}")
        
    async def bitcoin_dominace(self,liste_crypto):
        """Schedule Bitcoin dominance data retrieval."""
        try:
            liste = []
            liste = await self.get_bitcoin_dominace()
            # Check if the last data is older than 1 day
            if liste:
                last_date = datetime.strptime(liste[-1]["date"], "%Y-%m-%d")
                if (datetime.now() - last_date).days < 1:
                    return "Bitcoin dominance data is up to date"
            
            
            
            
            # get 
            market_cap_total = 0
            for crypto in liste_crypto:
                market_cap_total += crypto.get("market_cap", 0)
            bitcoin_dominance = 0
            ethereum_dominance = 0
            i = 0
            for crypto in liste_crypto:
                if i >= 2:
                    break
                if crypto.get("id") == "ethereum":
                    ethereum_dominance = crypto.get("market_cap", 0) / market_cap_total * 100
                    i += 1
                if crypto.get("id") == "bitcoin":
                    bitcoin_dominance = crypto.get("market_cap", 0) / market_cap_total * 100
                    i += 1
            
            
            other_percentage = 100 - bitcoin_dominance - ethereum_dominance
            bitcoin_dominance = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "bitcoin": bitcoin_dominance,
                "ethereum": ethereum_dominance,
                "others": other_percentage
            }
            
            liste.append(bitcoin_dominance)
            # Save to JSON
            os.makedirs('app/json/crypto/bitcoin_dominance', exist_ok=True)
            async with aiofiles.open('app/json/crypto/bitcoin_dominance/bitcoin_dominance.json', 'w', encoding='utf-8') as f:
                await f.write(json.dumps(liste, indent=4, ensure_ascii=False))
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating Bitcoin dominance: {str(e)}")
    
    async def schedule_bitcoin_dominace(self):
        """Schedule Bitcoin dominance data retrieval."""
        try:
            # get 
            val =await coinGeckoService.get_liste_crypto_with_weight()
            return await self.bitcoin_dominace(val)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating Bitcoin dominance: {str(e)}")
    
    async def get_bitcoin_dominace(self):
        """Get Bitcoin dominance data."""
        try:
            async with aiofiles.open('app/json/crypto/bitcoin_dominance/bitcoin_dominance.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            return json.loads(data)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Bitcoin dominance data not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Bitcoin dominance data: {e}")
    
    async def get_bit_coin_dominace_between_2_dates(self, date_start, date_end):
        """Retrieve Bitcoin dominance data between two dates."""
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%d")
        if date_start is None:
            raise HTTPException(status_code=400, detail="date_start is required")
        
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")

        try:
            async with aiofiles.open('app/json/crypto/bitcoin_dominance/bitcoin_dominance.json', 'r', encoding='utf-8') as f:
                data = await f.read()
            liste = json.loads(data)
            return [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Bitcoin dominance data not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Bitcoin dominance data: {e}")
    
    async def get_liste_crypto_updated(self):
        
        try:
            # get liste crypto updated by binance
            async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'r', encoding='utf-8') as f:
                liste_binace = json.loads(await f.read())
            # get liste crypto updated by coinGecko and coinMarketCap
            async with aiofiles.open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
                liste_coinGecko = json.loads(await f.read())
            
            liste = liste_binace
            
            
            for item in liste_coinGecko:
                i =0
                for item2 in liste_binace:
                    if item["id"] == item2["id"]:
                        item2["market_cap"] = item["market_cap"]
                        item2["volume_24h"] = item["volume_24h"]
                        # item2["price_change_percentage_24h"] = item["price_change_percentage_24h"]
                        i+=1
                        break
                if i == 0:
                    liste.append(item)
            
            return liste
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Crypto list file not found")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse crypto list: {e}")
    
    async def get_liste_crypto_with_weight(self):
        async with aiofiles.open('app/json/liste_crypto/listeCryptoWithWeight.json', 'r', encoding='utf-8') as f:
            liste = json.loads(await f.read())
        
        async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'r', encoding='utf-8') as f:
            liste_binace = json.loads(await f.read())
        
        liste_no_filter = await self.get_liste_crypto_nofilter(1,1000)
        liste_no_filter = liste_no_filter["liste"]
        
        for el in liste:
            i =0
            for el2 in liste_binace:
                if el['id'] == el2['id']:
                    # el['volume_24h'] = el2['volume_24h']
                    el['current_price'] = el2['current_price']
                    el['price_change_percentage_24h'] = el2['price_change_percentage_24h']
                    i+=1
                    
            
            for el2 in liste_no_filter:
                if el['id'] == el2['id']:
                    el['volume_24h'] = el2['volume_24h']
                    if i==0:
                        el['current_price'] = el2['current_price']
                    el['price_change_percentage_24h'] = el2['price_change_percentage_24h']
                    break
                
        
        return liste