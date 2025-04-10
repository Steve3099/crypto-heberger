import asyncio
import aiofiles
import websockets
import json
from datetime import datetime

price_buffer = {}  # Holds the latest price for each symbol

async def save_all_prices():
    for pair, price in list(price_buffer.items()):
        await save_price(pair, price)

async def save_price(pair, price):
    filename = f"app/json/crypto/websocket_price/{pair}_price.json"
    data_entry = {
        "date": datetime.utcnow().isoformat(),
        "price": price
    }

    try:
        async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content) if content else []
    except FileNotFoundError:
        data = []

    data.append(data_entry)

    async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
        await f.write(json.dumps(data, indent=4))

async def get_symboles_liste_from_json():
    with open("app/json/binance/symbols.json", "r") as f:
        data = json.load(f)
    return data

async def track_prices():
    liste = await get_symboles_liste_from_json()
    PAIRS = [el["symbol"].lower() for el in liste]
    # PAIRS = ["btcusdt", "ethusdt", "solusdt"]
    stream_query = "/".join([f"{pair}@ticker" for pair in PAIRS])
    BINANCE_WS_URL = f"wss://stream.binance.com:9443/stream?streams={stream_query}"

    async def periodic_saver():
        while True:
            await asyncio.sleep(15)
            print("💾 Saving all prices...")
            await save_all_prices()

    while True:
        try:
            async with websockets.connect(
                BINANCE_WS_URL,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                print("✅ Connected to Binance WebSocket")
                asyncio.create_task(periodic_saver())  # Start saving every 15 seconds

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    
                    if "data" in message:
                        stream_data = message["data"]
                        symbol = stream_data["s"].lower()
                        price = price = round(float(stream_data["c"]), 12)
                        price_buffer[symbol] = price

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"⚠️ Connection closed: {e}, reconnecting in 5 seconds...")
            await asyncio.sleep(5)
