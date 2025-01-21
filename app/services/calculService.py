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
            sommeRendemen += self.calculRendements(listePrix[i+1],listePrix[i])
        
        moyenneRendemen = sommeRendemen / populationTotale
        
        somme = 0
        for i in range(0,len(listePrix)-1):
            somme+= math.pow(self.calculRendements(listePrix[i+1],listePrix[i]) - moyenneRendemen,2)
            
        volatiliteJournaliere = math.sqrt(populationTotale*somme)
        
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
        
    
    def top5volatiliteJournaliere(self,listeCrypto):
        listeVolatilite= []
        i = 0;
        for el in listeCrypto:
            if i < 10:
                # print(el.get("id",''))
                
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
        return listeVolatilite