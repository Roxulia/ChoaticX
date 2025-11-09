from flask import Blueprint, jsonify, request
from Services.predictionService import PredictionService
from Exceptions.ServiceExceptions import *
from flask_limiter import Limiter

class PredictionAPI:
    def __init__(self,limiter: Limiter):
        self.blueprint = Blueprint('prediction_api', __name__)
        self.limiter = limiter
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule("/predict", view_func=self.limiter.limit("5 per minute")(self.predictSignal), methods=["POST"])
        
    def predictSignal(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error":"Empty Form Data"}),403
            symbol = data.get('symbol',None)
            timeframe = data.get('timeframe',None)
            x_Values = data.get('data',{})
            predictor = PredictionService(symbol,timeframe)
            signals = predictor.predict(x_Values)
            return jsonify({"data" :signals}),200
        except Exception as e:
            return jsonify({"error": str(e)}),500
