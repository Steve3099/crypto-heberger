from decimal import Decimal

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
            # price_change_percentage_24h = el.get("price_change_percentage_24h", 0)
            # if abs(price_change_percentage_24h) < 1:
            #     continue
            
            # Add non-stablecoins to the result list
            listeRetour.append(el)
        
        return listeRetour
    
    def getListeCryptoWithWeight(self,listeCrypto):
        listeRetour = []
        somme = 0
        for el in listeCrypto:
            somme += int(el.get("current_price","")) * int(el.get("circulating_supply",""))
        
        for el in listeCrypto:
            weight = (int(el.get("current_price","")) * int(el.get("circulating_supply",""))) / somme
            el["weight"] = round(weight,2)
            listeRetour.append(el)
            
        return listeRetour
    def getGraphWeight(self,listeCrypto):
        # if wieght < 1% we put all of then in a coin labeed other and add all thier weight together
        weightOther = 0
        listeRetourOther = []
        for el in listeCrypto:
            if el.get("weight") < 0.01:
                weightOther += el.get("weight")
            else:
                listeRetourOther.append(el)
        listeRetourOther.append({ "coin":"other","weight":weightOther})
        
        #  arrondier weght to 2 decimal
        sommeweight =0
        for el in listeRetourOther:
            el["weight"] = round(Decimal(el.get("weight")),2)
            sommeweight +=el["weight"]
            
        if sommeweight != 1:
            listeRetourOther[-1]["weight"] = round(Decimal(listeRetourOther[-1]["weight"]) + 1 - Decimal(sommeweight),2)
            
        return listeRetourOther