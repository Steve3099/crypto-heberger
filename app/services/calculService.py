#class cacluclService
import math


class CalculService:
    def calculRendements(self,prixF,prixAf):
        #call function logarythme
        return math.log(prixF/prixAf)
    
    def calculVolatiliteJournaliere(self,nombreJour,listePrixJournaliere):
        populationTotal = (1/(len(listePrixJournaliere)-1))
        
        moyenneRendemen = 0
        for i in range(0,nombreJour):
            moyenneRendemen += self.calculRendements(listePrixJournaliere[i-1][1],listePrixJournaliere[i][1]) 
            
        moyenneRendemen = moyenneRendemen / populationTotal
        
        somme = 0
        for i in range(0,nombreJour):
            somme+= math.pow(self.calculRendements(listePrixJournaliere[i-1][1],listePrixJournaliere[i][1]) - moyenneRendemen,2)
        
        volatiliteJournaliere = math.sqrt(populationTotal*somme)
        
        return volatiliteJournaliere
        