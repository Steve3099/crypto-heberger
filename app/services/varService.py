from app.services.cryptoService import CryptoService
from app.services.coinGeckoService import CoinGeckoService
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os
import aiofiles
from fastapi import HTTPException

coinGeckoService = CoinGeckoService()
cryptoService = CryptoService()

class VarService:
    def __init__(self):
        pass

    async def calculate_var(self, liste_price, liste_crypto, list_weight, percentile=1):
        """Calculate VaR for a portfolio and individual cryptos."""
        merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("id")})
        for i in range(1, len(liste_price)):
            liste_price[i]['date'] = pd.to_datetime(liste_price[i]['date'])
            merged['date'] = pd.to_datetime(merged['date'])
            liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("id")})
            merged = pd.merge(merged, liste_price[i], on='date')

        new_columns = {}
        for crypto in liste_crypto:
            crypto_id = crypto.get("id")
            new_columns[crypto_id] = np.log(
                merged[f'price_{crypto_id}'] / merged[f'price_{crypto_id}'].shift(1)
            )
        merged = pd.concat([merged, pd.DataFrame(new_columns)], axis=1).copy()
        merged.dropna(inplace=True)
        merged.fillna(0, inplace=True)

        # Calculate portfolio returns
        val = sum(list_weight[i] * merged[liste_crypto[i].get("id")] for i in range(len(list_weight)))
        merged['portfolio_return'] = val

        # Calculate VaR
        var_percentile_portfolio = np.percentile(merged['portfolio_return'], percentile)
        liste_var_percentile_crypto = [
            np.percentile(merged[crypto.get("id")], percentile) for crypto in liste_crypto
        ]

        return liste_var_percentile_crypto, var_percentile_portfolio

    async def get_Var_for_each_crypto(self):
        """Calculate VaR for filtered cryptos and their portfolio."""
        vs_currency = "usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        liste_prix = []
        liste_market_cap = []
        somme_market_cap = 0
        liste_crypto = []

        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'), vs_currency, 90)
            if len(historique) > 90:
                liste_crypto.append(el)
                liste_prix.append(historique)
                market_cap = await coinGeckoService.get_market_cap(el.get("id"))
                liste_market_cap.append(market_cap)
                somme_market_cap += market_cap

        if not liste_crypto:
            raise HTTPException(status_code=404, detail="No valid crypto data found")

        liste_weight = [market_cap / somme_market_cap for market_cap in liste_market_cap]
        liste_var, var_portfolio = await self.calculate_var(liste_prix, liste_crypto, liste_weight, percentile=1)
        return liste_var, var_portfolio, liste_weight, liste_crypto

    async def update_var(self):
        """Update portfolio and crypto VaR data."""
        os.makedirs('app/json/var/generale', exist_ok=True)
        os.makedirs('app/json/var/weight', exist_ok=True)
        os.makedirs('app/json/var/historique', exist_ok=True)

        # Read last VaR date
        try:
            async with aiofiles.open('app/json/var/generale/var.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                last_date = data[-1].get("date") if isinstance(data, list) else data.get("date")
        except (FileNotFoundError, json.JSONDecodeError):
            last_date = None

        today = datetime.now().strftime("%Y-%m-%d")
        if last_date != today:
            liste_var, var_portfolio, liste_weight, liste_crypto = await self.get_Var_for_each_crypto()

            # Update generale/var.json
            dataVar = {"date": today, "var": var_portfolio}
            async with aiofiles.open('app/json/var/generale/var.json', 'r+', encoding='utf-8') as f:
                try:
                    data = json.loads(await f.read())
                    if not isinstance(data, list):
                        data = [data]
                except (json.JSONDecodeError, FileNotFoundError):
                    data = []
                data.append(dataVar)
                await f.seek(0)
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))

            # Update weight files
            for i, crypto in enumerate(liste_crypto):
                file_path = f'app/json/var/weight/{crypto.get("id")}_weight.json'
                data_weight = {"date": today, "weight": liste_weight[i]}
                async with aiofiles.open(file_path, 'r+', encoding='utf-8') as f:
                    try:
                        data = json.loads(await f.read())
                        if not isinstance(data, list):
                            data = [data]
                    except (json.JSONDecodeError, FileNotFoundError):
                        data = []
                    data.append(data_weight)
                    await f.seek(0)
                    await f.write(json.dumps(data, indent=4, ensure_ascii=False))

            # Update VaR files
            for i, crypto in enumerate(liste_crypto):
                file_path = f'app/json/var/historique/{crypto.get("id")}_var.json'
                data_var = {"date": today, "var": liste_var[i]}
                async with aiofiles.open(file_path, 'r+', encoding='utf-8') as f:
                    try:
                        data = json.loads(await f.read())
                        if not isinstance(data, list):
                            data = [data]
                    except (json.JSONDecodeError, FileNotFoundError):
                        data = []
                    data.append(data_var)
                    await f.seek(0)
                    await f.write(json.dumps(data, indent=4, ensure_ascii=False))

            return {"message": "var updated"}
        return {"message": "var already updated"}

    async def get_var_portfeuille(self):
        """Retrieve the latest portfolio VaR."""
        try:
            async with aiofiles.open('app/json/var/generale/var.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                return data[-1].get("var") if isinstance(data, list) else data.get("var")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=404, detail=f"Portfolio VaR data not found: {str(e)}")

    async def get_var_crypto(self, id):
        """Retrieve the latest VaR for a crypto."""
        file_path = f'app/json/var/historique/{id}_var.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                return data[-1].get("var") if isinstance(data, list) else data.get("var")
        except FileNotFoundError:
            return await self.calcul_var_one_crypto(id)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid VaR data for {id}: {str(e)}")

    async def calculate_var_v2(self, prices_list, crypto_names, percentile=1):
        """Calculate VaR for multiple cryptocurrencies."""
        var_results = {}
        for i, prices in enumerate(prices_list):
            crypto_name = crypto_names[i].get("id")
            prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
            prices.dropna(inplace=True)
            if len(prices['log_return']) > 1:
                var_percentile = np.percentile(prices['log_return'], percentile, method='lower')
                var_results[crypto_name] = var_percentile
        return var_results

    async def calcul_var_one_crypto(self, id, percentile=1):
        """Calculate VaR for a single cryptocurrency."""
        liste_prix = await cryptoService.get_liste_prix_from_json(id)
        if not liste_prix:
            raise HTTPException(status_code=404, detail=f"No price data for crypto {id}")

        liste_prix = pd.DataFrame(liste_prix, columns=['date', 'price'])
        liste_prix['log_return'] = np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        liste_prix.dropna(inplace=True)

        if len(liste_prix['log_return']) > 1:
            return np.percentile(liste_prix['log_return'], percentile, method='lower')
        raise HTTPException(status_code=400, detail=f"Insufficient data for VaR calculation for {id}")

    async def update_var_v2(self):
        """Update VaR for filtered cryptocurrencies."""
        liste_crypto = await coinGeckoService.get_liste_crypto_filtered()
        liste_price = []
        liste_crypto_used = []

        for el in liste_crypto:
            historique = await coinGeckoService.get_historical_prices(el.get('id'), "usd", 90)
            if len(historique) > 5:
                liste_price.append(historique)
                liste_crypto_used.append(el)

        liste_var = await self.calculate_var_v2(liste_price, liste_crypto_used, 1)
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        for item in liste_crypto_used:
            file_path = f"app/json/var/historique/{item.get('id')}_var.json"
            data = {"date": today, "var": liste_var[item.get("id")]}
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with aiofiles.open(file_path, 'r+', encoding='utf-8') as f:
                try:
                    data_list = json.loads(await f.read())
                    if not isinstance(data_list, list):
                        data_list = [data_list]
                except (json.JSONDecodeError, FileNotFoundError):
                    data_list = []
                data_list.append(data)
                await f.seek(0)
                await f.write(json.dumps(data_list, indent=4, ensure_ascii=False))

    async def set_historique_var_crypto(self, id):
        """Set historical VaR data for a cryptocurrency."""
        liste_price = await coinGeckoService.get_historical_prices(id, "usd", 90)
        liste_price = liste_price[:-2]
        liste_var = []

        for i in range(len(liste_price) - 2):
            indice = len(liste_price) - i - 1
            if indice < 3:
                break
            subset_price = liste_price.iloc[:indice]
            var = await self.calcul_var_with_price(subset_price)
            data = {
                "date": liste_price.loc[indice, "date"],
                "var": var
            }
            liste_var.append(data)

        liste_var = sorted(liste_var, key=lambda x: x.get("date"))
        file_path = f'app/json/var/historique/{id}_var.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_var, indent=4, ensure_ascii=False))
        return liste_var

    async def calcul_var_with_price(self, liste_prix, percentile=1):
        """Calculate VaR for a price list."""
        liste_prix = liste_prix.copy()
        liste_prix['log_return'] = np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        liste_prix.dropna(inplace=True)
        if len(liste_prix['log_return']) > 1:
            return np.percentile(liste_prix['log_return'], percentile, method='lower')
        raise HTTPException(status_code=400, detail="Insufficient data for VaR calculation")

    async def get_var_historique_one_crypto(self, id, date_debut, date_fin=None):
        """Retrieve historical VaR for a crypto within a date range."""
        if date_fin is None:
            date_fin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        try:
            date_formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
            
            for fmt in date_formats:
                try:
                    date_debut = datetime.strptime(date_debut, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise HTTPException(status_code=400, detail="Invalid date_debut format")

            for fmt in date_formats:
                try:
                    date_fin = datetime.strptime(date_fin, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise HTTPException(status_code=400, detail="Invalid date_fin format")
            print("here")
            if date_debut > date_fin:
                raise HTTPException(status_code=400, detail="date_debut must be less than date_fin")

            val = await self.update_var_historique(id)
            retour = [
                item for item in val
                if date_debut <= datetime.strptime(item.get("date"), "%Y-%m-%dT%H:%M:%S.%f") <= date_fin
            ]
            return retour

        except ValueError:
            raise HTTPException(status_code=400, detail="Dates must be in format %Y-%m-%dT%H:%M:%S.%f")
        except FileNotFoundError:
            val = await self.set_historique_var_crypto(id)
            retour = [
                item for item in val
                if date_debut <= datetime.strptime(item.get("date"), "%Y-%m-%dT%H:%M:%S.%f") <= date_fin
            ]
            return retour

    async def read_var_historique_for_one_crypto(self, id):
        """Read historical VaR data for a crypto."""
        file_path = f'app/json/var/historique/{id}_var.json'
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            return await self.set_historique_var_crypto(id)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid VaR data for {id}: {str(e)}")

    async def update_var_historique(self, id):
        """Update historical VaR data for a crypto."""
        liste_var = await self.read_var_historique_for_one_crypto(id)
        last_date = liste_var[-1].get("date")
        today = datetime.now().strftime("%Y-%m-%dT00:00:00.000")
        date_format = "%Y-%m-%dT00:00:00.000"
        
        last_date_dt = datetime.strptime(last_date, date_format)
        today_dt = datetime.strptime(today, date_format)
        delta = (today_dt - last_date_dt).days

        if delta > 1:
            liste_prix = await coinGeckoService.get_historical_prices(id, "usd", 90)
            liste_prix = liste_prix[:-2].iloc[::-1]  # Reverse order

            for i in range(delta - 1):
                prix_used = liste_prix[i:]
                if len(prix_used) < 3:
                    continue
                var = await self.calcul_var_with_price(prix_used)
                data = {
                    "date": (last_date_dt + timedelta(days=i + 1)).strftime("%Y-%m-%dT00:00:00.000"),
                    "var": var
                }
                liste_var.append(data)

            file_path = f'app/json/var/historique/{id}_var.json'
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(liste_var, indent=4, ensure_ascii=False))

        return liste_var
    
    async def calculate_var_historical(self,btc_prices, percentile=1):
        btc_prices['log_return'] = np.log(btc_prices['price'] / btc_prices['price'].shift(1))
        btc_returns = btc_prices['log_return'].dropna()
        var_historical = np.percentile(btc_returns, percentile, method='lower')
        return var_historical, btc_returns

    # Fonction pour calculer la VaR Monte Carlo
    async def calculate_var_monte_carlo(self,btc_returns, simulations=100000, percentile=1):
        mu = btc_returns.mean()  # Moyenne des rendements
        sigma = btc_returns.std()  # Écart-type des rendements

        # Affichage de mu et sigma
        # print(f"--- Résultats statistiques ---")
        # print(f"Moyenne (mu) des rendements : {mu:.6f}")
        # print(f"Écart-type (sigma) des rendements : {sigma:.6f}")
        
        simulated_returns = np.random.normal(mu, sigma, simulations)
        var_mc = np.percentile(simulated_returns, percentile, method='lower')
        return var_mc, simulated_returns