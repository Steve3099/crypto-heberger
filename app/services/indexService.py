import asyncio
from fastapi import HTTPException
import pandas as pd
import aiofiles
import json
import os
import io
from datetime import datetime
from app.services.coinGeckoService import CoinGeckoService

coingeckoservice = CoinGeckoService()

class IndexService:
    def calculate_index(self, crypto_list, base_market_cap):
        """Calculate the crypto index value and total market cap."""
        market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in crypto_list)
        index_value = (market_cap / base_market_cap) * 100
        return round(index_value, 4), market_cap

    async def set_Index(self):
        """Update the crypto index and save results to JSON and CSV."""
        print("Démarrage de l'indice crypto...")
        base_market_cap = None

        # Read base_market_cap from JSON file
        try:
            async with aiofiles.open('app/json/index/base_market_cap.json', 'r', encoding='utf-8') as f:
                value = await f.read()
                if value.strip():
                    base_market_cap = float(value)
        except (FileNotFoundError, ValueError):
            pass  # base_market_cap remains None if file is missing or invalid

        try:
            data = await coingeckoservice.get_liste_crypto_filtered()
            filtered_data = [
                coin for coin in data
                if coin["current_price"] is not None and
                   (coin["total_volume"] is None or coin["total_volume"] >= 2000000)
            ]
            filtered_data = filtered_data[:80]

            # Ensure directory exists and write filtered data to JSON
            os.makedirs('app/json/liste_crypto', exist_ok=True)
            async with aiofiles.open('app/json/liste_crypto/liste_crypto.json', 'w', encoding='utf-8') as f:
                await f.write(json.dumps(filtered_data, indent=4, ensure_ascii=False))

            if base_market_cap is None:
                base_market_cap = sum(coin["current_price"] * coin["circulating_supply"] for coin in filtered_data)
                os.makedirs('app/json/index', exist_ok=True)
                async with aiofiles.open('app/json/index/base_market_cap.json', 'w', encoding='utf-8') as f:
                    await f.write(f"{base_market_cap:.4f}")

            index_value, total_market_cap = self.calculate_index(filtered_data, base_market_cap)
            print(f"Indice mis à jour: {index_value:.4f}")

            # Append index value to JSON file
            file_path = 'app/json/index/index.json'
            os.makedirs('app/json/index', exist_ok=True)
            data = []
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():
                        data = json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            val = {"date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": index_value}
            data.append(val)

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))

            # Create DataFrame for CSV
            df = pd.DataFrame([
                {
                    "Nom": coin["name"],
                    "Prix (USD)": f"{coin['current_price']:.2f}",
                    "Circulating Supply": f"{coin['circulating_supply']:,}",
                    "Volume (USD)": f"{coin['total_volume']:.2f}",
                    "Poids (%)": f"{(coin['current_price'] * coin['circulating_supply'] / total_market_cap * 100):.2f}"
                }
                for coin in filtered_data
            ])

            # Write DataFrame to CSV asynchronously
            os.makedirs('app/index', exist_ok=True)
            csv_path = 'app/index/index.csv'
            async with aiofiles.open(csv_path, 'w', encoding='utf-8') as f:
                await f.write(df.to_csv(index=False))

        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'indice: {e}")
            raise

    async def get_csv_index(self):
        """Read the index CSV file asynchronously."""
        try:
            async with aiofiles.open('app/index/index.csv', 'r', encoding='utf-8') as f:
                content = await f.read()
            return pd.read_csv(io.StringIO(content))
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Index CSV file not found")
        except pd.errors.ParserError as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")

    async def get_graphe_indices(self):
        """Generate graph data by grouping small weights into 'Autres'."""
        liste_indice = await self.get_csv_index()
        graphe = []
        value_other = 0

        for i in range(len(liste_indice)):
            poids = float(liste_indice["Poids (%)"][i])
            if poids >= 0.1:
                graphe.append({"Nom": liste_indice["Nom"][i], "Poids (%)": poids})
            else:
                value_other += poids

        graphe.append({"Nom": "Autres", "Poids (%)": value_other})
        return graphe

    async def get_liste_index_from_json_file(self, date_start=None, date_end=None):
        """Retrieve index values from JSON file within a date range."""
        if date_start is None:
            date_start = "2025-02-18 09:19:33"
        if date_end is None:
            date_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            async with aiofiles.open('app/json/index/index.json', 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            return [el for el in data if el["date"] >= date_start and el["date"] <= date_end]
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse index JSON: {e}")
        
    async def generate_index_between_dates(self, date_start=None, date_end=None):
        """Generate index values between two dates."""
        liste_indice = await self.get_liste_index_from_json_file(date_start, date_end)
        # if not liste_indice:
        #     raise HTTPException(status_code=404, detail="No index data found for the specified date range")

        # calcule days between dates
        date_format = "%Y-%m-%d %H:%M:%S"
        start_date = datetime.strptime(date_start, date_format)
        end_date = datetime.strptime(date_end, date_format)
        today = datetime.now()
        #diferences between today and date_start
        dif = (today - start_date).days
        delta = (end_date - start_date).days
        if delta < 0:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        data = await coingeckoservice.get_liste_crypto_filtered()
        filtered_data = [
            coin for coin in data
            if coin["current_price"] is not None and
                (coin["total_volume"] is None or coin["total_volume"] >= 2000000)
        ]
        filtered_data = filtered_data[:80]
        liste_data = []
        i = 0
        for coin in filtered_data:
            data = await coingeckoservice.get_prix_one_crypto_2(coin["id"],vs_currency="usd", days=dif+1)
            
            liste_data.append(data)
            if i%20 == 0 and i!= 0:
                await asyncio.sleep(60)
            i+=1
        
        liste_market_cap_total = await self.get_market_cap_total(filtered_data, liste_data)
        
        async with aiofiles.open('app/json/index/base_market_cap.json', 'r', encoding='utf-8') as f:
            value = await f.read()
            if value.strip():
                base_market_cap = float(value)
        
        liste_index = []
        for i in range(len(liste_market_cap_total)):
            index = (liste_market_cap_total[i] / base_market_cap) * 100
            val = {
                "date": datetime.fromtimestamp(liste_data[0]["prices"][i][0] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                "value": index
            }
            # verif that date is not over date_end
            if val["date"] > date_end:
                break
            if val["date"] < date_start:
                continue
            liste_index.append(val)
            liste_indice.append(val)
        
        #order the list by date
        liste_indice = sorted(liste_indice, key=lambda x: x["date"])
        # Save the updated index data to JSON file
        file_path = 'app/json/index/index.json'
        os.makedirs('app/json/index', exist_ok=True)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(liste_indice, indent=4, ensure_ascii=False))
        
        return liste_index
    async def get_market_cap_total(self, liste_crypto, data):
        market_cap_liste_total = []
        # calucl each market cap total for each timestamp
        for i in range(len(data[0]["prices"])):
            market_cap_total = 0
            for j in range(len(liste_crypto)):
                try:
                    market_cap_total += data[j]["market_caps"][i][1]
                except:
                    continue
                # market_cap_total += data[j]["market_caps"][i][1]
            market_cap_liste_total.append(market_cap_total)
        return market_cap_liste_total
            