from app.services.indexService import IndexService
from app.services.coinGeckoService import CoinGeckoService
from app.services.rendementService import RendementService
from app.services.cryptoService import CryptoService
import scipy.stats as stats
from fastapi import HTTPException

indexService = IndexService()
coingeckoservice = CoinGeckoService()
rendementservice = RendementService()
cryptoService = CryptoService()

class BetaService:
    async def get_beta_on_crypto(self, id):
        try :
            """Calculate beta, alpha, and R² for a cryptocurrency relative to the market index."""
            
            # Fetch crypto price data (last 91 days for returns calculation)
            # list_prix = await coingeckoservice.get_prix_one_crypto(id, days=181)
            list_prix = await cryptoService.get_liste_price_binance_from_json(id)
            
            list_prix = list_prix.tail(181)
            # take 24 price for each day
            list_prix = list_prix[::24]
            
            
            # Fetch index data (last 90 days)
            list_index = await indexService.get_liste_index_from_json_file()
            list_index = list_index[-180:]
            list_index_used = [el["value"] for el in list_index]

            
            # return list_prix
            # Calculate returns
            list_rendement = await rendementservice.get_rendement(list_prix)
            list_rendement = list_rendement[-180:]
            
            # return list_rendement
            # Validate data
            if len(list_index_used) < 2 or len(list_rendement) < 2:
                raise HTTPException(status_code=400, detail="Insufficient data for beta calculation")
            if len(list_index_used) != len(list_rendement):
                raise HTTPException(status_code=400, detail="Mismatched data lengths for market and portfolio")

            # Perform linear regression
            market = list_index_used
            portfolio = list_rendement
            slope, intercept, r_value, _, _ = stats.linregress(market, portfolio)
            # print(list_rendement)
            # return list_prix
            return {
                "beta_portefeuille": slope,
                "alpha_portefeuille": intercept,
                "r²": r_value ** 2,
                "cloud_points": [{"x": x, "y": y} for x, y in zip(market, portfolio)]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating beta: {str(e)}")
        
        