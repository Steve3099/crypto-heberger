from decimal import Decimal
import json
import math
import pandas as pd
import numpy as np
from app.services.callApiService import getHistorique

class CalculService:
    async def calculRendements(self, prixF, prixAf):
        """Calculate logarithmic returns asynchronously."""
        return math.log(prixF / prixAf)

    async def calculVolatilliteJournaliere(self, listePrix):
        """Calculate daily volatility from a list of prices asynchronously."""
        # Convert listePrix to DataFrame
        listePrix = pd.DataFrame(listePrix, columns=['date', 'price'])

        # Calculate log returns
        listePrix['log_return'] = np.log(listePrix['price'] / listePrix['price'].shift(1))

        # Drop NaN values
        listePrix.dropna(inplace=True)

        # Calculate historical volatility
        volatilite = listePrix['log_return'].std()

        return volatilite

    async def getListeVolatilite(self, listePrix):
        """Calculate a list of volatilities by progressively reducing the price list."""
        listeVolatilite = []
        for i in range(len(listePrix) - 2):
            price = listePrix[:-i] if i > 0 else listePrix
            volatilite = await self.calculVolatilliteJournaliere(price)
            listeVolatilite.append(volatilite)
        return listeVolatilite

    async def top10volatiliteJournaliere(self, listeCrypto):
        """Calculate daily and annual volatility for the top 10 cryptocurrencies."""
        listeVolatilite = []
        for i, el in enumerate(listeCrypto[:10]):
            try:
                # Fetch historical prices asynchronously
                historique = await getHistorique(coin=el.get("id", ""))
                historique_data = json.loads(historique)
                prices = [price[1] for price in historique_data.get("prices", [])]
                volatilite = await self.calculVolatilliteJournaliere(pd.DataFrame({
                    'date': [price[0] for price in historique_data.get("prices", [])],
                    'price': prices
                }))
                retour = {
                    "coin": el,
                    "volatiliteJournaliere": volatilite,
                    "volatiliteAnnuel": volatilite * math.sqrt(365)
                }
                listeVolatilite.append(retour)
            except Exception as e:
                print(f"Error calculating volatility for {el.get('id')}: {e}")
                continue

        # Sort by daily volatility in descending order
        listeVolatilite.sort(key=lambda x: x.get("volatiliteJournaliere", 0), reverse=True)
        return listeVolatilite

    async def top5CroissanceDecroissance(self, listeCrypto):
        """Return top 5 growing and declining cryptos based on 24h price change."""
        listeCrypto = listeCrypto.copy()  # Avoid modifying the input list
        listeCrypto.sort(key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)
        return {
            "top5Croissance": listeCrypto[:5],
            "top5Decroissance": listeCrypto[-5:]
        }

    async def getListePrix(self, listeCrypto=[]):
        """Fetch historical prices for up to 10 cryptocurrencies."""
        listeRetour = []
        for i, el in enumerate(listeCrypto[:10]):
            try:
                historique = await getHistorique(days=90, coin=el.get("id", ""))
                historique_data = json.loads(historique)
                prices = [price[1] for price in historique_data.get("prices", [])]
                listeRetour.append(prices)
            except Exception as e:
                print(f"Error fetching prices for {el.get('id')}: {e}")
                continue
        return listeRetour

    async def getvolatilitePortefeuil(self, listeCrypto, listePrix):
        """Calculate portfolio volatility and covariance matrix."""
        sommeTotale = Decimal('0')
        rows = len(listeCrypto)
        cols = len(listeCrypto)
        matrice = [[Decimal('0') for _ in range(cols)] for _ in range(rows)]

        for i in range(len(listePrix)):
            volatiliteI = await self.getListeVolatilite(listePrix[i])
            wheightI = Decimal(str(listeCrypto[i].get("weight", 0)))
            for j in range(len(listePrix)):
                volatiliteJ = volatiliteI if i == j else await self.getListeVolatilite(listePrix[j])
                wheightJ = Decimal(str(listeCrypto[j].get("weight", 0)))
                produit = sum(volatiliteI[k] * volatiliteJ[k] for k in range(len(volatiliteJ)))
                covariance = Decimal(str(produit / len(volatiliteJ)))
                matrice[i][j] = covariance
                matrice[j][i] = covariance
                sommeTotale += covariance * wheightI * wheightJ

        volatilitePortefeuil = math.sqrt(float(sommeTotale))
        return volatilitePortefeuil, matrice

    async def getHistoriqueVolatiliteGenerale(self, nombrejour, listeCrypto, listePrix):
        """Calculate historical portfolio volatility over a number of days."""
        listVolatilitePortefeuille = []
        for _ in range(nombrejour - 2):
            if len(listePrix[0]) >= 3:
                res, matrice = await self.getvolatilitePortefeuil(listeCrypto, listePrix)
                listVolatilitePortefeuille.append(res)
                listePrix = await self.removeFirstLine(listePrix)
            else:
                break
        return listVolatilitePortefeuille

    async def removeFirstLine(self, listePrix):
        """Remove the first price entry from each price list."""
        return [el[1:] for el in listePrix]

    async def normalize_weights(self, liste_crypto_market_cap):
        """Normalize market cap weights to sum to 1."""
        total_market_cap = sum(liste_crypto_market_cap)
        if total_market_cap == 0:
            return [0] * len(liste_crypto_market_cap)
        return [market_cap / total_market_cap for market_cap in liste_crypto_market_cap]

    async def round_weights(self, liste_weight):
        """Round weights and adjust to ensure they sum to 1."""
        somme_weight = Decimal('0')
        rounded_weights = []
        for weight in liste_weight:
            rounded = Decimal(str(round(weight, 4)))
            rounded_weights.append(rounded)
            somme_weight += rounded

        if somme_weight != 1:
            error = Decimal('1.0') - somme_weight
            min_weight = min(rounded_weights)
            index_min = rounded_weights.index(min_weight)
            rounded_weights[index_min] += error

        return rounded_weights

    async def calculate_statistics(self, liste_price, liste_crypto, liste_weight):
        """Calculate volatility, portfolio volatility, and covariance matrix."""
        merged = liste_price[0].rename(columns={'price': 'price_' + liste_crypto[0].get("id")})
        for i in range(1, len(liste_price)):
            liste_price[i]['date'] = pd.to_datetime(liste_price[i]['date'])
            merged['date'] = pd.to_datetime(merged['date'])
            liste_price[i] = liste_price[i].rename(columns={'price': 'price_' + liste_crypto[i].get("id")})
            merged = pd.merge(merged, liste_price[i], on='date')

        new_columns = {}
        for crypto in liste_crypto:
            crypto_id = crypto.get("id")
            new_columns[crypto_id] = np.log(
                merged[f'price_{crypto_id}'] / merged[f'price_{crypto_id}'].shift(1)
            )

        merged = pd.concat([merged, pd.DataFrame(new_columns)], axis=1).copy()
        merged.dropna(inplace=True)
        merged.fillna(0, inplace=True)

        liste_volatilite = [merged[crypto.get("id")].std() for crypto in liste_crypto]
        covariance_matrix = merged[[crypto.get("id") for crypto in liste_crypto]].cov()
        weights = np.array([float(w) for w in liste_weight])
        portfolio_volatility_mat = np.sqrt(weights.T @ covariance_matrix.values @ weights)

        return liste_volatilite, portfolio_volatility_mat, covariance_matrix

    async def calculate_correlation_matrix(self, covariance_matrix):
        """Calculate correlation matrix from covariance matrix."""
        std_devs = np.sqrt(np.diag(covariance_matrix))
        correlation_matrix = covariance_matrix / np.outer(std_devs, std_devs)
        return correlation_matrix