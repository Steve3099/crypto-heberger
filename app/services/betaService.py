from app.services.indexService import IndexService
from app.services.coinGeckoService import CoinGeckoService
from app.services.rendementService import RendementService
import scipy.stats as stats

indexService = IndexService()
coingeckoservice = CoinGeckoService()
rendementservice = RendementService()

class BetaService:
    
    async def get_beta_on_crypto(self,id):
        
        list_index = await indexService.get_liste_index_from_json_file()
        
        list_index = list_index[-90:]
        
        list_index_used = []
        for el in list_index:
            list_index_used.append(el["value"])
        
        list_prix = await coingeckoservice.get_prix_one_crypto(id,days=1)
        list_prix = list_prix.tail(91)
        
        list_rendement = await rendementservice.get_rendement(list_prix)
        market = list_index_used
        portfolio = list_rendement
        # return len(market),len(portfolio)
        slope, intercept, r_value, _, _ = stats.linregress(market, portfolio)
        data = {
            "beta_portefeuille":slope,
            "alpha_portefeuille":intercept,
            "r²":r_value**2
        }
        return data
        print(f"Bêta du portefeuille : {slope:.6f}")
        print(f"Alpha du portefeuille : {intercept:.6f}")
        print(f"R² : {r_value**2:.6f}")

        
        pass