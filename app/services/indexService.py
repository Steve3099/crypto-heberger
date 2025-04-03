import time
import pandas as pd
from app.services.coinGeckoService import CoinGeckoService
import json
import os
coingeckoservice = CoinGeckoService()

class IndexService:
    def calculate_index(self,crypto_list, base_market_cap):
        market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in crypto_list)
        index_value = (market_cap / base_market_cap) * 100  # Utilisation du market cap initial comme diviseur
        return round(index_value, 4), market_cap
    
    async def set_Index(self):
        print("Démarrage de l'indice crypto...")
        base_market_cap = None 
        # get base_market_cap from json file
        with open('app/json/index/base_market_cap.json', 'r') as f:
            value = f.read()
            # return value
            if value != '':
                base_market_cap = float(value)
        
         # Initialisation du diviseur de base
        
        # while True:
        try:
            data = await coingeckoservice.get_liste_crypto_filtered()
            #filtered those with marketcap < 2000000
            filtered_data = [coin for coin in data if
                            coin["current_price"] is not None and
                            (coin["total_volume"]  is None or coin["total_volume"] >= 2000000)]
            filtered_data = filtered_data[:80]
            
            # write date into json file
            with open('app/json/liste_crypto/liste_crypto.json', 'w') as f:
                json.dump(filtered_data, f, indent=4)
            
            # filtered_data = filter_data(data)
            
            if base_market_cap is None:
                base_market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in filtered_data)
                # set base_market_cap in json file
                with open('app/json/index/base_market_cap.json', 'w') as f:
                    f.write(f"{base_market_cap:.4f}")
            
            index_value, total_market_cap = self.calculate_index(filtered_data, base_market_cap)
            print(f"Indice mis à jour: {index_value:.4f}\n")
            
            # conserve index value into json file - add it to the bottom of the liste
            file_path = 'app/json/index/index.json'

            # Read existing data
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)  # Load existing list
                    except json.JSONDecodeError:
                        data = []  # If the file is empty or invalid, start fresh
            else:
                data = []

            # Append new value
            val = {"date": time.strftime('%Y-%m-%d %H:%M:%S'), "value": index_value}
            data.append(val)

            # Write back as a valid JSON list
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4) 
                            
            
            df = pd.DataFrame([{
                "Nom": coin["name"],
                "Prix (USD)": f"{coin['current_price']:.2f}",
                "Circulating Supply": f"{coin['circulating_supply']:,}",
                "Volume (USD)": f"{coin['total_volume']:.2f}",
                "Poids (%)": f"{(coin['current_price'] * coin['circulating_supply'] / total_market_cap * 100):.2f}"
            } for coin in filtered_data])
            
            # print(df.to_string(index=False))
            # put df in a csv file
            df.to_csv('app/index/index.csv', index=False)
            
        except Exception as e:
            print("Erreur lors de la mise à jour de l'indice:", e)
            # time.sleep(1200) 
            
    async def get_csv_index(self):
        df = pd.read_csv('app/index/index.csv')
        return df
    
    async def get_graphe_indices(self):
        liste_indice = await self.get_csv_index()
        # return liste_indice
        graphe = []
        # other = {"Nom": "Autres", "Poids": 0}
        value_other = 0
        for i in range(len(liste_indice["Nom"])):
            if liste_indice["Poids (%)"][i] >= 0.1:
                temp = {"Nom": liste_indice["Nom"][i], "Poids (%)": liste_indice["Poids (%)"][i]}
                graphe.append(temp)
            else:
                value_other += liste_indice["Poids (%)"][i]
        graphe.append({"Nom": "Autres", "Poids (%)": value_other})
        
        return graphe
    
    async def get_liste_index_from_json_file(self,date_start = None,date_end = None):
        liste = []
        if date_start is None:
            date_start = "2025-02-18 09:19:33"
        
        if date_end is None:
            date_end = time.strftime('%Y-%m-%d %H:%M:%S')
        with open('app/json/index/index.json', 'r') as f:
            data = json.load(f)
            for el in data:
                if el["date"] >= date_start and el["date"] <= date_end:
                    liste.append(el)
        return liste
        