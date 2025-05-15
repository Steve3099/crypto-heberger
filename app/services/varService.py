from app.services.coinGeckoService import CoinGeckoService
import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
coinGeckoService = CoinGeckoService()


class VarService:
    def __init__(self):
        pass
    
    async def calculate_var(self,liste_price,liste_crypto,list_weight, percentile=1):
        # liste_crypto= []
        # liste_price = []
        # list_weight= []
        merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("id")})
        # return liste_price,0
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
            raise ValueError("Crypto not found")
    
    async def calculate_var_v2(self,prices_list, crypto_names, percentile=1):
        var_results = {}
    
        for i, prices in enumerate(prices_list):
            crypto_name = crypto_names[i].get("id")
            
            # Calculer les rendements journaliers logarithmiques
            prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
            # Supprimer les valeurs NaN
            prices.dropna(inplace=True)
            # Calcul de la VaR historique (sans interpolation)
            var_percentile = np.percentile(prices['log_return'], percentile,method='lower')
            var_results[crypto_name] = var_percentile
        
        return var_results
    
    async def calcul_var_one_crypto(self, liste_prix,percentile=1):
        # crypto_name = crypto_names[i].get("id")
        
        # Calculer les rendements journaliers logarithmiques
        liste_prix['log_return'] = np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        # Supprimer les valeurs NaN
        liste_prix.dropna(inplace=True)
        # Calcul de la VaR historique (sans interpolation)
        var_percentile = np.percentile(liste_prix['log_return'], percentile,method='lower')
        return var_percentile
    
    # async def calulate_var_one_crypto(self, id, percentile=1):
    #     prices = await coinGeckoService.get_historical_prices(id, "usd", 90)
    #     var_results = {}
    #     crypto_name = id
    #     # Calculer les rendements journaliers logarithmiques
    #     prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
    #     # Supprimer les valeurs NaN
    #     prices.dropna(inplace=True)
    #     # Calcul de la VaR historique (sans interpolation)
    #     var_percentile = np.percentile(prices['log_return'], percentile, method='lower')
    #     var_results[crypto_name] = var_percentile
        
    #     # put it into json file
    #     today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    #     file_path = f"app/json/var/historique/{id}_var.json"
    #     data = {
    #         "date": today,
    #         "var": var_percentile
    #     }
    #     data_list = []
    #     if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
    #         data_list = [data]  # Create a new list with the first entry
    #     else:
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             try:
    #                 data_list = json.load(f)
    #                 if not isinstance(data_list, list):  # Ensure it's a list
    #                     data_list = [data_list]
    #             except json.JSONDecodeError:
    #                 data_list = []  # Handle corrupt or empty files
    #         data_list.append(data)  # Append the new entry

    #     # Write updated data back to file
    #     with open(file_path, 'w', encoding='utf-8') as f:
    #         json.dump(data_list, f, indent=4, ensure_ascii=False)
        
    #     return var_results
    
    async def update_var_v2(self):
        # get liste crypto
        liste_crypto = await coinGeckoService.get_liste_crypto_filtered()
        # return liste_crypto
        # get liste price
        liste_price = []
        for el in liste_crypto:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),"usd",90)
            # if len(historique) > 90:
            liste_price.append(historique)
        # calculate var
        liste_var = await self.calculate_var_v2(liste_price, liste_crypto, 1)
        # return liste_var
        # save var to json
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for item in liste_crypto:
            print(item.get('id'))
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
        
        