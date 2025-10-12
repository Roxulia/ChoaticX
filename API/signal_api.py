from flask import Blueprint, jsonify, request
from Services.signalService import SignalService
from Exceptions.ServiceExceptions import *
from flask_limiter import Limiter

class SignalAPI:
    def __init__(self,service : SignalService,limiter: Limiter):
        self.blueprint = Blueprint('signal_api', __name__)
        self.service = service
        self.limiter = limiter
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule("/zones", view_func=self.limiter.limit("10 per minute")(self.get_zones), methods=["GET"])
        self.blueprint.add_url_rule("/signals", view_func=self.limiter.limit("5 per minute")(self.get_running_signals), methods=["GET"])
        
    def get_zones(self):
        try:
            zones = self.service.get_untouched_zones()
            return jsonify({"data":zones}),200
        except NoUntouchedZone as e:
            return jsonify({"error" : f'{e}'}),404
        except Exception as e:
            return jsonify({"error" : "Something went wrong"}),500

    def get_running_signals(self):
        try:
            signals = self.service.get_running_signals()
            return jsonify({"data" :signals}),200
        except EmptySignalException as e:
            return jsonify({"error" : f'{e}'}),404
        except:
            return jsonify({"error": "Unknown Error Occur"}),500
        
        
