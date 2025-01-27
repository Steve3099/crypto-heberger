import requests
import pandas as pd
import numpy as np


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

# Fonction pour récupérer les données de capitalisation boursière
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

# Fonction pour normaliser les poids
def normalize_weights(btc_market_cap, eth_market_cap):
    total_market_cap = btc_market_cap + eth_market_cap
    btc_weight = btc_market_cap / total_market_cap
    eth_weight = eth_market_cap / total_market_cap
    return btc_weight, eth_weight

# Fonction pour calculer les statistiques : volatilité et covariance
def calculate_statistics(btc_prices, eth_prices, btc_weight, eth_weight):
    # Joindre les deux datasets sur les dates
    merged = pd.merge(btc_prices, eth_prices, on='date', suffixes=('_btc', '_eth'))
    
    # Calculer les rendements journaliers pour BTC et ETH
    merged['log_return_btc'] = np.log(merged['price_btc'] / merged['price_btc'].shift(1))
    merged['log_return_eth'] = np.log(merged['price_eth'] / merged['price_eth'].shift(1))
    
    # Supprimer les valeurs NaN
    merged.dropna(inplace=True)
    
    # Calcul de la volatilité historique
    vol_btc = merged['log_return_btc'].std()
    vol_eth = merged['log_return_eth'].std()
    
    # Calcul de la covariance entre BTC et ETH
    covariance = merged[['log_return_btc', 'log_return_eth']].cov().iloc[0, 1]
    
    # Méthode matricielle (plus précise)
    weights = np.array([btc_weight, eth_weight])
    covariance_matrix = np.array([
        [vol_btc**2, covariance],  # Variance de BTC, covariance
        [covariance, vol_eth**2]   # Covariance, variance de ETH
    ])
    
    portfolio_volatility_mat = np.sqrt(weights.T @ covariance_matrix @ weights)
    
    return vol_btc, vol_eth, covariance, portfolio_volatility_mat, covariance_matrix

# Calcul de la matrice de corrélation
def calculate_correlation_matrix(covariance_matrix):
    std_devs = np.sqrt(np.diag(covariance_matrix))
    correlation_matrix = covariance_matrix / np.outer(std_devs, std_devs)
    return correlation_matrix

# Récupérer les prix historiques pour BTC et ETH
btc_prices = get_historical_prices('bitcoin', days=90)
eth_prices = get_historical_prices('ethereum', days=90)

# Récupérer les capitalisations boursières
btc_market_cap = get_market_cap('bitcoin')
eth_market_cap = get_market_cap('ethereum')

# Normaliser les poids
btc_weight, eth_weight = normalize_weights(btc_market_cap, eth_market_cap)

# Afficher les poids normalisés
print(f"Poids du BTC: {btc_weight:.4f}")
print(f"Poids de l'ETH: {eth_weight:.4f}")

# Calculer les statistiques
vol_btc, vol_eth, covariance, portfolio_volatility_mat, covariance_matrix = calculate_statistics(
    btc_prices, eth_prices, btc_weight, eth_weight
)

# Calculer la matrice de corrélation
correlation_matrix = calculate_correlation_matrix(covariance_matrix)

# Annualiser les volatilités (BTC, ETH et portefeuille)
vol_btc_annual = vol_btc * np.sqrt(365)
vol_eth_annual = vol_eth * np.sqrt(365)
portfolio_volatility_mat_annual = portfolio_volatility_mat * np.sqrt(365)

# Afficher les résultats
print("=== Résultats ===")
print(f"Volatilité quotidienne de Bitcoin (BTC) : {vol_btc:.4f}")
print(f"Volatilité quotidienne d'Ethereum (ETH): {vol_eth:.4f}")
print(f"Covariance quotidienne entre BTC et ETH: {covariance:.6f}")
print(f"Volatilité quotidienne du portefeuille (matricielle) : {portfolio_volatility_mat:.4f}")

print("\n=== Résultats Annualisés ===")
print(f"Volatilité annuelle de Bitcoin (BTC) : {vol_btc_annual:.4f}")
print(f"Volatilité annuelle d'Ethereum (ETH): {vol_eth_annual:.4f}")
print(f"Volatilité annuelle du portefeuille (matricielle) : {portfolio_volatility_mat_annual:.4f}")

print("\n=== Matrice de Covariance ===")
print(covariance_matrix)

print("\n=== Matrice de Corrélation ===")
print(correlation_matrix)