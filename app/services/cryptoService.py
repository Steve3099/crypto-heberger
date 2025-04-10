import json
import os
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.binanceService import BinanceService

from fastapi import HTTPException
from datetime import datetime
coinGeckoService = CoinGeckoService()
callCoinMarketApi = CallCoinMarketApi()
binanceService = BinanceService()

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
    
    async def get_liste_prix_from_json(self,id):
        with open('app/json/crypto/prix/'+id+'_prix.json', 'r') as f:
            data = f.read()
            # return as a json
            
            liste = json.loads(data)
            # return liste
            liste_prix = []
            for item in liste:
                liste_prix.append(item)
            
            return liste_prix
    
    async def get_liste_prix_between_2_dates(self,id,date_start,date_end):
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        
        
        liste = await self.get_liste_prix_from_json(id)
        
        # filter the liste by date
        liste = [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        
        return liste
        
    
    async def get_price_range(self,id,date_start,date_end):
        
        
        # check if date_start < date_end
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        liste = await self.get_liste_prix_from_json(id)
        # transform liste which is a data frame to json
        
        liste = [item for item in liste if item["date"] >= date_start and item["date"] <= date_end]
        
        # get max price and min price
        max_price = 0
        min_price = 1000000000000
        for price in liste:
            if price["price"] > max_price:
                max_price = price["price"]
            if price["price"] < min_price:
                min_price = price["price"]
        
        return {
            "max_price":max_price,
            "min_price":min_price
        }
    
    async def get_historique_market_cap(self,id,date_start,date_end):
        
        # check if date_start < date_end
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        # read json file
        try:
            with open('app/json/crypto/market_cap/'+id+'_market_cap.json', 'r') as f:
                
                data = f.read()
                # return as a json
                
                liste = json.loads(data)
                liste_market_cap = []
                for item in liste:
                    if item["date"] >= date_start and item["date"] <= date_end:
                        liste_market_cap.append(item)
                
                return liste_market_cap
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Market cap for crypto with ID '{id}' not found")
        
        return liste
    
    async def set_historique_market_cap_generale(self):
        liste_crypto = await self.get_liste_crypto_from_json()
        liste_market_cap_history = []
        somme_market_cap=0
        liste_crypto_used = []
        for crypto in liste_crypto:
            with open('app/json/crypto/market_cap/'+crypto["id"]+'_market_cap.json', 'r') as f:
                data = f.read()
                liste = json.loads(data)
                if len(liste) < 90:
                    continue
                liste_crypto_used.append(crypto)
                liste_market_cap_history.append(liste)
        liste_somme_arket_cap = []
        print(len(liste_crypto_used))
        for i in range(len(liste_market_cap_history[0])):
            market_cap =0
            for j in range(len(liste_crypto_used)):
                market_cap += liste_market_cap_history[j][i]["market_cap"]
            data = {
                "date":liste_market_cap_history[0][i]["date"],
                "market_cap":market_cap
            }
            # do not add if hh:mm:ss is not 00:00:00
            if data["date"].split("T")[1] != "00:00:00.000":
                continue
            liste_somme_arket_cap.append(data)
        with open('app/json/crypto/market_cap/generale/historique_market_cap_generale.json', 'w') as f:
            json.dump(liste_somme_arket_cap, f, indent=4, ensure_ascii=False)
            # f.write(json.dumps(liste_somme_arket_cap))
        
        return "market_cap generale done"
    
    async def set_historique_volume_generale(self):
        liste_crypto = await self.get_liste_crypto_from_json()
        liste_volume_history = []
        somme_market_cap=0
        liste_crypto_used = []
        for crypto in liste_crypto:
            with open('app/json/crypto/volume/'+crypto["id"]+'_volume.json', 'r') as f:
                data = f.read()
                liste = json.loads(data)
                if len(liste) < 90:
                    continue
                liste_crypto_used.append(crypto)
                liste_volume_history.append(liste)
        liste_somme_volume = []
        print(len(liste_crypto_used))
        for i in range(len(liste_volume_history[0])):
            volume =0
            for j in range(len(liste_crypto_used)):
                volume += liste_volume_history[j][i]["volume"]
            data = {
                "date":liste_volume_history[0][i]["date"],
                "volume":volume
            }
            # do not add if hh:mm:ss is not 00:00:00
            if data["date"].split("T")[1] != "00:00:00.000":
                continue
            liste_somme_volume.append(data)
        with open('app/json/crypto/volume/generale/historique_volume_generale.json', 'w') as f:
            json.dump(liste_somme_volume, f, indent=4, ensure_ascii=False)
            # f.write(json.dumps(liste_somme_arket_cap))
        
        return "market_cap generale done"
    
    async def get_volume_generale_between_2_date(self,date_start,date_end):
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        with open('app/json/crypto/volume/generale/historique_volume_generale.json', 'r') as f:
            data = f.read()
            liste = json.loads(data)
            liste_volume = []
            for item in liste:
                if item["date"] >= date_start and item["date"] <= date_end:
                    liste_volume.append(item)
            
            return liste_volume
    async def get_marketcap_generale_between_2_date(self,date_start,date_end):
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start should be less than date_end")
        
        with open('app/json/crypto/market_cap/generale/historique_market_cap_generale.json', 'r') as f:
            data = f.read()
            liste = json.loads(data)
            liste_market_cap = []
            for item in liste:
                if item["date"] >= date_start and item["date"] <= date_end:
                    liste_market_cap.append(item)
            
            return liste_market_cap
    
    async def set_info_one_crypto(self,id,info):
        
        with open('app/json/crypto/info/'+id+'_info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
            # f.write(json.dumps(info))
        return "info "+id+" done"
    
    async def set_info_crypto(self):
        liste_coin_getcko = await coinGeckoService.set_liste_no_folter_to_json()
        liste_coin_market_cap = await callCoinMarketApi.get_liste_cypto_ufiltered()
        
        liste_crypto = []
        for item in liste_coin_getcko:
            for item2 in liste_coin_market_cap:
                # ignore case in comparaison majuscule/minuscule
                if item["name"].lower() == item2["name"].lower() or item["symbol"].lower() == item2["symbol"].lower():
                    item["volume_24h"] = item2["volume_24h"]
                    liste_crypto.append(item)
                    # await self.set_info_one_crypto(item["id"],item)
                    break
        
        # drop crypto with duplica id
        liste_crypto = list({v['id']:v for v in liste_crypto}.values())
        
        with open('app/json/crypto/info/crypto.json', 'w', encoding='utf-8') as f:
            json.dump(liste_crypto, f, indent=4, ensure_ascii=False)
            # f.write(json.dumps(info))
    
    async def get_liste_crypto_nofilter(self,page,quantity):
        with open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
            liste1 = json.load(f)
        # order by market cap
        liste = sorted(liste1, key=lambda x: x["market_cap"], reverse=True)
        
        # get the page
        quantite_de_donnees = len(liste)
        # round up
        
        nombre_de_page = -(-len(liste) // quantity) 
        liste = liste[(page-1)*quantity:page*quantity]
        
        page = page
        return {
            "quantite_de_donnees":quantite_de_donnees,
            "nombre_de_page":nombre_de_page,
            "page":page,
            "liste":liste
        }
        
    async def get_fear_and_greed_from_json(self):
        with open('app/json/fearAndGreed/fearAndGreed.json', 'r') as f:
            data = f.read()
            return json.loads(data)
    
    async def search_crypto_by_text(self,text,page,quantity):
        with open('app/json/crypto/info/crypto.json', 'r', encoding='utf-8') as f:
            liste1 = json.load(f)
        liste = []
        liste = sorted(liste1, key=lambda x: x["market_cap"], reverse=True)
        if text is not None:
            liste = [item for item in liste1 if text.lower() in item["name"].lower() or text.lower() in item["symbol"].lower()]
        
        quantite_de_donnees = len(liste)
        nombre_de_page = -(-len(liste) // quantity) 
        liste = liste[(page-1)*quantity:page*quantity]
        page = page
        return {
            "quantite_de_donnees":quantite_de_donnees,
            "nombre_de_page":nombre_de_page,
            "page":page,
            "liste":liste
        }
        
    async def set_historique_volume_generale(self):
        liste_crypto = await self.get_liste_crypto_from_json()
        liste_market_cap_history = []
        somme_market_cap=0
        liste_crypto_used = []
        for crypto in liste_crypto:
            with open('app/json/crypto/volume/'+crypto["id"]+'_volume.json', 'r') as f:
                data = f.read()
                liste = json.loads(data)
                if len(liste) < 90:
                    continue
                liste_crypto_used.append(crypto)
                liste_market_cap_history.append(liste)
        liste_somme_arket_cap = []
        for i in range(len(liste_market_cap_history[0])):
            market_cap =0
            for j in range(len(liste_crypto_used)):
                market_cap += liste_market_cap_history[j][i]["volume"]
            data = {
                "date":liste_market_cap_history[0][i]["date"],
                "volume":market_cap
            }
            # do not add if hh:mm:ss is not 00:00:00
            if data["date"].split("T")[1] != "00:00:00.000":
                continue
            liste_somme_arket_cap.append(data)
        with open('app/json/crypto/market_cap/generale/historique_market_cap_generale.json', 'w') as f:
            json.dump(liste_somme_arket_cap, f, indent=4, ensure_ascii=False)
            # f.write(json.dumps(liste_somme_arket_cap))
        
        return "market_cap generale done"
    async def refresh_price_one_crypto(self,crypto,liste_crypto_nofilter):
        new_data = {}
        price = -1
        val = 0
        for item in liste_crypto_nofilter:
            if crypto["name"].lower() == item["name"].lower() or crypto["symbol"].lower() == item["symbol"].lower():
                crypto["current_price"] = item["current_price"]
                price = item["current_price"]
                break
        
        if price <= 0:
            val += 1
            price = await coinGeckoService.get_last_Data(crypto["id"])
        
        new_data = {
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "price": price
        }
        #put data to botome of json file
        data = []
        try:
            file_path = f'app/json/crypto/prix/{crypto["id"]}_prix.json'
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
                
        except FileNotFoundError:
            # write to json file
            data =[]
        data.append(new_data)
        with open('app/json/crypto/prix/'+crypto["id"]+'_prix.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return val
    async def refresh_price_crypto(self):
        liste_crypto = await callCoinMarketApi.get_liste_cypto_ufiltered()
        
        liste_crypto_nofilter = await self.get_liste_crypto_nofilter(1,15000)
        
        liste_crypto_nofilter = liste_crypto_nofilter["liste"]
        for item in liste_crypto_nofilter:
            await self.refresh_price_one_crypto(item,liste_crypto)
        print("crypto price updated")
        
        with open('app/json/crypto/info/crypto.json', 'w', encoding='utf-8') as f:
            json.dump(liste_crypto_nofilter, f, indent=4, ensure_ascii=False)
    
    
    async def set_crypto_coin_gecko_correled_with_binance(self):
        liste_coin_gecko = await coinGeckoService.get_liste_crypto_nofilter()
        
        # remove duplicate crypto from liste_coin_gecko
        liste_coin_gecko = list({v['id']:v for v in liste_coin_gecko}.values())
        
        liste_binance = await binanceService.get_symbols_from_json()
        
        liste_crypto = []
        
        for item in liste_coin_gecko:
            i = 0
            for item2 in liste_binance:
                
                # remothe the usdt at the end of item2
                # item2 = item2.replace("usdt","")
                
                if item["symbol"].lower() == item2["baseAsset"].lower():
                    
                    # print(item["symbol"].lower(),item2["baseAsset"].lower())
                    liste_crypto.append(item)
                    #remove item2 from liste_binance
                    liste_binance.remove(item2)
                    i = 1
                    break     
        # put liste crypto to json file
        with open('app/json/crypto/info/crypto_binance.json', 'w', encoding='utf-8') as f:
            json.dump(liste_crypto, f, indent=4, ensure_ascii=False)
        # print(len(liste_binance))
        return liste_crypto
            
    