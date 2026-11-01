from flask import Blueprint, jsonify, request
from prediction.predictor import predict, store
from routes.alert_routes import log_alert
from utils.validation import validate_predict_payload

bp = Blueprint("prediction", __name__)


@bp.post("/api/predict")
def predict_route():
    if not store.ready:
        return jsonify({"error": "models_unavailable", "message": store.error}), 503
    clean, errors = validate_predict_payload(request.get_json(silent=True), store.meta)
    if errors:
        return jsonify({"error": "validation_failed", "details": errors}), 400
    result = predict(clean)
    log_alert(result)
    return jsonify(result)
