import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json

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

# Fonction pour récupérer les données de dominance de marché
def get_market_cap(crypto):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-pq44GDj1HKecURw2UA1uUYz8"
    }
    response = requests.get(url, headers=headers, params={})
    data = response.json()
    market_cap = data['market_data']['market_cap']['usd']
    return market_cap

# Fonction pour calculer les VaR historiques
def calculate_var(prices_list, crypto_names, percentile=1):
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
# recuperer la liste de crypto
list_crypto = get_liste_crypto()
# filtrer les crypto
list_crypto = excludeStableCoin(list_crypto)

list_crypto = list_crypto[:10]

# recuperer la liste de prix et la liste de market cap
liste_prix = []
liste=[]
for i in range(len(list_crypto)):
    crypto = list_crypto[i]
    
    # obtenir l'hitorique des prix des 10 crypto
    df = get_historical_prices(crypto = crypto.get("id"), days =90)
    
    liste_prix.append(df)
    liste.append(df.copy())
merged = liste[0].rename(columns={'price': 'price_' + list_crypto[0].get("name")})
for i in range(1, len(liste)):
    liste[i] = liste[i].rename(columns={'price': 'price_' + list_crypto[i].get("name")})
    merged = pd.merge(merged, liste[i], on='date')

# # put merge  into csv
merged.to_csv('listeprix.csv', index=False)
# Calculer les VaR historiques pour BTC, ETH et le portefeuille
liste_var = calculate_var(liste_prix, list_crypto, percentile=1)

# Sauvegarder les résultats dans des fichiers CSV
# btc_prices.to_csv('btc_prices.csv', index=False)
# eth_prices.to_csv('eth_prices.csv', index=False)

# Afficher les résultats


# for i in range(len(liste_var)):
#     print(f"VaR historique de {list_crypto[i].get('name')} à 99% : {liste_var[i]:.4f}")

# print(f"VaR historique du portefeuille à 99% : {var_portfolio:.4f}")

# pyt liste var into json
with open("liste_var.json","w") as f:
    json.dump(liste_var,f,indent=4)