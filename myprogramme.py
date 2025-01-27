import requests
import pandas as pd
import numpy as np
import json
from decimal import Decimal, getcontext

getcontext().prec = 28

def get_liste_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
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

def excludeStableCoin(listeCoin):
        # List of known stablecoin symbols to exclude
    stablecoin_symbols = {"usdt", "usdc", "busd", "dai", "tusd", "ust", "gusd", "pax", "eurs", "frax", "husd"}
    
    listeRetour = []
    for el in listeCoin:
        # Exclude known stablecoins by symbol
        if el.get("symbol", "").lower() in stablecoin_symbols:
            continue
        
        # Exclude assets with minimal price change (e.g., ±0.01% in 24h)
        price_change_percentage_24h = el.get("price_change_percentage_24h", 0)
        if abs(price_change_percentage_24h) < 0.01:
            continue
        # Add non-stablecoins to the result list
        listeRetour.append(el)
    
    return listeRetour

def get_historical_prices(crypto, vs_currency='usd', days=90):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].round(2)
    return df[['date', 'price']]

def get_market_cap(crypto):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    market_cap = data['market_data']['market_cap']['usd']
    return market_cap

def normalize_weights(liste_crypto_market_cap):
    total_market_cap = 0
    
    for i in range(len(liste_crypto_market_cap)):
        total_market_cap += liste_crypto_market_cap[i]
    
    liste_crypto_weight = []
    for i in range(len(liste_crypto_market_cap)):
        weight = liste_crypto_market_cap[i] / total_market_cap
        liste_crypto_weight.append(weight)
    return liste_crypto_weight

def round_weights(liste_weight):
    somme_weight = 0.0
    for i in range(len(liste_weight)):
        liste_weight[i] = round(liste_weight[i], 4)
        somme_weight += liste_weight[i]
    if somme_weight != 1.0:
        error = Decimal('1.0') - Decimal(str(somme_weight))
        min_weight = min(liste_weight)
        index_min = liste_weight.index(min_weight)
        print(min_weight)
        print(error)
        if error > 0:
            # enlever l'erreur au poids le plus faible
            liste_weight[index_min] = float(Decimal(str(liste_weight[index_min])) + Decimal(str(error)))
        else:
            # ajouter l'erreur au poids le plus fort
            liste_weight[index_min] = float(Decimal(str(liste_weight[index_min])) - Decimal(str(error)))
    return liste_weight

def calculate_statistics(liste_price,liste_crypto,liste_weight):
    # Joindre les datasets des liste  sur les dates and add suffixe (liste_crypto[i].get("name"))
    
    merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("name")})
    for i in range(1, len(liste_price)):
        liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("name")})
        merged = pd.merge(merged, liste_price[i], on='date')
        
    
    # Calculer les rendements journaliers pour les crypto de la liste
    
    for i in range(len(liste_crypto)):
        merged['log_return_'+liste_crypto[i].get("name")] = np.log(merged['price_'+liste_crypto[i].get("name")] / merged['price_'+liste_crypto[i].get("name")].shift(1))
    
    # Supprimer les valeurs NaN
    merged.dropna(inplace=True)
    
    # Calcul de la volatilité historique
    liste_volatilite = []
    for i in range(len(liste_crypto)):
        vol = merged['log_return_'+liste_crypto[i].get("name")].std()
        liste_volatilite.append(vol)
    
    # Calcul de la covariance entre les cryptos de la liste
    covariance_matrix = merged[[f'log_return_{crypto.get("name")}' for crypto in liste_crypto]].cov()
    
    # Méthode matricielle (plus précise)
    weights = np.array(liste_weight)
    portfolio_volatility_mat = np.sqrt(weights.T @ covariance_matrix.values @ weights)
    
    return liste_volatilite, portfolio_volatility_mat,covariance_matrix
    
def calculate_correlation_matrix(covariance_matrix):
    std_devs = np.sqrt(np.diag(covariance_matrix))
    correlation_matrix = covariance_matrix / np.outer(std_devs, std_devs)
    return correlation_matrix

list_crypto = get_liste_crypto()
list_crypto = excludeStableCoin(list_crypto)
# prendre que les 10 premier crypto pour le calcul
list_crypto = list_crypto[:10]


liste_prix = []
liste_market_cap = []
for i in range(len(list_crypto)):
    crypto = list_crypto[i]
    
    # obtenir l'hitorique des prix des 10 crypto
    df = get_historical_prices(crypto = crypto.get("id"), days =90)
    liste_prix.append(df)
    
    # obtenir le market cap de chaque crypto
    df = get_market_cap(crypto = crypto.get("id"))
    liste_market_cap.append(df)

# Normaliser les poids
liste_weight = normalize_weights(liste_market_cap)
liste_weight = round_weights(liste_weight)
# Afficher les poids normalisés
for i in range(len(liste_weight)):
    print(f"Weight for {list_crypto[i].get('name')} : {liste_weight[i]}")
    
liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculate_statistics(liste_prix,list_crypto,liste_weight)

# Calculer la matrice de corrélation
correlation_matrix = calculate_correlation_matrix(covariance_matrix)

# Annualiser les volatilités (BTC, ETH et portefeuille)
liste_volatilite_annuel = []

for i in range(len(liste_volatilite)):
    vol = liste_volatilite[i] * np.sqrt(365)
    liste_volatilite_annuel.append(vol)

portfolio_volatility_mat_annual = portfolio_volatility_mat * np.sqrt(365)

# Afficher les résultats

for i in range(len(liste_volatilite)):
    print(f"Volatilité quotidienne de {list_crypto[i].get('name')} : {liste_volatilite[i]:.4f}")
    print(f"Volatilité annuelle de {list_crypto[i].get('name')} : {liste_volatilite_annuel[i]:.4f}")
    
print(f"Volatilité quotidienne du portefeuille (matricielle) : {portfolio_volatility_mat:.4f}")

print(f"Volatilité annuelle du portefeuille (matricielle) : {portfolio_volatility_mat_annual:.4f}")

print("\n=== Matrice de Covariance ===")
print(covariance_matrix)

print("\n=== Matrice de Corrélation ===")
print(correlation_matrix)

    