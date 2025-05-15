import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Fonction pour récupérer les prix historiques d'une crypto
def get_historical_prices(crypto, vs_currency='usd', days=90):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].round(2)
    return df[['date', 'price']]

# Fonction pour calculer les VaR historiques pour chaque crypto individuellement
def calculate_var(prices_list, crypto_names, percentile=1):
    var_results = {}
    
    for i, prices in enumerate(prices_list):
        crypto_name = crypto_names[i]
        # Calculer les rendements journaliers logarithmiques
        prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
        # Supprimer les valeurs NaN
        prices.dropna(inplace=True)
        # Calcul de la VaR historique (sans interpolation)
        var_percentile = np.percentile(prices['log_return'], percentile,method='lower')
        var_results[crypto_name] = var_percentile
    
    return var_results

# Récupérer les prix historiques pour BTC et ETH
btc_prices = get_historical_prices('bitcoin', days=90)
eth_prices = get_historical_prices('ethereum', days=90)

# Liste des prix et noms des cryptos
prices_list = [btc_prices, eth_prices]
crypto_names = ['bitcoin', 'ethereum']

# Calculer les VaR historiques pour chaque crypto
var_results = calculate_var(prices_list, crypto_names, percentile=1)

# Afficher les résultats
print("=== Résultats ===")
for crypto, var_value in var_results.items():
    print(f"VaR historique de {crypto.capitalize()} à 99% : {var_value:.4f}")