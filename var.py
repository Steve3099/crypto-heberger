import requests
import pandas as pd
import numpy as np
import json
from decimal import Decimal, getcontext
import time
import math
getcontext().prec = 28

def get_liste_crypto(categorie_id="layer-1",page=1):
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "per_page": 250,
        "category": categorie_id,
        "page":page
        # "order": "volume_desc"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-uviXoVTxQUerBoCeZfuJ6c5y"
    }

    response = requests.get(url, headers=headers,params=params)
    df = json.loads(response.text)
    
    retour = []
    for i in range(len(df)):
        retour.append(df[i])
    
    return retour
def get_liste_symbole_by_id_categorie(id_Categorie):
    
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/category"
    params = {
        "id": id_Categorie
    }
    headers = {
        "accept": "application/json",
        "X-CMC_PRO_API_KEY": "d85a5f07-d675-48f5-8e8e-e9617ae7fcf3"
    }
    response = requests.get(url, headers=headers, params=params)
    data = json.loads(response.text)
    data  = data.get("data")
    liste_coin = data["coins"]
    
    liste_stablecoins = []
    for item in liste_coin:
        # put symbol to lower case  
        liste_stablecoins.append(item.get("symbol").lower())
    
    # put the liste symbole into csv
    with open("stablecoins.csv","w") as f:
        for symbol in liste_stablecoins:
            f.write(symbol + "\n")
    
    return liste_stablecoins

def excludeStableCoin(listeCoin):
    id_Stable_Coin = "604f2753ebccdd50cd175fc1"
    id_Wrapped_Token = "6053df7b6be1bf5c15e865ed"
    stablecoins = get_liste_symbole_by_id_categorie(id_Stable_Coin)
    wrapped_tokens = get_liste_symbole_by_id_categorie(id_Wrapped_Token)
    
    filtered = [coin for coin in listeCoin if 
                coin["symbol"].lower() not in stablecoins and 
                coin["symbol"].lower() not in wrapped_tokens and 
                coin["current_price"] is not None and
                (coin["total_volume"]  is None or coin["total_volume"] >= 2000000)]
    
    return filtered

def get_historical_prices(crypto, vs_currency='usd', days=90):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-pq44GDj1HKecURw2UA1uUYz8"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].round(2)
    return df[['date', 'price']]

def get_market_cap(crypto):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}'
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-pq44GDj1HKecURw2UA1uUYz8"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    market_cap = data['market_data']['market_cap']['usd']
    return market_cap

def normalize_weights(liste_crypto_market_cap):
    total_market_cap = 0
    
    for i in range(len(liste_crypto_market_cap)):
        total_market_cap += liste_crypto_market_cap[i]
    
    liste_crypto_weight = []
    for i in range(len(liste_crypto_market_cap)):
        weight = liste_crypto_market_cap[i] / total_market_cap
        liste_crypto_weight.append(weight)
    return liste_crypto_weight

def round_weights(liste_weight):
    somme_weight = Decimal('0')
    for i in range(len(liste_weight)):
        liste_weight[i] = Decimal(str(round(liste_weight[i], 4)))
        somme_weight += liste_weight[i]
    if somme_weight != 1.0:
        error = Decimal('1.0') - Decimal(str(somme_weight))
        min_weight = min(liste_weight)
        index_min = liste_weight.index(min_weight)
        
        if error > 0:
            liste_weight[index_min] = Decimal(str(liste_weight[index_min])) + Decimal(str(error))
        else:
            liste_weight[index_min] = Decimal(str(liste_weight[index_min])) - Decimal(str(error))
    return liste_weight


def calculate_statistics(liste_price,liste_crypto,liste_weight):
    # Joindre les datasets des liste  sur les dates and add suffixe (liste_crypto[i].get("name"))
    
    merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("name")})
    for i in range(1, len(liste_price)):
        liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("name")})
        merged = pd.merge(merged, liste_price[i], on='date')
    
    # put merge prix to csv
    # merged.to_csv('listeprix.csv', index=False)
    
    # Calculer les rendements journaliers pour les crypto de la liste
    
    for i in range(len(liste_crypto)):
        merged[liste_crypto[i].get("name")] = np.log(merged['price_'+liste_crypto[i].get("name")] / merged['price_'+liste_crypto[i].get("name")].shift(1))
    
    # Supprimer les valeurs NaN
    merged.dropna(inplace=True)
    
    # Calcul de la volatilité historique
    liste_volatilite = []
    for i in range(len(liste_crypto)):
        vol = merged[liste_crypto[i].get("name")].std()
        liste_volatilite.append(vol)
    
    # Calcul de la covariance entre les cryptos de la liste
    covariance_matrix = merged[[f'{crypto.get("name")}' for crypto in liste_crypto]].cov()
    
    # Méthode matricielle (plus précise)
    weights = np.array([float(Decimal(w)) for w in liste_weight])
    portfolio_volatility_mat = np.sqrt(weights.T @ covariance_matrix.values @ weights)
    
    return liste_volatilite, portfolio_volatility_mat,covariance_matrix
    
def calculate_correlation_matrix(covariance_matrix):
    std_devs = np.sqrt(np.diag(covariance_matrix))
    correlation_matrix = covariance_matrix / np.outer(std_devs, std_devs)
    return correlation_matrix

list_crypto_page_1 = get_liste_crypto(page = 1)
list_crypto_page_2 = get_liste_crypto(page = 2)
list_crypto_page_3 = get_liste_crypto(page = 3)
list_crypto_page_4 = get_liste_crypto(page = 4)

list_crypto = list_crypto_page_1 + list_crypto_page_2 + list_crypto_page_3 + list_crypto_page_4
# print(len(list_crypto))
list_crypto = excludeStableCoin(list_crypto)
list_crypto = list_crypto[:10]
# print(len(list_crypto))
# put the liste in a csv format and only wurite id and symbol

# with open("crypto.csv","w") as f:
#     for crypto in list_crypto:
#         f.write(json.dumps({"id":crypto.get("id"),"prix":crypto.get("current_price")}) + "\n")

# # with open("crypto.json","w") as f:
# #     for crypto in list_crypto:
# #         f.write(json.dumps({"id":crypto.get("id"),"symbol":crypto.get("symbol"),"price": crypto.get("current_price")}) + "\n")

# # prendre que les 10 premier crypto pour le calcul
# list_crypto = list_crypto[:10]


liste_prix = []
liste_market_cap = []
for i in range(len(list_crypto)):
    crypto = list_crypto[i]
    
    # obtenir l'hitorique des prix des 10 crypto
    df = get_historical_prices(crypto = crypto.get("id"), days =90)
    
    liste_prix.append(df)
    
    # obtenir le market cap de chaque crypto
    df = get_market_cap(crypto = crypto.get("id"))
    liste_market_cap.append(df)
        
# put listemarketcap to csv as dataframe
# liste_crypto_names = [crypto["name"] for crypto in list_crypto]

# df = pd.DataFrame({'market_cap': liste_market_cap, 'crypto': liste_crypto_names})

# df = pd.DataFrame(liste_market_cap, columns=['market_cap'])

# df.to_csv('listemarketcap.csv', index=True)

# Normaliser les poids
# liste_weight = normalize_weights(liste_market_cap)
# liste_weight = round_weights(liste_weight)

# # Afficher les poids normalisés
# for i in range(len(liste_weight)):
#     print(f"Weight for {list_crypto[i].get('name')} : {liste_weight[i]}")

# # calculer la somme de listeweight
# # somme = math.fsum(map(float, liste_weight))
# somme = Decimal("0.0")
# for i in range(len(liste_weight)):
#     somme +=liste_weight[i]
# print(f"Somme des poids : {somme}")
    
# liste_volatilite, portfolio_volatility_mat,covariance_matrix = calculate_statistics(liste_prix,list_crypto,liste_weight)

# # # Calculer la matrice de corrélation
# correlation_matrix = calculate_correlation_matrix(covariance_matrix)

# # # Annualiser les volatilités (BTC, ETH et portefeuille)
# liste_volatilite_annuel = []

# for i in range(len(liste_volatilite)):
#     vol = liste_volatilite[i] * np.sqrt(365)
#     liste_volatilite_annuel.append(vol)

# portfolio_volatility_mat_annual = portfolio_volatility_mat * np.sqrt(365)

# # Afficher les résultats

# for i in range(len(liste_volatilite)):
#     print(f"Volatilité quotidienne de {list_crypto[i].get('name')} : {liste_volatilite[i]:.4f}")
#     print(f"Volatilité annuelle de {list_crypto[i].get('name')} : {liste_volatilite_annuel[i]:.4f}")
    
# print(f"Volatilité quotidienne du portefeuille (matricielle) : {portfolio_volatility_mat:.4f}")

# print(f"Volatilité annuelle du portefeuille (matricielle) : {portfolio_volatility_mat_annual:.4f}")

# print("\n=== Matrice de Covariance ===")
# print(covariance_matrix)

# put matrice de covariance into csv
# covariance_matrix.to_csv('covariance_matrix.csv', index=False)

# print("\n=== Matrice de Corrélation ===")
# print(correlation_matrix)


#  calucl des rendements
liste_rendements = []
somme_rendement = 0
# print(liste_prix[1]["price"])
for i in range(len(liste_prix)):
    rendement = (liste_prix[i]["price"][90]- liste_prix[i]["price"][88])/liste_prix[i]["price"][88]
    somme_rendement += rendement
    liste_rendements.append(rendement)
print(f"Rendement moyen : {somme_rendement/len(liste_prix)}")

