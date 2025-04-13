import asyncio
import aiofiles
import websockets
import json
import os
from datetime import datetime
from fastapi import HTTPException

price_buffer = {}  # Holds the latest price for each symbol
price_file_lock = asyncio.Lock()

async def save_all_prices():
    """Save all prices in the buffer to their respective files."""
    tasks = [save_price(pair, price) for pair, price in list(price_buffer.items())]
    await asyncio.gather(*tasks)

async def save_price(pair, price):
    """Save a single price entry for a symbol to its JSON file."""
    async with price_file_lock:
        filename = f"app/json/crypto/websocket_price/{pair}_price.json"
        data_entry = {
            "date": datetime.utcnow().isoformat(),
            "price": price
        }
        try:
            async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content) if content.strip() else []
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
            async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
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