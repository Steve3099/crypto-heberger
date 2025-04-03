from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.services.coinGeckoService import CoinGeckoService
coinGeckoService = CoinGeckoService()

from fastapi import HTTPException

from app.services.voaltiliteService import VolatiliteService
from app.services.cryptoService import CryptoService
from app.services.varService import VarService
volatiliteService = VolatiliteService()
cryptoService = CryptoService()
varService = VarService()
class SimulateurService:
    def __init__(self):
        # Initialize any required attributes
        pass
    
    async def simulateur_volatilite(self, id,valeur = []):
        
        historique_volatilite = await volatiliteService.get_historique_volatilite_crypto_from_json(id)
        historique_prix = await cryptoService.get_liste_prix_from_json(id)
        # return historique_volatilite
        now = datetime.now().date()
        for i in range(len(valeur)):
            if valeur[i] < 0:
                raise HTTPException(status_code=400, detail="valeur must be positive")
            historique_prix.loc[len(historique_prix)] = [now, valeur[i]]
            volatilite = await volatiliteService.calcul_Volatillite_Journaliere_one_crypto(historique_prix)
            new_volatilite= {
                "date": now,
                "valeur": volatilite
            }
            historique_volatilite.append(new_volatilite)
            # add one day to now
            now = now + timedelta(days=1)
        return historique_volatilite
    
    async def simulateur_var(self, id,valeur):
        # Code
        
        # valuer must be positive
        if valeur < 0:
            raise HTTPException(status_code=400, detail="valeur must be positive")
        
        # get liste prix crypto
        # liste_prix = await cryptoService.get_liste_prix_from_json(id)
        now = datetime.now().date()
            
        liste_prix.loc[len(liste_prix)] = [now, valeur]
        return await varService.calcul_var_one_crypto(id)
    
    async def simulate_crypto_price(self,S0, mu, sigma, T, n_simulations=20, n=90):
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
        for i in range(n_simulations):
            W = np.random.normal(0, np.sqrt(dt), time_steps)  # Bruit Brownien
            W = np.cumsum(W)  # Processus de Wiener
            t = np.linspace(0, T, time_steps)
            price_paths[:, i] = S0 * np.exp((mu - 0.5 * sigma**2) * t + sigma * W)
        
        return price_paths
    
    async def calcul_Volatillite_Journaliere_one_crypto(self,listePrix):
        
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
    
    # async def run_similation_cupro_price(self,crypto_id,periode = 90,n_simulations = 20):
    #     # Code
    #     try:
    #         liste_prix = await coinGeckoService.get_historical_prices(crypto_id, days=periode)

    #         volatilite,mean_rendement = await self.calcul_Volatillite_Journaliere_one_crypto(liste_prix[:-2])

    #         prix_inital = liste_prix['price'].iloc[-1]

            
    #         # ---- Paramètres ----
    #         S0 = prix_inital      # Prix initial en $
    #         mu = mean_rendement     # Rendement moyen quotidien
    #         sigma = volatilite   # Volatilité historique quotidienne
    #         T = periode          # Nombre de jours à simuler
    #         time_steps = periode      # Nombre de pas de temps
    #         # Nombre de trajectoires

    #         # ---- Simulation ----
    #         simulated_paths = await self.simulate_crypto_price(S0, mu, sigma, T, n_simulations,n =time_steps)
            
    #         return simulated_paths
    #     except Exception as e:
    #         return str(e)
    
    async def run_similation_cupro_price(self, crypto_id, periode=90, n_simulations=20):
        try:
            liste_prix = await coinGeckoService.get_historical_prices(crypto_id, days=periode)

            volatilite, mean_rendement = await self.calcul_Volatillite_Journaliere_one_crypto(liste_prix[:-2])

            prix_initial = liste_prix['price'].iloc[-1]

            S0 = prix_initial
            mu = mean_rendement
            sigma = volatilite
            T = periode
            time_steps = periode

            simulated_paths = await self.simulate_crypto_price(S0, mu, sigma, T, n_simulations, n=time_steps)
            
            mean_prices = np.mean(simulated_paths, axis=1)
            
            # Transpose the array so each list represents a full simulation
            simulated_paths_list = np.transpose(simulated_paths).tolist()

            # Compute mean prices at each time step
            mean_prices = np.mean(simulated_paths, axis=1).tolist()

            # Return in JSON format
            return {
                "simulated_paths": simulated_paths_list,  # Each list is a simulation now
                "mean_prices": mean_prices
            }
            
            # return {"simulated_prices": simulated_paths}  # Wrap the list inside a dictionary ✅

        except Exception as e:
            return {"error": str(e)}  # Return errors in a JSON-friendly way ✅
