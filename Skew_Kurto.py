import requests
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis  # Importation des fonctions de scipy.stats

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

# Fonction pour calculer le skewness et le kurtosis pour chaque crypto individuellement
def calculate_skewness_kurtosis(prices_list, crypto_names):
    results = {}
    
    for i, prices in enumerate(prices_list):
        crypto_name = crypto_names[i]
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

# Récupérer les prix historiques pour BTC et ETH
btc_prices = get_historical_prices('bitcoin', days=90)
eth_prices = get_historical_prices('ethereum', days=90)

# Liste des prix et noms des cryptos
prices_list = [btc_prices, eth_prices]
crypto_names = ['bitcoin', 'ethereum']

# Calculer le skewness et le kurtosis pour chaque crypto
results = calculate_skewness_kurtosis(prices_list, crypto_names)

# Afficher les résultats
print("=== Résultats ===")
for crypto, metrics in results.items():
    print(f"{crypto.capitalize()} :")
    print(f"  Skewness : {metrics['skewness']:.4f}")
    print(f"  Kurtosis : {metrics['kurtosis']:.4f}")