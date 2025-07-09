from flask import Blueprint, jsonify
from main import SignalService

signal_api = Blueprint('signal_api', __name__)
service = SignalService()

@signal_api.route("/zones", methods=["GET"])
def get_zones():
    zones = service.get_latest_zones()
    return jsonify(zones)

@signal_api.route("/signals", methods=["GET"])
def get_signals():
    signals = service.get_current_signals()
    return jsonify(signals)
