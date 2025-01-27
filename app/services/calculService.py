#class cacluclService
from decimal import Decimal
import json
import math

from app.services.callApiService import getHistorique


class CalculService:
    def calculRendements(self,prixF,prixAf):
        #call function logarythme
        return math.log(prixF/prixAf)
    
    def calculVolatilliteJournaliere(self,listePrix):
        populationTotale = len(listePrix)-1
        # parcouriri la liste par le derniere indice et ignorer la derniere indice
        sommeRendemen = 0
        for i in range(0,len(listePrix)-2):
            sommeRendemen += self.calculRendements(listePrix[i+1],listePrix[i])
        
        somme = 0
        for i in range(0,len(listePrix)-2):
            somme+= math.pow(self.calculRendements(listePrix[i+1],listePrix[i]) - sommeRendemen,2)
            
        volatiliteJournaliere = math.sqrt(somme/populationTotale)
        
        return volatiliteJournaliere
    
    def getListeVolatilite(self,listePrix):
        listeVolatilite = []
        indice = 0
        for i in range(1,len(listePrix)-2):
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
    
    async def getListePrix(self, listeCrypto = []):
        listeRetour = []
        i = 0;
        for el in listeCrypto:
            # a changer
            if i < 10:
                historique = await getHistorique(days = 9,coin = el.get("id",''))
                
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
            # print(len(listePrix))
        # for i in range(0,l):
        #     res = self.getvolatilitePortefeuil(nombrejour,listeCrypto,listePrix)
        #     listVolatilitePortefeuille.append(res)
        return listVolatilitePortefeuille
    
    def removeFirstLine(self,listePrix):
        listeRetour = []
        # remove firs line of each element in listeprix
        for el in listePrix:
            listeRetour.append(el[1:])
        
        return listeRetour