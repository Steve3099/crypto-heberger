#class cacluclService
import json
import math

from app.services.callApiService import getHistorique


class CalculService:
    def calculRendements(self,prixF,prixAf):
        #call function logarythme
        return math.log(prixF/prixAf)
    
    def calculVolatilliteJournaliere(self,nombrejour,listePrix):
        populationTotale = len(listePrix)-1
        # parcouriri la liste par le derniere indice et ignorer la derniere indice
        sommeRendemen = 0
        for i in range(0,len(listePrix)-1):
            sommeRendemen += self.calculRendements(listePrix[i],listePrix[i+1])
        
        somme = 0
        for i in range(0,len(listePrix)-1):
            somme+= math.pow(self.calculRendements(listePrix[i],listePrix[i+1]) - sommeRendemen,2)
            
        volatiliteJournaliere = math.sqrt(somme/populationTotale)
        
        
        return volatiliteJournaliere
    
    def getListeVolatilite(self,nombrejour,listePrix):
        listeVolatilite = []
        indice = 0
        for i in range(0,len(listePrix)-2):
            if indice == 0:
                listeVolatilite.append(self.calculVolatilliteJournaliere(nombrejour-indice,listePrix))
            else:
                price = listePrix[:-indice]
                listeVolatilite.append(self.calculVolatilliteJournaliere(nombrejour-indice,price))
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
                volatilite = self.calculVolatilliteJournaliere(5, prices)
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
    
    def matriceCovariances(self,nombrejour = 90 , listeCrypto = []):
        listeRetour = []
        i = 0;
        for el in listeCrypto:
            # a changer
            if i < 10:
                historique = getHistorique(coin = el.get("id",''))
                historique_data = json.loads(historique)
                # Extract prices
                prices = historique_data.get("prices", [])
                #calcul volatilite
                prices = [price[1] for price in prices]
                
                listeRetour.append(prices)
                i+=1
            else:
                break
        # calcul matrice de covariances
        matrice = []
        sommeTotale = 0
        for i in range(0,len(listeRetour)):
            volatiliteI = self.getListeVolatilite(nombrejour,listeRetour[i])
            wheightI = listeCrypto[i].get("weight",0)
            sommeI = 0
            for j in range(0,len(listeRetour)):
                
                volatiliteJ = self.getListeVolatilite(nombrejour,listeRetour[j])
                wheightJ = listeCrypto[j].get("weight",0)
                produit =0
                for k in range(0,len(volatiliteJ)):
                    produit += volatiliteI[k] * volatiliteJ[k]
                
                sommeI += (produit / len(volatiliteJ)) * wheightI * wheightJ
                
            sommeTotale += sommeI
        volatilitePortefeuil = math.sqrt(sommeTotale)
                # matrice.append(result)
                
        return volatilitePortefeuil