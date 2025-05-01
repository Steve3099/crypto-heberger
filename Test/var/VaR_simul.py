import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Fonction pour récupérer les prix historiques du BTC
def get_historical_prices(crypto='bitcoin', vs_currency='usd', days=90):
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

# Fonction pour calculer la VaR historique avec method='lower'
def calculate_var_historical(btc_prices, percentile=1):
    btc_prices['log_return'] = np.log(btc_prices['price'] / btc_prices['price'].shift(1))
    btc_returns = btc_prices['log_return'].dropna()
    var_historical = np.percentile(btc_returns, percentile, method='lower')
    return var_historical, btc_returns

# Fonction pour calculer la VaR Monte Carlo
def calculate_var_monte_carlo(btc_returns, simulations=100000, percentile=1):
    mu = btc_returns.mean()  # Moyenne des rendements
    sigma = btc_returns.std()  # Écart-type des rendements

    # Affichage de mu et sigma
    print(f"--- Résultats statistiques ---")
    print(f"Moyenne (mu) des rendements : {mu:.6f}")
    print(f"Écart-type (sigma) des rendements : {sigma:.6f}")
    
    simulated_returns = np.random.normal(mu, sigma, simulations)
    var_mc = np.percentile(simulated_returns, percentile, method='lower')
    return var_mc, simulated_returns

# Exécution principale
btc_prices = get_historical_prices(days=90)
var_hist, btc_returns = calculate_var_historical(btc_prices)
var_mc, simulated_returns = calculate_var_monte_carlo(btc_returns)

# Affichage des résultats
print("=== Résultats BTC ===")
print(f"VaR historique (99%) : {var_hist:.4f}")
print(f"VaR Monte Carlo (99%) : {var_mc:.4f}")

# Graphique Monte Carlo
plt.figure(figsize=(10, 5))
plt.hist(simulated_returns, bins=100, color='skyblue', edgecolor='black')
plt.axvline(var_mc, color='red', linestyle='dashed', linewidth=2, label=f'VaR Monte Carlo 99% = {var_mc:.4f}')
plt.title('Simulation Monte Carlo des rendements BTC (1 jour)')
plt.xlabel('Rendements simulés')
plt.ylabel('Fréquence')
plt.legend()
plt.grid(True)
plt.show()
