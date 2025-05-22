import numpy as np
import scipy.stats as stats

# Données des rendements (à remplacer nos valeurs market returns = Indice et portfolio retunrs = rendements crypto)
market_returns = [
    "0.1%", "0.8%", "0.1%", "(2.7%)", "(0.0%)", "(1.6%)", "(0.3%)", "(2.0%)", "0.6%", "3.0%", "4.1%", "(2.2%)", "1.0%", "(0.4%)"
    ]

portfolio_returns = [
    "(0.0%)", "0.8%", "0.2%", "0.1%", "1.0%", "0.3%", "0.5%", "(0.5%)", "0.6%", "1.5%", "0.7%", "(0.1%)", "(0.1%)", "0.1%"
    ]

# Fonction pour convertir les rendements en nombres 
def parse_returns(returns):
    parsed = []
    for val in returns:
        val = val.replace("%", "").replace("(", "-").replace(")", "")  
        try:
            parsed.append(float(val) / 100)  
        except ValueError:
            print(f"Erreur de conversion : {val}")
    return np.array(parsed)


market = parse_returns(market_returns)
portfolio = parse_returns(portfolio_returns)

# Aligner les séries 
min_len = min(len(market), len(portfolio))
market = market[:min_len]
portfolio = portfolio[:min_len]

# Régression linéaire
slope, intercept, r_value, _, _ = stats.linregress(market, portfolio)

# Résultats
print(f"Bêta du portefeuille : {slope:.4f}")
print(f"Alpha du portefeuille : {intercept:.4f}")
print(f"R² : {r_value**2:.4f}")
