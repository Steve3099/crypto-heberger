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

    async def simulateur_var(self, id, valeur):
        """Simulate VaR by appending a new price and calculating."""
        if valeur < 0:
            raise HTTPException(status_code=400, detail="Value must be positive")

        # Fetch price data
        liste_prix = await cryptoService.get_liste_prix_from_json(id)
        if not liste_prix:
            raise HTTPException(status_code=404, detail=f"No price data for crypto {id}")

        # Convert to DataFrame
        liste_prix = pd.DataFrame(liste_prix, columns=['date', 'price'])
        
        # Append new price
        now = datetime.now().date()
        liste_prix.loc[len(liste_prix)] = [now, valeur]

        # Calculate VaR
        return await varService.calcul_var_one_crypto(id)

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