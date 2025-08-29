from flask import Blueprint, jsonify
from Services.signalService import SignalService

class SignalAPI:
    def __init__(self):
        self.blueprint = Blueprint('signal_api', __name__)
        self.service = SignalService()
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule("/zones", view_func=self.get_zones, methods=["GET"])
        self.blueprint.add_url_rule("/signals", view_func=self.get_signals, methods=["GET"])

    def get_zones(self):
        zones = self.service.get_untouched_zones()
        if zones is None:
            return jsonify({"error": "No zones found"}), 500
        return jsonify({"data":zones}),200

    def get_signals(self):
        try:
            signals = self.service.get_current_signals()
            return jsonify({"data" :signals}),200
        except:
            return jsonify({"error": "Unknown Error Occur"},500)
        
