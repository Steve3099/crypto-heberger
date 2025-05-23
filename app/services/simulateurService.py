from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.services.coinGeckoService import CoinGeckoService
from fastapi import HTTPException
from app.services.voaltiliteService import VolatiliteService
from app.services.cryptoService import CryptoService
from app.services.varService import VarService

coinGeckoService = CoinGeckoService()
volatiliteService = VolatiliteService()
cryptoService = CryptoService()
varService = VarService()

class SimulateurService:
    def __init__(self):
        pass

    async def simulateur_volatilite(self, id, valeur=[]):
        """Simulate volatility by appending new prices and recalculating."""
        historique_volatilite = await volatiliteService.get_historique_volatilite_crypto_from_json(id)
        historique_prix = await cryptoService.get_liste_prix_from_json(id)

        if not historique_prix:
            raise HTTPException(status_code=404, detail=f"No price data for crypto {id}")

        # Convert to DataFrame if not already
        historique_prix = pd.DataFrame(historique_prix, columns=['date', 'price'])
        
        now = datetime.now().date()
        for i, val in enumerate(valeur):
            if val < 0:
                raise HTTPException(status_code=400, detail="Values must be positive")
            
            # Append new price
            historique_prix.loc[len(historique_prix)] = [now, val]
            
            # Calculate volatility
            volatilite = await volatiliteService.calcul_Volatillite_Journaliere_one_crypto(historique_prix)
            historique_volatilite.append({
                "date": now,
                "valeur": volatilite
            })
            
            # Increment date
            now += timedelta(days=1)

        return historique_volatilite

    async def simulate_crypto_price(self, S0, mu, sigma, T, n_simulations=20, n=90):
        """Simulate crypto price trajectories using geometric Brownian motion."""
        np.random.seed(42)  # For reproducibility
        
        dt = T / n  # Time increment
        time_steps = n  # Number of time steps
        price_paths = np.zeros((time_steps, n_simulations))
        price_paths[0, :] = S0

        for i in range(n_simulations):
            W = np.random.normal(0, np.sqrt(dt), time_steps)  # Brownian noise
            W = np.cumsum(W)  # Wiener process
            t = np.linspace(0, T, time_steps)

            price_paths[1:, i] = S0 * np.exp((mu - 0.5 * sigma**2) * t[1:] + sigma * W[1:])
        
        return price_paths

    async def calcul_Volatillite_Journaliere_one_crypto(self, listePrix):
        """Calculate daily volatility and mean returns for a price list."""
        # Ensure DataFrame format
        listePrix = pd.DataFrame(listePrix, columns=['date', 'price'])
        
        # Calculate log returns
        listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))
        
        # Calculate mean returns
        mean_rendements = listePrix['log_return'].mean()
        
        # Drop NaN values
        listePrix.dropna(inplace=True)
        
        # Calculate historical volatility
        volatilite = listePrix['log_return'].std()
        
        return volatilite, mean_rendements

    async def run_similation_cupro_price(self, crypto_id, periode=90, n_simulations=20):
        """Run price simulation for a crypto based on historical data."""
        try:
            liste_prix = await coinGeckoService.get_historical_prices(crypto_id, days=periode)
            if liste_prix.empty:
                raise HTTPException(status_code=404, detail=f"No price data for crypto {crypto_id}")

            volatilite, mean_rendement = await self.calcul_Volatillite_Journaliere_one_crypto(liste_prix[:-2])

            prix_initial = liste_prix['price'].iloc[-1]

            S0 = prix_initial
            mu = mean_rendement
            sigma = volatilite
            T = periode
            time_steps = periode

            simulated_paths = await self.simulate_crypto_price(S0, mu, sigma, T, n_simulations, n=time_steps)
            
            # Compute mean prices at each time step
            mean_prices = np.mean(simulated_paths, axis=1).tolist()

            # Transpose simulated paths for JSON output
            simulated_paths_list = np.transpose(simulated_paths).tolist()

            return {
                "simulated_paths": simulated_paths_list,
                "mean_prices": mean_prices
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
    
    async def simulate_var(self, crypto_id,quantite=10000):
        # get crypto prices
        # liste_prix = await coinGeckoService.get_historical_prices(crypto_id, days=90)
        liste_prix = await cryptoService.get_liste_prix_from_json(crypto_id)
        if not liste_prix:
            raise HTTPException(status_code=404, detail=f"No price data for crypto {crypto_id}")
        
        liste_prix = pd.DataFrame(liste_prix, columns=['date', 'price'])
        
        # btc_prices = get_historical_prices(days=90)
        var_hist, var_coin_returns = await varService.calculate_var_historical(liste_prix)
        var_mc, simulated_returns = await varService.calculate_var_monte_carlo(var_coin_returns)
        
        # print("=== Résultats BTC ===")
        # print(f"VaR historique (99%) : {var_hist:.4f}")
        # print(f"VaR Monte Carlo (99%) : {var_mc:.4f}")
        # return 0
        # # Graphique Monte Carlo
        # plt.figure(figsize=(10, 5))
        # plt.hist(simulated_returns, bins=100, color='skyblue', edgecolor='black')
        # plt.axvline(var_mc, color='red', linestyle='dashed', linewidth=2, label=f'VaR Monte Carlo 99% = {var_mc:.4f}')
        # plt.title('Simulation Monte Carlo des rendements BTC (1 jour)')
        # plt.xlabel('Rendements simulés')
        # plt.ylabel('Fréquence')
        # plt.legend()
        # plt.grid(True)
        # plt.show()
        
        

        return {
            "historical_var": float(var_hist),
            "monte_carlo_var": float(var_mc),
            "simulated_returns": simulated_returns.tolist() if isinstance(simulated_returns, np.ndarray) else simulated_returns,
            "title": 'Simulation Monte Carlo des rendements (1 jour)',
            "x_label": 'Rendements simulés',
            "y_label": 'Fréquence'
        }
    
    async def simulation_potential_loss(self, crypto_id, quantite=100):
        
        # get crypto prices
        liste_prix = await coinGeckoService.get_historical_prices(crypto_id, days=90)
        if liste_prix.empty:
            raise HTTPException(status_code=404, detail=f"No price data for crypto {crypto_id}")
        
        price = liste_prix['price'].iloc[-1]
        
        notional = quantite * price
        # return liste_prix
        # make quentit into integer
        quantite = int(quantite)
        
        # btc_prices = get_historical_prices(days=90)
        var_hist, var_coin_returns = await varService.calculate_var_historical(liste_prix)
        
        var_mc, simulated_returns = await varService.calculate_var_monte_carlo(var_coin_returns)
        
        # print("=== Résultats BTC ===")
        # print(f"VaR historique (99%) : {var_hist:.4f}")
        # print(f"VaR Monte Carlo (99%) : {var_mc:.4f}")
        
        var99_historique = var_hist
        var99_monte_carlo = var_mc
        perte_potentielle_historique = notional * var99_historique 
        
        perte_potentielle_monte_carlo = notional * var99_monte_carlo
        
        perte_portefeuil_coin_historique = perte_potentielle_historique/price
        
        perte_portefeuil_coin_monte_carlo = perte_potentielle_monte_carlo/price
        
        return {
            "var_historique": {
                "price": price,
                "quantite": quantite,
                "notional": notional,
                "var99": var99_historique,
                "potentiel_loss (us $)": perte_potentielle_historique,
                "potentiel_loss (coin)": perte_portefeuil_coin_historique
            },
            "var_monte_carlo": {
                "price": price,
                "quantite": quantite,
                "notional": notional,
                "var99": var99_monte_carlo,
                "potentiel_loss (us $)": perte_potentielle_monte_carlo,
                "potentiel_loss (coin)": perte_portefeuil_coin_monte_carlo
            }
        }
        
        # return 0
        # # Graphique Monte Carlo
        # plt.figure(figsize=(10, 5))
        # plt.hist(simulated_returns, bins=100, color='skyblue', edgecolor='black')
        # plt.axvline(var_mc, color='red', linestyle='dashed', linewidth=2, label=f'VaR Monte Carlo 99% = {var_mc:.4f}')
        # plt.title('Simulation Monte Carlo des rendements BTC (1 jour)')
        # plt.xlabel('Rendements simulés')
        # plt.ylabel('Fréquence')
        # plt.legend()
        # plt.grid(True)
        # plt.show()
        
        

        # return {
        #     "historical_var": float(var_hist),
        #     "monte_carlo_var": float(var_mc),
        #     "simulated_returns": simulated_returns.tolist() if isinstance(simulated_returns, np.ndarray) else simulated_returns,
        #     "title": 'Simulation Monte Carlo des rendements (1 jour)',
        #     "x_label": 'Rendements simulés',
        #     "y_label": 'Fréquence'
        # }
                