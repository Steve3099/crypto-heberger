import pandas as pd
import numpy as np
class RendementService:
    
    async def get_rendement(self,liste_prix):
        liste_prix['log_return']=np.log(liste_prix['price'] / liste_prix['price'].shift(1))
        return liste_prix['log_return'].values[1:]
    