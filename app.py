from flask import Flask
from API.signal_api import SignalAPI
from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis,json,threading,os

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
service = SignalService()
signal_api = SignalAPI(service=service,limiter=limiter)
app.register_blueprint(signal_api.blueprint, url_prefix="/api")

if __name__ == "__main__":
    socketio.run(app,host = "0.0.0.0",port = 5000)
