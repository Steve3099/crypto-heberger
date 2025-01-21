class CoinGeckoService:
    def excludeStableCoin(self, listeCoin):
        # List of known stablecoin symbols to exclude
        stablecoin_symbols = {"usdt", "usdc", "busd", "dai", "tusd", "ust", "gusd", "pax", "eurs", "frax", "husd"}
        
        listeRetour = []
        for el in listeCoin:
            # Exclude known stablecoins by symbol
            if el.get("symbol", "").lower() in stablecoin_symbols:
                continue
            
            # Exclude assets with minimal price change (e.g., ±1% in 24h)
            price_change_percentage_24h = el.get("price_change_percentage_24h", 0)
            if abs(price_change_percentage_24h) < 1:
                continue
            
            # Add non-stablecoins to the result list
            listeRetour.append(el)
        
        return listeRetour