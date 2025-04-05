from apscheduler.schedulers.background import BackgroundScheduler
from app.services.indexService import IndexService
from app.services.coinGeckoService import CoinGeckoService
from app.services.voaltiliteService import VolatiliteService
# from app.services.
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routers.apisheduler import action


scheduler = AsyncIOScheduler()


indexService = IndexService()
coinGeckoService = CoinGeckoService()
volatiliteService = VolatiliteService()
# Create scheduler
# scheduler = BackgroundScheduler()

def my_cron_task():
    print(f"Running cron task at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Schedule the cron job
scheduler.add_job(indexService.set_Index, "interval", minutes=10, coalesce=True, misfire_grace_time=300, kwargs={}, id="index_update", replace_existing=True)
scheduler.add_job(coinGeckoService.set_global_data_to_json, "interval", minutes=10, coalesce=True, misfire_grace_time=300, kwargs={}, id="index_update", replace_existing=True)

# scheduler.add_job(volatiliteService.update_historique_volatilite_generale, "cron", hour=0, minute=5)
# scheduler.add_job(coinGeckoService.schedule_historique_prix, "cron", hour=0, minute=5)
# scheduler.add_job(coinGeckoService.schedule_market_cap, "cron", hour=1, minute=5)
# scheduler.add_job(coinGeckoService.schedule_liste_crypto_with_weight_volatility,"cron",hour=2,minute=5)
scheduler.add_job(action, "cron", hour=1, minute=0)

# Start the scheduler
scheduler.start()
