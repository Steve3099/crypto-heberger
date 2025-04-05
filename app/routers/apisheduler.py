from app.services.varService import VarService
from fastapi import APIRouter
from app.services.coinGeckoService import CoinGeckoService
from app.services.indexService import IndexService
from app.services.voaltiliteService import VolatiliteService
from app.services.cryptoService import CryptoService
from app.services.skeuness_kurtoService import Skewness_KurtoService
from app.services.callCoinMarketApi import CallCoinMarketApi

apisheduler = APIRouter()
indexService = IndexService()
coinGeckoService = CoinGeckoService()
volatileService = VolatiliteService()
varService = VarService()
cryptoService = CryptoService()
skewness_kurtoService = Skewness_KurtoService()
callCoinMArketApi = CallCoinMarketApi()

@apisheduler.get("/sheduler/listeprix")
async def set_liste_prix():
    await coinGeckoService.schedule_historique_prix()
    return {"message":"prix done"}

@apisheduler.get("/sheduler/marketcap")
async def set_market_cap():
    await coinGeckoService.schedule_market_cap()
    return {"message":"market cap done"}

@apisheduler.get("/sheduler/index")
async def set_index():
    await indexService.set_Index()
    return {"message":"index done"}

@apisheduler.get("/sheduler/listecryptowithweight")
async def set_liste_crypto_with_weight():
    await coinGeckoService.schedule_liste_crypto_with_weight_volatility()
    return {"message":"liste crypto with weight done"}

@apisheduler.get('/sheduler/volatilite')
async def set_volatilite():
    await volatileService.set_historique_volatilite()
    return {"message":"volatilite done"}

@apisheduler.get('/sheduler/listenofilter')
async def set_liste_sans_filtre():
    liste_crypto = await coinGeckoService.set_liste_no_folter_to_json()
    return len(liste_crypto)

@apisheduler.get('/sheduler/volatilitegenerale/update')
async def update_volatilite_generale():
    await volatileService.update_historique_volatilite_generale()
    return {"message":"volatilite generale done"}

@apisheduler.get('/sheduler/setvolatilite')
async def set_volatilite_crypto():
    await volatileService.set_historique_volatiltie_for_each_crypto_to_json()
    return {"message":"volatilite for each crypto done"}

@apisheduler.get('/sheduler/update_volatilite_crpto')
async def update_volatilite_for_ecah_crypto():
    await volatileService.update_historique_volatilite_for_each_crypto()
    return {"message":"volatilite update done"}

# @apisheduler.get('/sheduler/set_var')
# async def set_var():
#     await varService.set_Var_for_each_crypto()
#     return {"message":"var done"}

@apisheduler.get('/sheduler/action')
async def action():
    await set_fear_and_greed()
    await set_liste_prix()
    await set_market_cap()
    await update_volatilite_generale()
    await update_volatilite_for_ecah_crypto()
    # await set_liste_sans_filtre()
    await set_liste_crypto_with_weight()
    await set_var()
    await cryptoService.set_info_crypto()
    await set_historique_market_cap_generale()
    await set_historique_volume_generale()
    return {"message":"action done"}

@apisheduler.get('/sheduler/set_info_crypto')
async def set_info_crypto():
    await cryptoService.set_info_crypto()
    return {"message":"action done"}

@apisheduler.get('/sheduler/set_var')
async def set_var():
    return await varService.update_var_v2()
    # return {"message":"var done"}

@apisheduler.get('/sheduler/set_vollatilite_annuel')
async def set_vollatilite_annuel():
    return await volatileService.set_volatilite_annuel()
    # return {"message":"var done"}
    
@apisheduler.get('/sheduler/set_vollatilite_annuel_per_crypto')
async def set_vollatilite_annuel_per_crypto():
    return await volatileService.set_historique_volatilite_annuel_per_cryto()
    # return {"message":"var done"}
    
@apisheduler.get('/sheduler/set_historique_volatilite_for_one_crypto')
async def set_historique_volatilite_for_one_crypto(id):
    ids = [id]
    for id in ids:
        await volatileService.set_historique_volatilite_for_one_crypto(id)
    # return await volatileService.set_historique_volatilite_for_one_crypto(id)
    # return {"message":"var done"}

@apisheduler.get('/sheduler/set_historique_prix_for_one_crypto')
async def set_historique_prix_for_one_crypto(id):
    ids = [id]
    for id in ids:
        await coinGeckoService.set_historical_price_to_json(id)
    # return await coinGeckoService.set_historical_price_to_json(id)
    # return {"message":"var done"}
    
@apisheduler.get('/sheduler/set_historique_market_cap_for_one_crypto')
async def set_historique_market_cap_generale():
    return await cryptoService.set_historique_market_cap_generale()

@apisheduler.get('/sheduler/set_skewness_kurto')
async def set_skewness_kurto():
    return await skewness_kurtoService.set_skewness_kurto()
    # return {"message":"var done"}
    
@apisheduler.get('/sheduler/get_list_cryptos')
async def get_list_cryptos():
    await cryptoService.set_info_crypto()
    return "done"
    # print(len(await coinGeckoService.set_liste_no_folter_to_json()))
    # return await callCoinMArketApi.get_liste_cypto_ufiltered()
async def set_fear_and_greed():
    await callCoinMArketApi.getFearAndGreed()
    return "fear and greed done"

@apisheduler.get('/sheduler/set_historique_var_crypto')
async def set_historique_var_crypto(id):
    return await varService.set_historique_var_crypto(id)
    # return {"message":"var done"}
    
# set_historique_volume_generale
@apisheduler.get('/sheduler/set_historique_volume_generale')
async def set_historique_volume_generale():
    return await cryptoService.set_historique_volume_generale()
    # return {"message":"var done"}

#set stabel and wrapped coin
@apisheduler.get('/sheduler/set_stable_and_wrapped_coin')
async def set_stable_and_wrapped_coin():
    await callCoinMArketApi.set_liste_stabke_wrapped_tokens()
    return {"message":"stable and wrapped coins done"}

# set volume generale historique
@apisheduler.get('/sheduler/set_volume_generale_historique')
async def set_volume_generale_historique():
    await cryptoService.set_historique_volume_generale()
    return {"message":"volume generale done"}

#set_global_data_to_json
@apisheduler.get('/sheduler/set_global_data_to_json')
async def set_global_data_to_json():
    await coinGeckoService.set_global_data_to_json()
    return {"message":"global data done"}