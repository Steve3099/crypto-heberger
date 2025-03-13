import requests
import pandas as pd
import numpy as np
import json
from scipy.stats import skew, kurtosis  # Importation des fonctions de scipy.stats

# Fonction pour récupérer les prix historiques d'une crypto
def get_liste_crypto(categorie_id="layer-1",page=1):
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "per_page": 250,
        "category": categorie_id,
        "page":page
        # "order": "volume_desc"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }

    response = requests.get(url, headers=headers,params=params)
    df = json.loads(response.text)
    
    retour = []
    for i in range(len(df)):
        retour.append(df[i])
    
    return retour
def get_liste_symbole_by_id_categorie(id_Categorie):
    
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
    params = {
        "id": id_Categorie
    }
    headers = {
        "accept": "application/json",
        "X-CMC_PRO_API_KEY": "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"
    }
    response = requests.get(url, headers=headers, params=params)
    data = json.loads(response.text)
    data  = data.get("data")
    liste_coin = data["coins"]
    
    liste_stablecoins = []
    for item in liste_coin:
        # put symbol to lower case  
        liste_stablecoins.append(item.get("symbol").lower())
    
    # put the liste symbole into csv
    with open("stablecoins.csv","w") as f:
        for symbol in liste_stablecoins:
            f.write(symbol + "\n")
    
    return liste_stablecoins

def excludeStableCoin(listeCoin):
    id_Stable_Coin = "604f2753ebccdd50cd175fc1"
    id_Wrapped_Token = "6053df7b6be1bf5c15e865ed"
    stablecoins = get_liste_symbole_by_id_categorie(id_Stable_Coin)
    wrapped_tokens = get_liste_symbole_by_id_categorie(id_Wrapped_Token)
    
    filtered = [coin for coin in listeCoin if 
                coin["symbol"].lower() not in stablecoins and 
                coin["symbol"].lower() not in wrapped_tokens and 
                coin["current_price"] is not None and
                (coin["total_volume"]  is None or coin["total_volume"] >= 2000000)]
    
    return filtered

# Fonction pour récupérer les prix historiques de BTC ou ETH
def get_historical_prices(crypto, vs_currency='usd', days=90):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-pq44GDj1HKecURw2UA1uUYz8"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].round(6)
    return df[['date', 'price']]

# Fonction pour calculer le skewness et le kurtosis pour chaque crypto individuellement
def calculate_skewness_kurtosis(prices_list, crypto_names):
    results = {}
    
    for i, prices in enumerate(prices_list):
        crypto_name = crypto_names[i].get("id")
        # Calculer les rendements journaliers logarithmiques
        prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
        # Supprimer les valeurs NaN
        prices.dropna(inplace=True)
        # Vérifier qu'il y a assez de données pour les calculs
        if len(prices['log_return']) > 1:  # Nécessite au moins 2 rendements
            # Calcul du skewness et du kurtosis
            skew_value = skew(prices['log_return'])
            kurt_value = kurtosis(prices['log_return'], fisher=True)  # Kurtosis normalisée (0 pour une normale)
            results[crypto_name] = {'skewness': skew_value, 'kurtosis': kurt_value}
        else:
            print(f"Pas assez de rendements pour {crypto_name}, skewness et kurtosis non calculés.")
    
    return results

# recuperer la liste de crypto
list_crypto = get_liste_crypto()
# filtrer les crypto
list_crypto = excludeStableCoin(list_crypto)

list_crypto = list_crypto[:10]

# Récupérer les prix historiques pour BTC et ETH
# btc_prices = get_historical_prices('bitcoin', days=90)
# eth_prices = get_historical_prices('ethereum', days=90)

prices_list = []
for i in range(len(list_crypto)):
    crypto = list_crypto[i]
    
    # obtenir l'hitorique des prix des 10 crypto
    df = get_historical_prices(crypto = crypto.get("id"), days =90)
    
    prices_list.append(df)
    
print(prices_list[0])
# Liste des prix et noms des cryptos
# prices_list = [btc_prices, eth_prices]
# crypto_names = ['bitcoin', 'ethereum']

# Calculer le skewness et le kurtosis pour chaque crypto
# results = calculate_skewness_kurtosis(prices_list, list_crypto)

# # Afficher les résultats
# print("=== Résultats ===")
# for crypto, metrics in results.items():
#     print(f"{crypto.capitalize()} :")
#     print(f"  Skewness : {metrics['skewness']:.4f}")
#     print(f"  Kurtosis : {metrics['kurtosis']:.4f}")