from app.services.coinGeckoService import CoinGeckoService
import pandas as pd
import numpy as np

coinGeckoService = CoinGeckoService()


class VarService:
    def __init__(self):
        pass
    
    async def calculate_var(self,liste_price,liste_crypto,list_weight, percentile=1):
        # liste_crypto= []
        # liste_price = []
        # list_weight= []
        
        merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("name")})
        for i in range(1, len(liste_price)):
            liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("name")})
            merged = pd.merge(merged, liste_price[i], on='date')
            
        # put merge prix to csv
        merged.to_csv('Varlisteprix.csv', index=False)
        
        # Joindre les datasets sur les dates
        
        for i in range(len(liste_crypto)):
            merged['log_return_'+liste_crypto[i].get("name")] = np.log(merged['price_'+liste_crypto[i].get("name")] / merged['price_'+liste_crypto[i].get("name")].shift(1))
        
        
    # Supprimer les valeurs NaN
        merged.dropna(inplace=True)
        
        # Calcul des rendements journaliers du portefeuille
        val = 0
        for i in range(len(list_weight)):
            val += list_weight[i] * merged['log_return_' + liste_crypto[i].get("name")]
        
        merged['portfolio_return'] = val
        
        # Calcul de la VaR historique du portefeuille (percentile spécifié)
        var_percentile_portfolio = np.percentile(merged['portfolio_return'], percentile)
        
        # Calcul de la VaR historique pourtout les cypto
        liste_var_percentile_crypto = []
        for i in range(len(liste_crypto)):
            var_percentile_crypto = np.percentile(merged['log_return_' + liste_crypto[i].get("name")], percentile)
            liste_var_percentile_crypto.append(var_percentile_crypto)
        
        
        # var_percentile_btc = np.percentile(merged['log_return_btc'], percentile)
        # var_percentile_eth = np.percentile(merged['log_return_eth'], percentile)
        return liste_var_percentile_crypto , var_percentile_portfolio
    
    async def set_Var_for_each_crypto(self):
        vs_currency = "usd" 
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        liste_prix = []
        liste_market_cap =[]
        somme_market_cap = 0
        for el in liste_crypto_start:
            historique = coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
            # if len(historique) > 90:
            #     liste_crypto.append(el)
            liste_prix.append(historique)
        
            market_cap = await coinGeckoService.get_market_cap(el.get("id"))
            liste_market_cap.append(market_cap)
            somme_market_cap += market_cap
            
        liste_weight = []
        for market_cap in liste_market_cap:
            liste_weight.append(market_cap / somme_market_cap)
            
        liste_var, var_portfolio = await self.calculate_var(liste_prix, liste_crypto_start, liste_weight, percentile=1)
        print("=== Résultats ===")
        # poids des cfypto
        for i in range(len(liste_weight)):
            print(f"Weight for {liste_crypto_start[i].get('name')} : {liste_weight[i]}")
            
        for i in range(len(liste_var)):
            print(f"VaR historique de {liste_crypto_start[i].get('name')} à 99% : {liste_var[i]:.4f}")

        # print(f"VaR historique du BTC à 99% : {var_btc:.4f}")
        # print(f"VaR historique de l'ETH à 99% : {var_eth:.4f}")
        print(f"VaR historique du portefeuille à 99% : {var_portfolio:.4f}")