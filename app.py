from flask import Flask
from API.signal_api import SignalAPI
from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app,cors_allowed_origins="*")
service = SignalService(socketio=socketio)
signal_api = SignalAPI(service=service)
scheduler = SchedulerManager(service=service)
scheduler.start()

app.register_blueprint(signal_api.blueprint, url_prefix="/api")

if __name__ == "__main__":
    socketio.run(app,debug=True)