from flask import Flask
from API.signal_api import SignalAPI
from API.prediction_api import PredictionAPI
from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis,json,threading,os
from Database.DB import MySQLDB as DB
from Database.Cache import Cache


DB.init_logger('api_db.log')
Cache.init()
app = Flask(__name__)
socketio = SocketIO(app,cors_allowed_origins="*")
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per minute"]  # global limit
)
r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()
pubsub.subscribe("signals_channel")

def listen_signals():
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            socketio.emit("new_signal", data, broadcast=True)
#threading.Thread(target=listen_signals, daemon=True).start()
btcservice = SignalService(symbol="BTCUSDT",threshold=500)
btc_api = SignalAPI(service=btcservice,limiter=limiter)
bnbservice = SignalService(symbol="BNBUSDT",threshold=5)
bnb_api = SignalAPI(service=bnbservice,limiter=limiter)
paxgservice = SignalService(symbol="PAXGUSDT",threshold=10)
paxg_api = SignalAPI(service=paxgservice,limiter=limiter)
ethservice = SignalService(symbol="ETHUSDT",threshold=10)
eth_api = SignalAPI(service=ethservice,limiter=limiter)
solservice = SignalService(symbol="SOLUSDT",threshold=10)
sol_api = SignalAPI(service=solservice,limiter=limiter)
predict_api = PredictionAPI(limiter=limiter)
app.register_blueprint(btc_api.blueprint, url_prefix="/api/btc")
app.register_blueprint(bnb_api.blueprint, url_prefix="/api/bnb")
app.register_blueprint(paxg_api.blueprint, url_prefix="/api/paxg")
app.register_blueprint(eth_api.blueprint, url_prefix="/api/eth")
app.register_blueprint(sol_api.blueprint, url_prefix="/api/sol")
app.register_blueprint(predict_api.blueprint,url_prefix='/api')

if __name__ == "__main__":
    
    socketio.run(app,host = "0.0.0.0",port = 5000)
