import pandas as pd

class Coin:
    def __init__(self):
        pass
    
    def set_historique_volatilite_to_json(self,history):
        # put historique into json
        pd.DataFrame(history).to_json('app/json/historique/historique.json')
        