from apscheduler.schedulers.background import BackgroundScheduler
from app.services.indexService import IndexService
from app.services.coinGeckoService import CoinGeckoService
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

indexService = IndexService()
coinGeckoService = CoinGeckoService()
# Create scheduler
# scheduler = BackgroundScheduler()

def my_cron_task():
    print(f"Running cron task at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Schedule the cron job
scheduler.add_job(indexService.set_Index, "interval", minutes=5)
scheduler.add_job(coinGeckoService.schedule_historique_prix, "cron", hour=20, minute=5)
# scheduler.add_job(coinGeckoService.schedule_market_cap, "cron", hour=14, minute=33)

# Start the scheduler
scheduler.start()
