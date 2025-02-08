import time
import pandas as pd
from app.services.coinGeckoService import CoinGeckoService

coingeckoservice = CoinGeckoService()

class IndexService:
    def calculate_index(self,crypto_list, base_market_cap):
        market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in crypto_list)
        index_value = (market_cap / base_market_cap) * 100  # Utilisation du market cap initial comme diviseur
        return round(index_value, 4), market_cap
    
    def set_Index(self):
        print("Démarrage de l'indice crypto...")
        base_market_cap = None  # Initialisation du diviseur de base
        
        # while True:
        try:
            filtered_data = coingeckoservice.callCoinGeckoListeCrypto()
            # filtered_data = filter_data(data)
            
            if base_market_cap is None:
                base_market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in filtered_data)
            
            index_value, total_market_cap = self.calculate_index(filtered_data, base_market_cap)
            print(f"Indice mis à jour: {index_value:.4f}\n")
            
            df = pd.DataFrame([{
                "Nom": coin["name"],
                "Prix (USD)": f"{coin['current_price']:.2f}",
                "Circulating Supply": f"{coin['circulating_supply']:,}",
                "Volume (USD)": f"{coin['total_volume']:.2f}",
                "Poids (%)": f"{(coin['current_price'] * coin['circulating_supply'] / total_market_cap * 100):.2f}"
            } for coin in filtered_data])
            
            # print(df.to_string(index=False))
            # put df in a csv file
            df.to_csv('app/index/index.csv', index=False)
            
        except Exception as e:
            print("Erreur lors de la mise à jour de l'indice:", e)
            # time.sleep(1200) 
            
    def get_csv_index(self):
        df = pd.read_csv('app/index/index.csv')
        return df