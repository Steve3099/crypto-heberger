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
def calculate_var(liste_price,liste_crypto,list_weight, percentile=1):
    # liste_crypto= []
    # liste_price = []
    # list_weight= []
    
    merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("name")})
    for i in range(1, len(liste_price)):
        liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("name")})
        merged = pd.merge(merged, liste_price[i], on='date')
        
    # put merge prix to csv
    merged.to_csv('Varlisteprix.csv', index=False)
    # Joindre les deux datasets sur les dates
    # merged = pd.merge(btc_prices, eth_prices, on='date', suffixes=('_btc', '_eth'))
    
    # Calculer les rendements journaliers pour BTC et ETH
    # merged['log_return_btc'] = np.log(merged['price_btc'] / merged['price_btc'].shift(1))
    # merged['log_return_eth'] = np.log(merged['price_eth'] / merged['price_eth'].shift(1))
    
    for i in range(len(liste_crypto)):
        merged['log_return_'+liste_crypto[i].get("name")] = np.log(merged['price_'+liste_crypto[i].get("name")] / merged['price_'+liste_crypto[i].get("name")].shift(1))
    
    
    # Supprimer les valeurs NaN
    merged.dropna(inplace=True)
    
    # Calcul des rendements journaliers du portefeuille
    val = 0
    for i in range(len(list_weight)):
       val += list_weight[i] * merged['log_return_' + liste_crypto[i].get("name")]
    
    merged['portfolio_return'] = val
    
    # Calcul de la VaR historique du portefeuille (percentile spécifié)
    var_percentile_portfolio = np.percentile(merged['portfolio_return'], percentile)
    
    # Calcul de la VaR historique pourtout les cypto
    liste_var_percentile_crypto = []
    for i in range(len(liste_crypto)):
        var_percentile_crypto = np.percentile(merged['log_return_' + liste_crypto[i].get("name")], percentile)
        liste_var_percentile_crypto.append(var_percentile_crypto)
    
    
    # var_percentile_btc = np.percentile(merged['log_return_btc'], percentile)
    # var_percentile_eth = np.percentile(merged['log_return_eth'], percentile)
    return liste_var_percentile_crypto , var_percentile_portfolio
    return var_percentile_btc, var_percentile_eth, var_percentile_portfolio

# recuperer la liste de crypto
list_crypto = get_liste_crypto()
# filtrer les crypto
list_crypto = excludeStableCoin(list_crypto)

list_crypto = list_crypto[:10]

# recuperer la liste de prix et la liste de market cap
liste_prix = []
liste_market_cap = []
somme_market_cap = 0
for i in range(len(list_crypto)):
    crypto = list_crypto[i]
    
    # obtenir l'hitorique des prix des 10 crypto
    df = get_historical_prices(crypto = crypto.get("id"), days =90)
    
    liste_prix.append(df)
    
    # obtenir le market cap de chaque crypto
    df = get_market_cap(crypto = crypto.get("id"))
    liste_market_cap.append(df)
    
    somme_market_cap += df

        


# Récupérer les prix historiques pour BTC et ETH
# btc_prices = get_historical_prices('bitcoin', days=90)
# eth_prices = get_historical_prices('ethereum', days=90)

# Récupérer les dominances de marché
# btc_market_cap = get_market_cap('bitcoin')
# eth_market_cap = get_market_cap('ethereum')
# total_market_cap = btc_market_cap + eth_market_cap

# obtenire la liste des poids
liste_weight = []
for market_cap in liste_market_cap:
    liste_weight.append(market_cap / somme_market_cap)

# btc_weight = btc_market_cap / total_market_cap
# eth_weight = eth_market_cap / total_market_cap

# Calculer les VaR historiques pour BTC, ETH et le portefeuille
liste_var, var_portfolio = calculate_var(liste_prix, list_crypto, liste_weight, percentile=1)

# Sauvegarder les résultats dans des fichiers CSV
# btc_prices.to_csv('btc_prices.csv', index=False)
# eth_prices.to_csv('eth_prices.csv', index=False)

# Afficher les résultats
print("=== Résultats ===")
# poids des cfypto
for i in range(len(liste_weight)):
    print(f"Weight for {list_crypto[i].get('name')} : {liste_weight[i]}")

# print(f"Poids du BTC dans le portefeuille : {btc_weight:.4f}")
# print(f"Poids de l'ETH dans le portefeuille : {eth_weight:.4f}")

for i in range(len(liste_var)):
    print(f"VaR historique de {list_crypto[i].get('name')} à 99% : {liste_var[i]:.4f}")

# print(f"VaR historique du BTC à 99% : {var_btc:.4f}")
# print(f"VaR historique de l'ETH à 99% : {var_eth:.4f}")
print(f"VaR historique du portefeuille à 99% : {var_portfolio:.4f}")