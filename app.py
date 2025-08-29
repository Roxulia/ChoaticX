from flask import Flask
from API.signal_api import SignalAPI
from Scheduler.scheduler import SchedulerManager

app = Flask(__name__)

signal_api = SignalAPI()
app.register_blueprint(signal_api.blueprint, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True)