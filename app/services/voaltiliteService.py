from fastapi import HTTPException
from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import aiofiles
import os
import asyncio

calculService = CalculService()
coinGeckoService = CoinGeckoService()

class VolatiliteService:
    async def set_historique_volatilite(self):
        """Set historical portfolio volatility for filtered cryptos."""
        vs_currency = "usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        
        liste_crypto = []
        liste_prix = []
        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'), vs_currency, 90)
            if len(historique) > 90:
                liste_crypto.append(el)
                liste_prix.append(historique)
        
        liste_crypto = liste_crypto[:80]
        liste_prix = liste_prix[:80]
        
        liste_market_cap = [await coinGeckoService.get_market_cap(el.get("id")) for el in liste_crypto]
        liste_weight = await calculService.normalize_weights(liste_market_cap)
        liste_weight = await calculService.round_weights(liste_weight)
        
        liste_volatilite_portefeuille = []
        for i in range(len(liste_prix[0]) - 2):
            liste_prix_utiliser = [el.iloc[:-i] if i != 0 else el for el in liste_prix]
            liste_volatilite, portfolio_volatility_mat, covariance_matrix = await calculService.calculate_statistics(
                liste_prix_utiliser, liste_crypto, liste_weight
            )
            liste_volatilite_portefeuille.append(portfolio_volatility_mat)
        
        liste_volatilite = [
            {
                "date": liste_prix[0]["date"][i],
                "value": liste_volatilite_portefeuille[len(liste_volatilite_portefeuille) - i - 1]
            }
            for i in range(len(liste_volatilite_portefeuille))
        ]
        
        os.makedirs('app/json/volatilite', exist_ok=True)
        async with aiofiles.open('app/json/volatilite/volatilite.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_volatilite, indent=4, ensure_ascii=False))

    async def update_historique_volatilite_generale(self):
        """Update portfolio volatility if outdated."""
        os.makedirs('app/json/volatilite', exist_ok=True)
        try:
            async with aiofiles.open('app/json/volatilite/volatilite.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                last_element = data[-1]
        except (FileNotFoundError, json.JSONDecodeError):
            await self.set_historique_volatilite()
            return

        last_date = datetime.strptime(last_element["date"], '%Y-%m-%dT%H:%M:%S.%f')
        now = datetime.now()
        difference = (now - last_date).days

        if difference >= 2:
            vs_currency = "usd"
            liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
            liste_crypto_start = liste_crypto_start[:80]
            
            liste_crypto = []
            liste_prix = []
            for i, el in enumerate(liste_crypto_start):
                historique = await coinGeckoService.get_historical_prices(el.get('id'), vs_currency, 90)
                if len(historique) > 90:
                    liste_crypto.append(el)
                    liste_prix.append(historique[:-2])
                if i % 20 == 19:
                    await asyncio.sleep(60)  # Rate limit delay

            liste_crypto = liste_crypto[:80]
            liste_prix = liste_prix[:80]
            
            liste_market_cap = [await coinGeckoService.get_market_cap(el.get("id")) for el in liste_crypto]
            liste_weight = await calculService.normalize_weights(liste_market_cap)
            liste_weight = await calculService.round_weights(liste_weight)
            
            liste_volatilite_portefeuille = []
            for i in range(difference - 1):
                liste_prix_utiliser = [el.iloc[:-i] if i != 0 else el for el in liste_prix]
                liste_volatilite, portfolio_volatility_mat, covariance_matrix = await calculService.calculate_statistics(
                    liste_prix_utiliser, liste_crypto, liste_weight
                )
                liste_volatilite_portefeuille.append(portfolio_volatility_mat)
            
            liste_volatilite = [
                {
                    "date": liste_prix[0]["date"][len(liste_prix[0]) - difference + 1 + i],
                    "value": liste_volatilite_portefeuille[-i - 1]
                }
                for i in range(len(liste_volatilite_portefeuille))
            ]
            
            for item in liste_volatilite:
                await self.update_volatilite_annuel(item["date"], item["value"] * np.sqrt(365))
            
            async with aiofiles.open('app/json/volatilite/volatilite.json', 'r+', encoding='utf-8') as f:
                data = json.loads(await f.read())
                data += liste_volatilite
                await f.seek(0)
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def get_historique_volatilite_from_json(self, date_debut=None, date_fin=None):
        """Retrieve historical volatility within a date range."""
        if date_debut is None:
            date_debut = "2024-11-29T00:00:00.000"
        if date_fin is None:
            date_fin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        try:
            async with aiofiles.open('app/json/volatilite/volatilite.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                liste = [el for el in data if date_debut <= el["date"] <= date_fin]
                liste.sort(key=lambda x: x.get("date"))
                return liste
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid volatility data")

    async def get_last_volatilite_from_json(self):
        """Retrieve the latest volatility."""
        try:
            async with aiofiles.open('app/json/volatilite/volatilite.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                return data[-1]
        except (FileNotFoundError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="Volatility data not found")

    async def set_volatilite_journaliere_crypto(self):
        """Placeholder for setting daily crypto volatility."""
        pass

    async def calcul_Volatillite_Journaliere_one_crypto(self, listePrix):
        """Calculate daily volatility for a single crypto."""
        listePrix = pd.DataFrame(listePrix, columns=['date', 'price'])
        listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))
        listePrix.dropna(inplace=True)
        return listePrix['log_return'].std()

    async def get_historique_Volatilite(self, listePrix):
        """Calculate historical volatility series."""
        listeVolatilite = []
        for i in range(len(listePrix) - 2):
            price = listePrix if i == 0 else listePrix[:-i]
            volatilite = await self.calcul_Volatillite_Journaliere_one_crypto(price)
            listeVolatilite.append(volatilite)
        return listeVolatilite

    async def set_historique_volatiltie_for_each_crypto_to_json(self):
        """Set historical volatility for each crypto."""
        vs_currency = "usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        liste_crypto = []
        liste_prix = []

        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'), vs_currency, 90)
            if len(historique) > 90:
                liste_crypto.append(el)
                liste_prix.append(historique)
                historique_volatilite = await self.get_historique_Volatilite(historique)
                historique_volatilite_crypto = [
                    {
                        "date": historique["date"][i],
                        "value": historique_volatilite[-i]
                    }
                    for i in range(1, len(historique[:-2]))
                ]
                historique_volatilite_crypto = await self.delete_duplicate_date(historique_volatilite_crypto)
                
                os.makedirs('app/json/volatilite', exist_ok=True)
                async with aiofiles.open(
                    f'app/json/volatilite/{el.get("id")}_volatilite.json', 'w', encoding='utf-8'
                ) as f:
                    await f.write(json.dumps(historique_volatilite_crypto, indent=4, ensure_ascii=False))

    async def delete_duplicate_date(self, liste):
        """Remove duplicate dates from a list."""
        liste_date = []
        liste_temp = []
        for el in liste:
            if el["date"] not in liste_date:
                liste_date.append(el["date"])
                liste_temp.append(el)
        return liste_temp

    async def update_historique_volatilite_for_one_crypto(self, id):
        """Update historical volatility for a single crypto."""
        file_path = f'app/json/volatilite/{id}_volatilite.json'
        os.makedirs('app/json/volatilite', exist_ok=True)

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            return await self.set_historique_volatilite_for_one_crypto(id)

        last_element = data[-1]
        last_date = datetime.strptime(last_element["date"], '%Y-%m-%dT%H:%M:%S.%f')
        now = datetime.now()
        difference = (now - last_date).days

        if difference >= 2:
            historique = await coinGeckoService.get_historical_prices(id, "usd", 90)
            listeVolatilite = []
            for i in range(difference - 1):
                price = historique if i == 0 else historique[:-i]
                volatilite = await self.calcul_Volatillite_Journaliere_one_crypto(price)
                listeVolatilite.append(volatilite)
            
            liste_volatilite = [
                {
                    "date": historique["date"][len(historique[:-2]) - difference + i + 1],
                    "value": listeVolatilite[-i - 1]
                }
                for i in range(len(listeVolatilite))
            ]
            
            data += liste_volatilite
            data = await self.delete_duplicate_date(data)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
        
        return data

    async def update_historique_volatilite_for_each_crypto(self):
        """Update historical volatility for all cryptos."""
        vs_currency = "usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        now = datetime.now()

        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'), vs_currency, 90)
            if len(historique) <= 90:
                continue
            
            file_path = f'app/json/volatilite/{el.get("id")}_volatilite.json'
            os.makedirs('app/json/volatilite', exist_ok=True)
            
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                    data = await self.delete_duplicate_date(data)
            except (FileNotFoundError, json.JSONDecodeError):
                await self.set_historique_volatilite_for_one_crypto(el.get('id'))
                continue

            last_element = data[-1]
            last_date = datetime.strptime(last_element["date"], '%Y-%m-%dT%H:%M:%S.%f')
            difference = (now - last_date).days

            if difference >= 2:
                listeVolatilite = []
                for i in range(difference - 1):
                    price = historique if i == 0 else historique[:-i]
                    volatilite = await self.calcul_Volatillite_Journaliere_one_crypto(price)
                    listeVolatilite.append(volatilite)
                
                liste_volatilite = [
                    {
                        "date": (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                        "value": listeVolatilite[i]
                    }
                    for i in range(len(listeVolatilite))
                ]
                
                data += liste_volatilite
                data = await self.delete_duplicate_date(data)
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def get_historique_volatilite_crypto_from_json(self, id, date_start="2024-11-29T00:00:00.000", date_end=None):
        """Retrieve historical volatility for a crypto within a date range."""
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        file_path = f'app/json/volatilite/{id}_volatilite.json'
        today = datetime.now().date()
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                last_date = datetime.strptime(data[-1]["date"], '%Y-%m-%dT%H:%M:%S.%f').date()
                if (today - last_date).days >= 2:
                    data = await self.update_historique_volatilite_for_one_crypto(id)
                
                liste = [el for el in data if date_start <= el["date"] <= date_end]
                liste.sort(key=lambda x: x.get("date"))
                return liste
        except FileNotFoundError:
            data = await self.set_historique_volatilite_for_one_crypto(id)
            liste = [el for el in data if date_start <= el["date"] <= date_end]
            liste.sort(key=lambda x: x.get("date"))
            return liste
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Invalid volatility data for {id}")

    async def set_historique_volatilite_for_one_crypto(self, id):
        """Set historical volatility for a single crypto."""
        vs_currency = "usd"
        historique = await coinGeckoService.get_historical_prices(id, vs_currency, 90)
        
        if len(historique) > 10:
            historique_volatilite = await self.get_historique_Volatilite(historique)
            historique_volatilite_crypto = [
                {
                    "date": str(historique["date"][i]),
                    "value": historique_volatilite[-i]
                }
                for i in range(1, len(historique[:-2]))
            ]
            
            file_path = f'app/json/volatilite/{id}_volatilite.json'
            os.makedirs('app/json/volatilite', exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(historique_volatilite_crypto, indent=4, ensure_ascii=False))
            return historique_volatilite_crypto
        raise HTTPException(status_code=403, detail="Crypto too young for volatility history")

    async def get_top_10_volatilite_crypto(self):
        """Retrieve top 10 cryptos by volatility."""
        liste = await coinGeckoService.get_liste_crypto_with_weight()
        liste.sort(key=lambda x: x.get("volatiliteJournaliere", 0), reverse=True)
        return liste[:10]

    async def set_volatilite_annuel(self):
        """Set annualized volatility."""
        os.makedirs('app/json/volatilite/volatilite_annuel', exist_ok=True)
        async with aiofiles.open('app/json/volatilite/volatilite.json', 'r', encoding='utf-8') as f:
            data = json.loads(await f.read())
            liste = [{"date": el["date"], "value": el["value"] * np.sqrt(365)} for el in data]
        
        async with aiofiles.open(
            'app/json/volatilite/volatilite_annuel/historique.json', 'w', encoding='utf-8'
        ) as f:
            await f.write(json.dumps(liste, indent=4, ensure_ascii=False))

    async def update_volatilite_annuel(self, date, value):
        """Update annualized volatility."""
        os.makedirs('app/json/volatilite/volatilite_annuel', exist_ok=True)
        file_path = 'app/json/volatilite/volatilite_annuel/historique.json'
        try:
            async with aiofiles.open(file_path, 'r+', encoding='utf-8') as f:
                data = json.loads(await f.read())
                data.append({"date": date, "value": value})
                await f.seek(0)
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
        except (FileNotFoundError, json.JSONDecodeError):
            data = [{"date": date, "value": value}]
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def get_volatilite_annuel_historique(self, date_debut, date_fin):
        """Retrieve annualized volatility history."""
        if date_debut is None:
            raise HTTPException(status_code=400, detail="date_debut cannot be null")
        if date_fin is None:
            date_fin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_debut > date_fin:
            raise HTTPException(status_code=400, detail="date_debut must be less than date_fin")

        file_path = 'app/json/volatilite/volatilite_annuel/historique.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                liste = [el for el in data if date_debut <= el["date"] <= date_fin]
                liste.sort(key=lambda x: x.get("date"))
                return liste
        except (FileNotFoundError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="Annual volatility data not found")

    async def set_historique_volatilite_annuel_per_cryto(self):
        """Set annualized volatility for each crypto."""
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        
        for el in liste_crypto_start:
            file_path = f'app/json/volatilite/volatilite_annuel/crypto/{el.get("id")}_volatilite_annuel.json'
            try:
                async with aiofiles.open(f'app/json/volatilite/{el.get("id")}_volatilite.json', 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                    liste = [{"date": vol["date"], "value": vol["value"] * np.sqrt(365)} for vol in data]
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(liste, indent=4, ensure_ascii=False))
            except FileNotFoundError:
                continue
        return "volatilite annuel set"

    async def get_volatilite_annuel_for_one_crypto(self, id, date_start, date_end):
        """Retrieve annualized volatility for a crypto."""
        if date_start is None:
            raise HTTPException(status_code=400, detail="date_start cannot be null")
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start must be less than date_end")

        file_path = f'app/json/volatilite/volatilite_annuel/crypto/{id}_volatilite_annuel.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                liste = [el for el in data if date_start <= el["date"] <= date_end]
                liste.sort(key=lambda x: x.get("date"))
                return liste
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Annual volatility not found for {id}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Invalid data for {id}")