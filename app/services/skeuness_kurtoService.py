import numpy as np
import json
import pandas as pd
from scipy.stats import skew, kurtosis

from app.services.coinGeckoService import CoinGeckoService

coinGeckoService = CoinGeckoService()

class Skewness_KurtoService:
    def __init__(self):
        pass
    
    async def calculate_skewness_kurtosis(self,prices_list, crypto_names):
        results = {}
        for i, prices in enumerate(prices_list):
            crypto_name = crypto_names[i].get("id")
            # Calculer les rendements journaliers logarithmiques
            prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
            # Supprimer les valeurs NaN
            prices.dropna(inplace=True)
            # Vérifier qu'il y a assez de données pour les calculs
            if len(prices['log_return']) > 1:  # Nécessite au moins 2 rendements
                # print(f"Calcul du skewness et du kurtosis pour {crypto_name}")
                # Calcul du skewness et du kurtosis
                skew_value = skew(prices['log_return'])
                kurt_value = kurtosis(prices['log_return'], fisher=True)  # Kurtosis normalisée (0 pour une normale)
                temp = {'skewness': skew_value, 'kurtosis': kurt_value}
                # set skewness and kurtosis itno json file
                with open('app/json/crypto/skewness_kurtosis/'+crypto_name+'_skewness_kurtosis.json', 'w') as f:
                    json.dump(temp, f, indent=4, ensure_ascii=False)
            else:
                pass
                # print(f"Pas assez de rendements pour {crypto_name}, skewness et kurtosis non calculés.")
    
    # verif if skewness and kurtosis are already calculated
    async def check_skewness_kurtosis(self, crypto_id):
        try:
            with open('app/json/crypto/skewness_kurtosis/'+crypto_id+'_skewness_kurtosis.json', 'r') as f:
                data = f.read()
                return json.loads(data)
        except FileNotFoundError:
            return None
    
    async def calculate_skewness_kurtosis_one_crypto(self, prices, crypto_name):
        prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
        # Supprimer les valeurs NaN
        prices.dropna(inplace=True)
        
        # Vérifier qu'il y a assez de données pour les calculs
        if len(prices['log_return']) > 1:  # Nécessite au moins 2 rendements
            # print(f"Calcul du skewness et du kurtosis pour {crypto_name}")
            # Calcul du skewness et du kurtosis
            skew_value = skew(prices['log_return'])
            kurt_value = kurtosis(prices['log_return'], fisher=True)  # Kurtosis normalisée (0 pour une normale)
            temp = {'skewness': skew_value, 'kurtosis': kurt_value}
            # set skewness and kurtosis itno json file
            with open('app/json/crypto/skewness_kurtosis/'+crypto_name+'_skewness_kurtosis.json', 'w') as f:
                json.dump(temp, f, indent=4, ensure_ascii=False)
            
            return temp
    
    async def set_skewness_kurto(self):
        
        # recuperer la liste de crypto
        liste_crypto = await coinGeckoService.get_liste_crypto_filtered()
        
        # recuperer la liste de prix de chaque crypto
        liste_prix = []
        liste_crypto_used = []
        for i in range(len(liste_crypto)):
            crypto = liste_crypto[i]
            
            # obtenir l'hitorique des prix des 10 crypto
            df = await coinGeckoService.get_historical_prices(crypto = crypto.get("id"), days =90)
            if len(df) > 90:
                liste_prix.append(df)
                liste_crypto_used.append(crypto)
        # return liste_prix
        await self.calculate_skewness_kurtosis(liste_prix, liste_crypto_used)
        return "skewness and kurtosis done"
    
    async def get_skewness_kurtosis(self, id):
        try:
            with open('app/json/crypto/skewness_kurtosis/'+id+'_skewness_kurtosis.json', 'r') as f:
                data = f.read()
                return json.loads(data)
        except FileNotFoundError:
            df = await coinGeckoService.get_historical_prices(crypto = id, days =90)
            
            return await self.calculate_skewness_kurtosis_one_crypto(df,id)
        