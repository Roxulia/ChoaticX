from flask import Flask
from API.signal_api import SignalAPI
from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
socketio = SocketIO(app,cors_allowed_origins="*")
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per minute"]  # global limit
)
service = SignalService(socketio=socketio)
signal_api = SignalAPI(service=service,limiter=limiter)
scheduler = SchedulerManager(service=service)
scheduler.start()

app.register_blueprint(signal_api.blueprint, url_prefix="/api")

if __name__ == "__main__":
    socketio.run(app,debug=True)