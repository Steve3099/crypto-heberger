from app.services.cryptoService import CryptoService
from app.services.coinGeckoService import CoinGeckoService
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os
from fastapi import HTTPException
coinGeckoService = CoinGeckoService()
cryptoService = CryptoService()

class VarService:
    def __init__(self):
        pass
    
    async def calculate_var(self,liste_price,liste_crypto,list_weight, percentile=1):
        merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("id")})
        for i in range(1, len(liste_price)):
        # Ensure the 'date' column in both DataFrames is in datetime format
            liste_price[i]['date'] = pd.to_datetime(liste_price[i]['date'])
            merged['date'] = pd.to_datetime(merged['date'])
            
            # Rename the 'price' column
            liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("id")})
        
            # Merge on the 'date' column
            merged = pd.merge(merged, liste_price[i], on='date')

        # Dictionary to store new columns
        new_columns = {}
        # return merged,0
        for crypto in liste_crypto:
            crypto_id = crypto.get("id")
            new_columns[crypto_id] = np.log(
                merged[f'price_{crypto_id}'] / merged[f'price_{crypto_id}'].shift(1)
            )
        merged = pd.concat([merged, pd.DataFrame(new_columns)], axis=1)

        # Optional: Copy the DataFrame to remove fragmentation
        merged = merged.copy()
        # Supprimer les valeurs NaN
        merged.dropna(inplace=True)
        merged.fillna(0, inplace=True)
        if merged.isna().sum().sum() > 0:
            print("Il y a encore des NaN dans merged :", merged.isna().sum())
        # return merged,0
        for i in range(len(liste_crypto)):
            merged[liste_crypto[i].get("id")] = np.log(merged['price_'+liste_crypto[i].get("id")] / merged['price_'+liste_crypto[i].get("id")].shift(1)).fillna(0) 
        # return merged,0
        # Supprimer les valeurs NaN
        merged.dropna(inplace=True)
        # Calcul des rendements journaliers du portefeuille
        val = 0
        for i in range(len(list_weight)):
            val += list_weight[i] * merged[liste_crypto[i].get("id")]
        
        merged['portfolio_return'] = val
        
        # Calcul de la VaR historique du portefeuille (percentile spécifié)
        var_percentile_portfolio = np.percentile(merged['portfolio_return'], percentile)
        
        # Calcul de la VaR historique pourtout les cypto
        liste_var_percentile_crypto = []
        for i in range(len(liste_crypto)):
            var_percentile_crypto = np.percentile(merged[liste_crypto[i].get("id")], percentile)
            liste_var_percentile_crypto.append(var_percentile_crypto)
        
        
        # var_percentile_btc = np.percentile(merged['log_return_btc'], percentile)
        # var_percentile_eth = np.percentile(merged['log_return_eth'], percentile)
        return liste_var_percentile_crypto , var_percentile_portfolio
        
    
    async def get_Var_for_each_crypto(self):
        vs_currency = "usd" 
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        liste_prix = []
        liste_market_cap =[]
        somme_market_cap = 0
        liste_crypto = []
        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
            if len(historique) > 90:
                liste_crypto.append(el)
                temp = historique
                # return temp
                liste_prix.append(historique)
                market_cap = await coinGeckoService.get_market_cap(el.get("id"))
                liste_market_cap.append(market_cap)
                somme_market_cap += market_cap
        liste_weight = []
        for market_cap in liste_market_cap:
            liste_weight.append(market_cap / somme_market_cap)
        # return liste_weight    
        liste_var, var_portfolio = await self.calculate_var(liste_prix, liste_crypto, liste_weight, percentile=1)
        # return liste_var, var_portfolio 
        return liste_var, var_portfolio,liste_weight,liste_crypto
        
    
    async def update_var(self):
        # get last date frrom var.json
        with open('app/json/var/generale/var.json') as f:
            data = json.load(f)
            # get last element of data
            data = data[-1]
            last_date = data.get("date")
        # get today date
        today = datetime.now().strftime("%Y-%m-%d")
        # if last date is not today
        if last_date != today:
            # get var for each crypto
        
            liste_var, var_portfolio,liste_weight,liste_crypto = await self.get_Var_for_each_crypto()
            liste_var = await self.calculate_var_v2(liste_prix, liste_crypto, percentile=1)
            # update var.json
            dataVar = {
                "date": today,
                "var": var_portfolio
            }
            
            # add data to botom of the liste
            with open('app/json/var/generale/var.json', 'r') as f:
                data = json.load(f)
                #  transfor data to liste if data is not a liste already
                if type(data) != list:
                    data = [data]
                data.append(dataVar)
                with open('app/json/var/generale/var.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            
            # update weight
            for i in range(len(liste_weight)):
                data = {
                    "date": today,
                    "weight": liste_weight[i]
                }
                with open('app/json/var/weight/'+liste_crypto[i].get('id')+'_wieght.json', 'r') as f:
                    data = json.load(f)
                    if type(data) != list:
                        data = [data]
                    data.append(data)
                    with open('app/json/var/weight/'+liste_crypto[i].get('id')+'_wieght.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            
            # update var
            for i in range(len(liste_var)):
                data = {
                    "date": today,
                    "var": liste_var[i]
                }
                with open('app/json/var/historique/'+liste_crypto[i].get('id')+'_var.json', 'r') as f:
                    data = json.load(f)
                    if type(data) != list:
                        data = [data]
                    data.append(data)
                    with open('app/json/var/historique/'+liste_crypto[i].get('id')+'_var.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            
            return {"message":"var updated"}
        else:
            return {"message":"var already updated"}
        
    async def get_var_portfeuille(self):
        with open('app/json/var/generale/var.json') as f:
            data = json.load(f)
            data = data[-1]
            return data.get("var")
    
    async def get_var_crypto(self,id):
        try:
            with open('app/json/var/historique/'+id+'_var.json') as f:
                data = json.load(f)
                data = data[-1]
                return data.get("var")
        except FileNotFoundError:
            return await self.calcul_var_one_crypto(id)
            raise ValueError("Crypto not found")
    
    async def calculate_var_v2(self,prices_list, crypto_names, percentile=1):
        var_results = {}
        
        for i, prices in enumerate(prices_list):
            print(len(prices))
            crypto_name = crypto_names[i].get("id")
            print(crypto_name)
            # Calculer les rendements journaliers logarithmiques
            prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
            # Supprimer les valeurs NaN
            prices.dropna(inplace=True)
            # Calcul de la VaR historique (sans interpolation)
            var_percentile = np.percentile(prices['log_return'], percentile,method='lower')
            var_results[crypto_name] = var_percentile
        
        return var_results
    
    async def calcul_var_one_crypto(self,id,percentile=1):
        # crypto_name = crypto_names[i].get("id")
        liste_prix = await cryptoService.get_liste_prix_from_json(id)
        # Calculer les rendements journaliers logarithmiques
        liste_prix['log_return'] = np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        # Supprimer les valeurs NaN
        liste_prix.dropna(inplace=True)
        # Calcul de la VaR historique (sans interpolation)
        var_percentile = np.percentile(liste_prix['log_return'], percentile,method='lower')
        return var_percentile
    
    async def update_var_v2(self):
        # get liste crypto
        liste_crypto = await coinGeckoService.get_liste_crypto_filtered()
        # get liste price
        liste_price = []
        liste_crypto_used = []
        for el in liste_crypto:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),"usd",90)
            if len(historique) > 5:
                liste_price.append(historique)
                liste_crypto_used.append(el)
        # calculate var
        liste_var = await self.calculate_var_v2(liste_price, liste_crypto_used, 1)
        # save var to json
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for item in liste_crypto_used:
            file_path = f"app/json/var/historique/{item.get('id')}_var.json"
            data = {
                "date": today,
                "var": liste_var[item.get("id")]
            }

            # Check if file exists and is not empty
            if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
                data_list = [data]  # Create a new list with the first entry
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data_list = json.load(f)
                        if not isinstance(data_list, list):  # Ensure it's a list
                            data_list = [data_list]
                    except json.JSONDecodeError:
                        data_list = []  # Handle corrupt or empty files
                data_list.append(data)  # Append the new entry

            # Write updated data back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, indent=4, ensure_ascii=False)
        
    async def set_historique_var_crypto(self, id):
        # get liste price
        liste_price = await coinGeckoService.get_historical_prices(id,"usd",90)
        liste_price = liste_price[:-2]
        liste_var = []
        for i in range(0, len(liste_price)-2):
            indice = len(liste_price) - i - 1
            if indice < 3 :
                break
            subset_price = liste_price.iloc[:len(liste_price)-i]
            var  = await self.calcul_var_with_price(subset_price)
            data = {
                "date": liste_price.loc[indice, "date"],
                "var": var
            }
            liste_var.append(data)
        # order liste_var by date croissant
        liste_var = sorted(liste_var, key=lambda x: x.get("date"))
            # write it in file
        with open('app/json/var/historique/'+id+'_var.json', 'w', encoding='utf-8') as f:
            json.dump(liste_var, f, indent=4, ensure_ascii=False)
        return liste_var
            
    
    async def calcul_var_with_price(self,liste_prix,percentile=1):
        liste_prix = liste_prix.copy() 
        liste_prix['log_return'] = np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        # Supprimer les valeurs NaN
        liste_prix.dropna(inplace=True)
        # Calcul de la VaR historique (sans interpolation)
        var_percentile = np.percentile(liste_prix['log_return'], percentile,method='lower')
        return var_percentile
    
    async def get_var_historique_one_crypto(self,id,date_debut,date_fin = None):
        try:
            if date_fin is None:
                date_fin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            #  verif date_debut and date_fin
            date_debut = datetime.strptime(date_debut, "%Y-%m-%dT%H:%M:%S.%f")
            date_fin = datetime.strptime(date_fin, "%Y-%m-%dT%H:%M:%S.%f")
            
            if date_debut > date_fin:
                raise HTTPException(status_code=400, detail="date_debut must be less than date_fin")
            
            val = await self.update_var_historique(id)
            
            retour = []
            for item in val:
                date = datetime.strptime(item.get("date"), "%Y-%m-%dT%H:%M:%S.%f")
                if date >= date_debut and date <= date_fin:
                    retour.append(item)
            return retour
        
        except ValueError:
            raise HTTPException(status_code=400, detail="date_debut and date_fin must have the format %Y-%m-%dT%H:%M:%S.%f")
        
        except FileNotFoundError:
            val =  await self.set_historique_var_crypto(id)
            retour = []
            for item in val:
                date = datetime.strptime(item.get("date"), "%Y-%m-%dT%H:%M:%S.%f")
                if date >= date_debut and date <= date_fin:
                    retour.append(item)
            return retour
    
    async def read_var_historique_for_one_crypto(self,id):
        try:
            with open('app/json/var/historique/'+id+'_var.json') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            return await self.set_historique_var_crypto(id)
    
    async def update_var_historique(self,id):
        liste_var = await self.read_var_historique_for_one_crypto(id)
        # get last date frrom var.json
        last_date = liste_var[-1].get("date")
        
        # chech if format of last date is %Y-%m-%dT00:00:00.000 avec hours and minute and second zero
        if last_date[-14:] != "T00:00:00.000":
            liste_var = await self.set_historique_var_crypto(id)
            return liste_var
        
        # get today date
        today = datetime.now().strftime("%Y-%m-%dT00:00:00.000")
        # calcul difference between last date and today
        date_format = "%Y-%m-%dT00:00:00.000"
        last_date = datetime.strptime(last_date, date_format)
        today = datetime.strptime(today, date_format)
        delta = today - last_date
        delta = delta.days
        if delta > 1:
            liste_prix = await coinGeckoService.get_historical_prices(id,"usd",90)
            liste_prix = liste_prix[:-2]
            for i in range(delta-1):
                var  = await self.calcul_var_with_price(liste_prix)
                data = {
                    "date": (last_date + timedelta(days=i+1)).strftime("%Y-%m-%dT00:00:00.000"),
                    "var": var
                }
                liste_var.append(data)
                liste_prix = liste_prix.iloc[:-1]
        

            with open('app/json/var/historique/'+id+'_var.json', 'w', encoding='utf-8') as f:
                json.dump(liste_var, f, indent=4, ensure_ascii=False)
        
        return liste_var
        