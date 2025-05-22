import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
import requests

def simulate_crypto_price(S0, mu, sigma, T, n_simulations=20, n=90):
    """
    Simule des trajectoires de prix pour une crypto-monnaie suivant un mouvement brownien géométrique.
    
    S0: Prix initial
    mu: Drift (rendement espéré par jour)
    sigma: Volatilité journalière
    T: Horizon de temps en jours
    n_simulations: Nombre de simulations
    n: Nombre de pas (par défaut 90 jours)
    """
    
    np.random.seed(42)  # Pour la reproductibilité
    
    dt = T / n  # Incrément de temps
    time_steps = n  # Nombre de pas de temps
    price_paths = np.zeros((time_steps, n_simulations))  # Stocke les trajectoires
    price_paths[0, :] = S0

    for i in range(n_simulations):
        W = np.random.normal(0, np.sqrt(dt), time_steps)  # Bruit Brownien
        W = np.cumsum(W)  # Processus de Wiener
        t = np.linspace(0, T, time_steps)

        price_paths[1:, i] = S0 * np.exp((mu - 0.5 * sigma**2) * t[1:] + sigma * W[1:])
    
    return price_paths

def calcul_Volatillite_Journaliere_one_crypto(listePrix):
        
    # mettre liste prix dans un dataFrame
    listePrix = pd.DataFrame(listePrix,columns=['date','price'])
    
    # cacul rendement et la somme des rendement
    listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))
    
    # calculer la moyenne des rendements
    mean_rendements = listePrix['log_return'].mean()
    
    # Supprimer les valeurs NaN
    listePrix.dropna(inplace=True)
    
    # Calcul de la volatilité historique
    volatilite  = listePrix['log_return'].std()
    
    return volatilite,mean_rendements        


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

crypto_id = 'bitcoin'

liste_prix = get_historical_prices(crypto_id)

volatilite,mean_rendement = calcul_Volatillite_Journaliere_one_crypto(liste_prix[:-2])

prix_inital = liste_prix['price'].iloc[-1]


# ---- Paramètres ----
S0 = prix_inital      # Prix initial en $
mu = mean_rendement     # Rendement moyen quotidien
sigma = volatilite   # Volatilité historique quotidienne
T = 90          # Nombre de jours à simuler
n_simulations = 20  # Nombre de trajectoires

# ---- Simulation ----
simulated_paths = simulate_crypto_price(S0, mu, sigma, T, n_simulations)

# ---- Intervalle de confiance à 95% ----
mean_prices = np.mean(simulated_paths, axis=1)
#lower_bound = np.percentile(simulated_paths, 2.5, axis=1)
#upper_bound = np.percentile(simulated_paths, 97.5, axis=1)

# ---- Affichage ----
plt.figure(figsize=(10, 5))
plt.plot(simulated_paths, alpha=0.6, color='blue')
plt.plot(mean_prices, color='red', linewidth=2, label='Moyenne simulée')
#plt.fill_between(range(T), lower_bound, upper_bound, color='gray', alpha=0.3, label="IC 95%")

plt.title(f"Simulation du prix d'une crypto sur {T} jours")
plt.xlabel("Jours")
plt.ylabel("Prix estimé")
plt.legend()
plt.grid()
plt.show()
