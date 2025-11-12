import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Blueprint, jsonify, request,Flask
from Services.predictionService import PredictionService
from Exceptions.ServiceExceptions import *
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_socketio import SocketIO

class PredictionAPI:
    def __init__(self,limiter: Limiter = None):
        self.blueprint = Blueprint('prediction_api', __name__)
        self.limiter = limiter
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule("/predict", view_func=self.limiter.limit("5 per minute")(self.predictSignal), methods=["POST"])
        self.blueprint.add_url_rule("/columns", view_func=self.limiter.limit("5 per minute")(self.getRequiredColumns), methods=["POST"])
        

    def getRequiredColumns(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error":"Empty Request Body"}),400
            symbol = data.get('symbol',None)
            timeframe = data.get('timeframe',None)
            print(timeframe)
            if symbol is None:
                return jsonify({"error":"Empty Symbol"}),400
            if timeframe is None:
                return jsonify({"error":"Empty Timeframe"}),400
            predictor = PredictionService(symbol,[timeframe])
            columns = predictor.getRequiredColumns()
            return jsonify({"data" :columns}),200
        except Exception as e:
            return jsonify({"error": str(e)}),500
        
    def predictSignal(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error":"Empty Request Body"}),400
            symbol = data.get('symbol',None)
            timeframe = data.get('timeframe',None)
            print(timeframe)
            if symbol is None:
                return jsonify({"error":"Empty Symbol"}),400
            if timeframe is None:
                return jsonify({"error":"Empty Timeframe"}),400
            x_Values = data.get('data',{})
            predictor = PredictionService(symbol,[timeframe])
            signals = predictor.predict(x_Values)
            return jsonify({"data" :signals}),200
        except Exception as e:
            return jsonify({"error": str(e)}),500


if __name__ == "__main__":
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    socketio = SocketIO(app,cors_allowed_origins="*")
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["50 per minute"]  # global limit
    )
    test = PredictionAPI(limiter)
    app.register_blueprint(test.blueprint,url_prefix='/api')
    socketio.run(app,host = "0.0.0.0",port = 5000,debug=True)