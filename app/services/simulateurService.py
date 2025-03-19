from datetime import datetime, timedelta

from app.services.voaltiliteService import VolatiliteService
from app.services.cryptoService import CryptoService
from app.services.varService import VarService
volatiliteService = VolatiliteService()
cryptoService = CryptoService()
varService = VarService()
class SimulateurService:
    def __init__(self):
        # Initialize any required attributes
        pass
    
    async def simulateur_volatilite(self, id,valeur = []):
        
        historique_volatilite = await volatiliteService.get_historique_volatilite_crypto_from_json(id)
        historique_prix = await cryptoService.get_liste_prix_from_json(id)
        # return historique_volatilite
        now = datetime.now().date()
        for i in range(len(valeur)):
            
            historique_prix.loc[len(historique_prix)] = [now, valeur[i]]
            volatilite = await volatiliteService.calcul_Volatillite_Journaliere_one_crypto(historique_prix)
            new_volatilite= {
                "date": now,
                "valeur": volatilite
            }
            historique_volatilite.append(new_volatilite)
            # add one day to now
            now = now + timedelta(days=1)
        return historique_volatilite
    
    async def simulateur_var(self, id,valeur):
        # Code
        # get liste prix crypto
        liste_prix = await cryptoService.get_liste_prix_from_json(id)
        now = datetime.now().date()
            
        liste_prix.loc[len(liste_prix)] = [now, valeur]
        return await varService.calcul_var_one_crypto(liste_prix)
        