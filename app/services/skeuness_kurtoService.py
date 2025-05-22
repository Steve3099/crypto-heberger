import numpy as np
import json
import pandas as pd
from scipy.stats import skew, kurtosis
from app.services.coinGeckoService import CoinGeckoService
import aiofiles
import os
from fastapi import HTTPException

coinGeckoService = CoinGeckoService()

class Skewness_KurtoService:
    def __init__(self):
        pass

    async def calculate_skewness_kurtosis(self, prices_list, crypto_names):
        """Calculate skewness and kurtosis for multiple cryptocurrencies."""
        for i, prices in enumerate(prices_list):
            crypto_name = crypto_names[i].get("id")
            # Calculate log returns
            prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
            prices.dropna(inplace=True)

            # Check for sufficient data
            if len(prices['log_return']) > 1:
                skew_value = skew(prices['log_return'])
                kurt_value = kurtosis(prices['log_return'], fisher=True)
                temp = {'skewness': skew_value, 'kurtosis': kurt_value}

                # Save to JSON
                os.makedirs('app/json/crypto/skewness_kurtosis', exist_ok=True)
                async with aiofiles.open(
                    f'app/json/crypto/skewness_kurtosis/{crypto_name}_skewness_kurtosis.json',
                    'w',
                    encoding='utf-8'
                ) as f:
                    await f.write(json.dumps(temp, indent=4, ensure_ascii=False))

    async def check_skewness_kurtosis(self, crypto_id):
        """Check if skewness and kurtosis data exists for a crypto."""
        try:
            async with aiofiles.open(
                f'app/json/crypto/skewness_kurtosis/{crypto_id}_skewness_kurtosis.json',
                'r',
                encoding='utf-8'
            ) as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            return None

    async def calculate_skewness_kurtosis_one_crypto(self, prices, crypto_name):
        """Calculate skewness and kurtosis for a single cryptocurrency."""
        prices['log_return'] = np.log(prices['price'] / prices['price'].shift(1))
        prices.dropna(inplace=True)

        if len(prices['log_return']) > 1:
            skew_value = skew(prices['log_return'])
            kurt_value = kurtosis(prices['log_return'], fisher=True)
            temp = {'skewness': skew_value, 'kurtosis': kurt_value}

            # Save to JSON
            os.makedirs('app/json/crypto/skewness_kurtosis', exist_ok=True)
            async with aiofiles.open(
                f'app/json/crypto/skewness_kurtosis/{crypto_name}_skewness_kurtosis.json',
                'w',
                encoding='utf-8'
            ) as f:
                await f.write(json.dumps(temp, indent=4, ensure_ascii=False))
            
            return temp
        else:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {crypto_name}")

    async def set_skewness_kurto(self):
        """Calculate and store skewness and kurtosis for filtered cryptocurrencies."""
        liste_crypto = await coinGeckoService.get_liste_crypto_filtered()
        
        liste_prix = []
        liste_crypto_used = []
        for crypto in liste_crypto:
            df = await coinGeckoService.get_historical_prices(crypto=crypto.get("id"), days=90)
            if len(df) > 90:
                liste_prix.append(df)
                liste_crypto_used.append(crypto)

        await self.calculate_skewness_kurtosis(liste_prix, liste_crypto_used)
        return "skewness and kurtosis done"

    async def get_skewness_kurtosis(self, id):
        """Retrieve or calculate skewness and kurtosis for a cryptocurrency."""
        try:
            async with aiofiles.open(
                f'app/json/crypto/skewness_kurtosis/{id}_skewness_kurtosis.json',
                'r',
                encoding='utf-8'
            ) as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            df = await coinGeckoService.get_historical_prices(crypto=id, days=90)
            if df.empty:
                raise HTTPException(status_code=404, detail=f"No price data for crypto {id}")
            return await self.calculate_skewness_kurtosis_one_crypto(df, id)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON data: {str(e)}")