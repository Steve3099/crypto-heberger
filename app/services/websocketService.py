import asyncio
import aiofiles
import websockets
import json
import os
from datetime import datetime, timedelta
from fastapi import HTTPException

price_buffer = {}  # Holds the latest price for each symbol
price_file_lock = asyncio.Lock()
crypto_info_lock = asyncio.Lock()

async def save_all_prices():
    """Save all prices in the buffer to their respective files."""
    tasks = [save_price(pair, price) for pair, price in list(price_buffer.items())]
    await asyncio.gather(*tasks)

async def save_price(pair, price):
    """Save a single price entry for a symbol to its JSON file."""
    async with price_file_lock:
        filename = f"app/json/crypto/websocket_price/{pair}_price.json"
        now = datetime.utcnow()
        data_entry = {
            "date": now.isoformat(),
            "price": price
        }
        try:
            async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content) if content.strip() else []
                
            # update price of crypto in liste no filter 
            # remove usdt from pair
            # symbole = crypto.get("symbol", "").lower()
            if pair.endswith("usdt"):
                pair = pair[:-4]
            
            # get liste no filter
            async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'r', encoding='utf-8') as f:
                liste = json.loads(await f.read())
            
            # find the crypto in liste
            for el in liste:
                if el.get("symbol", "").lower() == pair:
                    # update the price
                    el["current_price"] = price
                    
                    # calcul variation percentage 24 hours
                    # get the price 24 hours ago from data
                    dt_24h_ago = now - timedelta(hours=20)
                    # print(dt_24h_ago)
                    # Allow a 1-minute margin when comparing dates
                    margin = timedelta(minutes=5)
                    price_24h = None

                    for item in data:
                        try:
                            item_date = datetime.fromisoformat(item.get("date"))
                        except Exception:
                            
                            continue
                        if abs((item_date - dt_24h_ago).total_seconds()) <= margin.total_seconds():
                            price_24h = item.get("price")
                            break

                    if price_24h:
                        variation = ((price  / price_24h) -1) * 100
                        # print(f"Price 24h ago: {price_24h}, Current price: {price}, Variation: {variation}")
                        el["price_change_percentage_24h"] = round(variation, 4)
                    # else:
                    #     el["price_change_percentage_24h"] = None
                    
                    break
            # save the updated liste
            async with aiofiles.open('app/json/crypto/info/crypto_binance.json', 'w', encoding='utf-8') as f:
                await f.write(json.dumps(liste, indent=4, ensure_ascii=False))
            
        except FileNotFoundError:
            data = []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {filename}: {e}")
            data = []
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return

        data.append(data_entry)

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            temp_filename = filename + ".tmp"
            async with aiofiles.open(temp_filename, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
            os.replace(temp_filename, filename)
        except Exception as e:
            print(f"Error writing to {filename}: {e}")

async def get_symbols_liste_from_json():
    """Retrieve the list of symbols from a JSON file."""
    filename = "app/json/binance/symbols.json"
    try:
        async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content.strip() else []
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Symbols file {filename} not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {filename}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {filename}: {str(e)}")

async def track_prices():
    """Track cryptocurrency prices via Binance WebSocket."""
    try:
        liste = await get_symbols_liste_from_json()
        PAIRS = [el["symbol"].lower() for el in liste]
    except HTTPException as e:
        print(f"Failed to load symbols: {e.detail}")
        return

    if not PAIRS:
        print("No symbols to track")
        return

    stream_query = "/".join([f"{pair}@ticker" for pair in PAIRS])
    BINANCE_WS_URL = f"wss://stream.binance.com:9443/stream?streams={stream_query}"

    async def periodic_saver():
        while True:
            await asyncio.sleep(15)
            print("💾 Saving all prices...")
            await save_all_prices()

    # Start periodic saver once
    saver_task = asyncio.create_task(periodic_saver())

    while True:
        try:
            async with websockets.connect(
                BINANCE_WS_URL,
                ping_interval=20,
                ping_timeout=10,
                max_size=2**20  # Limit message size to 1MB
            ) as websocket:
                print("✅ Connected to Binance WebSocket")
                
                while True:
                    try:
                        response = await websocket.recv()
                        message = json.loads(response)
                        
                        if "data" in message:
                            stream_data = message["data"]
                            symbol = stream_data["s"].lower()
                            if symbol in PAIRS:  # Only process tracked symbols
                                price = round(float(stream_data["c"]), 12)
                                price_buffer[symbol] = price
                    except json.JSONDecodeError as e:
                        print(f"Error parsing WebSocket message: {e}")
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        raise  # Reconnect on connection close
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        continue

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"⚠️ Connection closed: {e}, reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}, reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            # Clean up price_buffer for stale symbols
            stale_symbols = [symbol for symbol in price_buffer if symbol not in PAIRS]
            for symbol in stale_symbols:
                price_buffer.pop(symbol, None)

    # Cancel saver task on exit (unreachable in this loop, but included for completeness)
    saver_task.cancel()