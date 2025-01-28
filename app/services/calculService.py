#class cacluclService
from decimal import Decimal
import json
import math
import pandas as pd
import numpy as np
from app.services.callApiService import getHistorique


class CalculService:
    def calculRendements(self,prixF,prixAf):
        #call function logarythme
        return math.log(prixF/prixAf)
    
    def calculVolatilliteJournaliere(self,listePrix):
        
        # mettre liste prix dans un dataFrame
        listePrix = pd.DataFrame(listePrix,columns=['date','price'])
        
        # cacul rendement et la somme des rendement
        listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))
        
        # Supprimer les valeurs NaN
        listePrix.dropna(inplace=True)
        
        # Calcul de la volatilité historique
        volatilite  = listePrix['log_return'].std()
        
        return volatilite
    
    def getListeVolatilite(self,listePrix):
        listeVolatilite = []
        indice = 0
        for i in range(len(listePrix)-2):
            if indice == 0:
                listeVolatilite.append(self.calculVolatilliteJournaliere(listePrix))
            else:
                price = listePrix[:-indice]
                listeVolatilite.append(self.calculVolatilliteJournaliere(price))
            indice += 1    
        return listeVolatilite
        
    
    def top10volatiliteJournaliere(self,listeCrypto):
        listeVolatilite= []
        i = 0;
        for el in listeCrypto:
            # a changer
            if i < 10:
                
                historique = getHistorique(coin = el.get("id",''))
                # print(len(historique))
                historique_data = json.loads(historique)
                # Extract prices
                prices = historique_data.get("prices", [])
                #calcul volatilite
                prices = [price[1] for price in prices]
                volatilite = self.calculVolatilliteJournaliere(prices)
                retour = {
                    "coin":el,
                    "volatiliteJournaliere": volatilite,
                    "volatiliteAnnuel" : volatilite * math.sqrt(365)
                }
                listeVolatilite.append(retour)
                i+=1
            else:
                break
            
        # sort list desc by volatilite
        
        listeVolatilite.sort(key=lambda x: x.get("volatiliteJournaliere",0),reverse=True)
        
        
        
        return listeVolatilite
    
    
    def top5CroissanceDevroissance(self,listeCrypto):
        # sort list desc by price_change_24h
        
        listeCrypto.sort(key=lambda x: x.get("price_change_percentage_24h",0),reverse=True)
        retour = {
            "top5Croissance": listeCrypto[:5],
            "top5Decroissance": listeCrypto[-5:]
        }
        
        return retour
    
    def getListePrix(self, listeCrypto = []):
        listeRetour = []
        i = 0;
        for el in listeCrypto:
            # a changer
            if i < 10:
                historique = getHistorique(days = 90,coin = el.get("id",''))
                
                historique_data = json.loads(historique)
                
                # Extract prices
                prices = historique_data.get("prices", [])
                #calcul volatilite
                prices = [price[1] for price in prices]
                
                listeRetour.append(prices)
                i+=1
            else:
                break
            
        return listeRetour
    def getvolatilitePortefeuil(self,listeCrypto,listePrix):
        # calcul matrice de covariances
        sommeTotale = 0
        rows = len(listeCrypto)
        cols = len(listeCrypto)
        matrice = [[-1 for _ in range(cols)] for _ in range(rows)]
        for i in range(0,len(listePrix)):
            volatiliteI = self.getListeVolatilite(listePrix[i])
            wheightI = listeCrypto[i].get("weight",0)
            sommeI = 0
            for j in range(0,len(listePrix)):
                if i == j:
                    volatiliteJ = volatiliteI
                else:
                    volatiliteJ = self.getListeVolatilite(listePrix[j])
                wheightJ = listeCrypto[j].get("weight",0)
                produit =0
                for k in range(0,len(volatiliteJ)):
                    produit += volatiliteI[k] * volatiliteJ[k]
                
                sommeI += Decimal(produit / len(volatiliteJ)) * wheightI * wheightJ
                matrice[i][j] = sommeI
                matrice[j][i] = sommeI
            # print(matrice[i])
            sommeTotale += sommeI
        volatilitePortefeuil = math.sqrt(sommeTotale)
                # matrice.append(result)
                
        return volatilitePortefeuil,matrice
    
    def getHistoriqueVolatiliteGenerale(self,nombrejour,listeCrypto,listePrix):
        
        listVolatilitePortefeuille = []
        for i in range(0,nombrejour-2):
            if len(listePrix[0]) >= 3:
                res,matrice = self.getvolatilitePortefeuil(listeCrypto,listePrix)
                listVolatilitePortefeuille.append(res)
                listePrix = self.removeFirstLine(listePrix)
        return listVolatilitePortefeuille
    
    def removeFirstLine(self,listePrix):
        listeRetour = []
        # remove firs line of each element in listeprix
        for el in listePrix:
            listeRetour.append(el[1:])
        
        return listeRetour
    
    def normalize_weights(self,liste_crypto_market_cap):
        total_market_cap = 0
    
        for i in range(len(liste_crypto_market_cap)):
            total_market_cap += liste_crypto_market_cap[i]
    
        liste_crypto_weight = []
        for i in range(len(liste_crypto_market_cap)):
            weight = liste_crypto_market_cap[i] / total_market_cap
            liste_crypto_weight.append(weight)
        return liste_crypto_weight

    def round_weights(self,liste_weight):
        somme_weight = 0.0
        for i in range(len(liste_weight)):
            liste_weight[i] = round(liste_weight[i], 4)
            somme_weight += liste_weight[i]
        if somme_weight != 1.0:
            error = Decimal('1.0') - Decimal(str(somme_weight))
            min_weight = min(liste_weight)
            index_min = liste_weight.index(min_weight)
            if error > 0:
                # enlever l'erreur au poids le plus faible
                liste_weight[index_min] = float(Decimal(str(liste_weight[index_min])) + Decimal(str(error)))
            else:
                # ajouter l'erreur au poids le plus fort
                liste_weight[index_min] = float(Decimal(str(liste_weight[index_min])) - Decimal(str(error)))
        return liste_weight