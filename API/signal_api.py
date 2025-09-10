from flask import Blueprint, jsonify, request
from Services.signalService import SignalService
from Exceptions.ServiceExceptions import *

class SignalAPI:
    def __init__(self,service : SignalService):
        self.blueprint = Blueprint('signal_api', __name__)
        self.service = service
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule("/zones", view_func=self.get_zones, methods=["GET"])
        self.blueprint.add_url_rule("/signals", view_func=self.get_running_signals, methods=["GET"])
        self.blueprint.add_url_rule("/signal_with_input", view_func=self.get_signals_with_input, methods=["POST"])

    def get_zones(self):
        try:
            zones = self.service.get_untouched_zones()
            return jsonify({"data":zones}),200
        except NoUntouchedZone as e:
            return jsonify({"error" : f'{e}'},404)
        except Exception as e:
            return jsonify({"error" : "Something went wrong"},500)

    def get_running_signals(self):
        try:
            signals = self.service.get_running_signals()
            return jsonify({"data" :signals}),200
        except EmptySignalException as e:
            return jsonify({"error" : f'{e}'},404)
        except:
            return jsonify({"error": "Unknown Error Occur"},500)
        
    def get_signals_with_input(self):
        try:
            data = request.get_json()
            signals = self.service.get_signals_with_input(data)
            return jsonify({"data" :signals}),200
        except Exception as e:
            return jsonify({"error": str(e)}),500
        
