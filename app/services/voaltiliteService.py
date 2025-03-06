from app.services.calculService import CalculService
from app.services.coinGeckoService import CoinGeckoService
from app.services.callCoinMarketApi import CallCoinMarketApi
from app.services.indexService import IndexService
from datetime import datetime
import json
import pandas as pd
import numpy as np

calculService = CalculService()
coinGeckoService = CoinGeckoService()
callCoinMArketApi = CallCoinMarketApi()

class VolatiliteService:
    async def set_historique_volatilite(self):
        vs_currency="usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        # liste_crypto_start = liste_crypto_start[:80]
        # liste_crypto_start = liste_crypto_start[250:252]
        # get liste de prix
        
        liste_crypto = []
        liste_prix = []
        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
            if len(historique) > 90:
                liste_crypto.append(el)
                liste_prix.append(historique)
        liste_crypto = liste_crypto[:80]
        liste_prix = liste_prix[:80]
        # get liste_weight
        liste_market_cap =[]
        for el in liste_crypto:
            market_cap = await coinGeckoService.get_market_cap(el.get("id"))
            liste_market_cap.append(market_cap)
        
        liste_weight = calculService.normalize_weights(liste_market_cap)
        
        liste_weight = calculService.round_weights(liste_weight)
        liste_volatilite_portefeuille = []
        
        for i in range(len(liste_prix[0])-2):
            liste_prix_utiliser = []
            for el in liste_prix:
                test = []
                if i!= 0:
                    test = el.iloc[:-i] 
                else:
                    test =  el
                liste_prix_utiliser.append(test)
            
            liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculService.calculate_statistics(liste_prix_utiliser,liste_crypto,liste_weight)
            liste_volatilite_portefeuille.append(portfolio_volatility_mat)
            
        # put together adate liste_pirx avec la liste_volatilite_portefeuille in json folder
        liste_volatilite = []

        # Ensure liste_volatilite_portefeuille is defined before using it
        # return liste_prix[0]
        
        for i in range(0, len(liste_volatilite_portefeuille)):  
            temp = {
                "date": liste_prix[0]["date"][i],
                "value": liste_volatilite_portefeuille[len(liste_volatilite_portefeuille)-i-1]
            }
            liste_volatilite.append(temp)

        # Write liste_volatilite to JSON file
        with open('app/json/volatilite/volatilite.json', 'w', encoding='utf-8') as f:
            json.dump(liste_volatilite, f, indent=4, ensure_ascii=False)
        
    async def update_historique_volatilite_generale(self):
        # read the file
        with open('app/json/volatilite/volatilite.json', 'r') as f:
            data = json.load(f)
        # get the last element
        last_element = data[-1]
        
        # check if the difference between the last date and now is greater than 2 day
        last_date = datetime.strptime(last_element["date"], '%Y-%m-%dT%H:%M:%S.%f')
        now = datetime.now()
        difference = now - last_date
        difference = difference.days
        # if the difference is greater than 2 day
        # return difference
        if difference >= 2:
            vs_currency="usd"
            liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
            # get liste de prix
            
            liste_crypto = []
            liste_prix = []
            for el in liste_crypto_start:
                historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
                if len(historique) > 90:
                    liste_crypto.append(el)
                    liste_prix.append(historique[:-2])
            liste_crypto = liste_crypto[:80]
            liste_prix = liste_prix[:80]
            # get liste_weight
            liste_market_cap =[]
            for el in liste_crypto:
                market_cap = await coinGeckoService.get_market_cap(el.get("id"))
                liste_market_cap.append(market_cap)
            
            liste_weight = calculService.normalize_weights(liste_market_cap)
            
            liste_weight = calculService.round_weights(liste_weight)
            liste_volatilite_portefeuille = []
            for i in range(0,difference-1):
                liste_prix_utiliser = []
                for el in liste_prix:
                    test = []
                    if i!= 0:
                        test = el[:-i] 
                    else:
                        test =  el
                    liste_prix_utiliser.append(test)
                liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculService.calculate_statistics(liste_prix_utiliser,liste_crypto,liste_weight)
                
                liste_volatilite_portefeuille.append(portfolio_volatility_mat)
            
            # put the liste_volatilite_portefeuille into the bottom oth json file
            liste_volatilite = []
            
            for i in range(0, len(liste_volatilite_portefeuille)):  
                temp = {
                    "date": liste_prix[0]["date"][len(liste_prix[0])-difference+1+i],
                    "value": liste_volatilite_portefeuille[-i-1]
                }
                liste_volatilite.append(temp)
                await self.update_volatilite_annuel(temp["date"],temp["value"] * np.sqrt(365))
            
            # add liste_volatilite to bootom of JSON file
            with open('app/json/volatilite/volatilite.json', 'r') as f:
                data = json.load(f)
                data += liste_volatilite
            with open('app/json/volatilite/volatilite.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
    async def get_historique_volatilite_from_json(self,date_debut,date_fin):
        try:
            with open('app/json/volatilite/volatilite.json', 'r') as f:
                data = json.load(f)
                liste = []
                for el in data:
                    if el["date"] >= date_debut and el["date"] <= date_fin:
                        liste.append(el)
                return liste
        except FileNotFoundError:
            return []
        
    async def get_last_volatilite_from_json(self):
        with open('app/json/volatilite/volatilite.json', 'r') as f:
            data = json.load(f)
            return data[-1]
        
    async def set_volatilite_journaliere_crypto(self):
        pass
            
            
    async def calcul_Volatillite_Journaliere_one_crypto(self,listePrix):
        
        # mettre liste prix dans un dataFrame
        listePrix = pd.DataFrame(listePrix,columns=['date','price'])
        
        # cacul rendement et la somme des rendement
        listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))
        
        # Supprimer les valeurs NaN
        listePrix.dropna(inplace=True)
        
        # Calcul de la volatilité historique
        volatilite  = listePrix['log_return'].std()
        
        return volatilite        
    
    async def get_historique_Volatilite(self,listePrix):
        listeVolatilite = []
        indice = 0
        for i in range(len(listePrix)-2):
            if indice == 0:
                listeVolatilite.append(await self.calcul_Volatillite_Journaliere_one_crypto(listePrix))
            else:
                price = listePrix[:-indice]
                listeVolatilite.append(await self.calcul_Volatillite_Journaliere_one_crypto(price))
            indice += 1    
        return listeVolatilite
    
    async def set_historique_volatiltie_for_each_crypto_to_json(self):
        vs_currency="usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        liste_crypto = []
        liste_prix = []
        liste_historique = []
        
        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
            if len(historique) > 90:
                liste_crypto.append(el)
                
                liste_prix.append(historique)
                historique_volatilite = await self.get_historique_Volatilite(historique)
                # liste_historique.append(historique_volatilite)
                historique_volatilite_crypto = []
                for i in range(1,len(historique[:-2])):
                    
                    temp = {
                        "date": liste_prix[0]["date"][i],
                        "value": historique_volatilite[-i]
                    }
                    historique_volatilite_crypto.append(temp)
                # Write historique_volatilite_crypto to JSON file
                with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'w', encoding='utf-8') as f:
                    json.dump(historique_volatilite_crypto, f, indent=4, ensure_ascii=False)
    
    async def update_historique_volatilite_for_each_crypto(self):
        vs_currency="usd"
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        # date now
        now = datetime.now()
        
        for el in liste_crypto_start:
            historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
            if len(historique) <= 90:
                continue
            
            # check if file exist
            try:
                f = open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'r')
            except FileNotFoundError:
                # print(el.get("id"))
                await self.set_historique_volatilite_for_one_crypto(el.get('id'))
            # read the file
            with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'r') as f:
                # check if f is not null
                if f is None:
                    historique_volatilite = await self.get_historique_Volatilite(historique)
                # liste_historique.append(historique_volatilite)
                    historique_volatilite_crypto = []
                    for i in range(1,len(historique[:-2])):
                        
                        temp = {
                            "date": historique[0]["date"][i],
                            "value": historique_volatilite[-i]
                        }
                        historique_volatilite_crypto.append(temp)
                    # Write historique_volatilite_crypto to JSON file
                    with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'w', encoding='utf-8') as f:
                        json.dump(historique_volatilite_crypto, f, indent=4, ensure_ascii=False)
                    data = historique_volatilite_crypto
                else:
                    data = json.load(f)
                
            # get the last element
            last_element = data[-1]
        
        # check if the difference between the last date and now is greater than 2 day
            last_date = datetime.strptime(last_element["date"], '%Y-%m-%dT%H:%M:%S.%f')
            difference = now - last_date
            difference = difference.days
            if difference >= 2: 
                historique = await coinGeckoService.get_historical_prices(el.get('id'),vs_currency,90)
                listeVolatilite = []
                for i in range(0,difference-1):
                    if i == 0:
                        listeVolatilite.append(await self.calcul_Volatillite_Journaliere_one_crypto(historique))
                    else:
                        price = historique[:-i]
                        listeVolatilite.append(await self.calcul_Volatillite_Journaliere_one_crypto(price))
                    
                # put the listeVolatilite into the bottom oth json file
                liste_volatilite = []
                for i in range(0, len(listeVolatilite)):  
                    temp = {
                        "date": historique["date"][len(historique[:-2])-difference+i+1],
                        "value": listeVolatilite[-i-1]
                    }
                    liste_volatilite.append(temp)
                
                # add liste_volatilite to bootom of JSON file
                with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'r') as f:
                    data = json.load(f)
                    data += liste_volatilite
                with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    
    async def get_historique_volatilite_crypto_from_json(self,id,date_start="2024-11-29T00:00:00.000",date_end=None):
        if date_end is None:
            date_end = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        with open('app/json/volatilite/'+id+'_volatilite.json', 'r') as f:
            data = json.load(f)
            liste = []
            for el in data:
                if el["date"] >= date_start and el["date"] <= date_end:
                    liste.append(el)
            return liste
    
    async def set_historique_volatilite_for_one_crypto(self,id):
        vs_currency="usd"
        
        # for el in liste_crypto_start:
        historique = await coinGeckoService.get_historical_prices(id,vs_currency,90)
        print(len(historique))
        if len(historique) > 90:
            
            historique_volatilite = await self.get_historique_Volatilite(historique)
            # liste_historique.append(historique_volatilite)
            historique_volatilite_crypto = []
            for i in range(1,len(historique[:-2])):
                
                temp = {
                    "date": historique["date"][i],
                    "value": historique_volatilite[-i]
                }
                historique_volatilite_crypto.append(temp)
            # Write historique_volatilite_crypto to JSON file or create the file if it doesn't exist
            with open('app/json/volatilite/'+id+'_volatilite.json', 'w', encoding='utf-8') as f:
                json.dump(historique_volatilite_crypto, f, indent=4, ensure_ascii=False)
            
    async def get_top_10_volatilite_crypto(self):
        # await self.get_historique_volatilite_crypto_from_json("bitcoin")
        liste = await coinGeckoService.get_liste_crypto_with_weight()
        
        # sort it by volatiliteJournaliere Decroissant
        liste.sort(key=lambda x: x.get("volatiliteJournaliere",0),reverse=True)
        return liste[:10]
        
    async def set_volatilite_annuel(self):
        # get volatilite journalier form json
        with open('app/json/volatilite/volatilite.json', 'r') as f:
            data = json.load(f)
            liste = []
            for el in data:
                temp = {
                    "date": el["date"],
                    "value": el["value"] * np.sqrt(365)
                }
                liste.append(temp)
            
            # Write liste to JSON file
            with open('app/json/volatilite/volatilite_annuel/historique.json', 'w', encoding='utf-8') as f:
                json.dump(liste, f, indent=4, ensure_ascii=False)
    
    async def update_volatilite_annuel(self,date,value):
        # read the file
        with open('app/json/volatilite/volatilite_annuel/historique.json', 'r') as f:
            data = json.load(f)
            data.append({"date":date,"value":value})
        # add data to JSON file
        with open('app/json/volatilite/volatilite_annuel/historique.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    async def get_volatilite_annuel_historique(self,date_debut,date_fin):
        
        # check that nor date_debut nor date fin is null
        if date_fin is None:
            date_fin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        if date_debut is None:
            raise ValueError("date_debut cannot be null")
        
        # date_debut must be less than date_fin
        if date_debut > date_fin:
            raise ValueError("date_debut must be less than date_fin")
        
        with open('app/json/volatilite/volatilite_annuel/historique.json', 'r') as f:
            data = json.load(f)
            liste = []
            for el in data:
                if el["date"] >= date_debut and el["date"] <= date_fin:
                    liste.append(el)
            return liste
     
    async def set_historique_volatilite_annuel_per_cryto(self):
        liste_crypto_start = await coinGeckoService.get_liste_crypto_filtered()
        
        for el in liste_crypto_start:
            try:
                with open('app/json/volatilite/'+el.get("id")+'_volatilite.json', 'r') as f:
                    data = json.load(f)
                    liste = []
                    for vol in data:
                        temp = {
                            "date": vol["date"],
                            "value": vol["value"] * np.sqrt(365)
                        }
                        liste.append(temp)
                    
                    # Write liste to JSON file
                    with open('app/json/volatilite/volatilite_annuel/crypto/'+el.get("id")+'_volatilite_annuel.json', 'w', encoding='utf-8') as f:
                        json.dump(liste, f, indent=4, ensure_ascii=False)
            except FileNotFoundError:
                print(el.get('id'))
                continue
        return "volatilite annuel set"
    
    # 
                
