"""Flask application entry point.  Run:  python app.py"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from prediction.predictor import store
from routes import alert_routes, analytics_routes, location_routes, prediction_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def create_app():
    app = Flask(__name__)
    CORS(app)  # allow the HTML/JS frontend (different port) to call the API
    alert_routes.init_db()
    store.load()
    for module in (prediction_routes, location_routes, analytics_routes, alert_routes):
        app.register_blueprint(module.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok" if store.ready else "degraded", "backend": True,
                        "models_loaded": store.ready, "demo_data": bool(store.ready and store.meta.get("demo_data")), "risk_model_loaded": store.risk_model is not None,
                        "trained_at": store.meta["trained_at"] if store.ready else None,
                        "message": None if store.ready else store.error})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "not_found"}), 404

    @app.errorhandler(Exception)
    def unexpected(exc):
        logging.exception("Unhandled error")
        return jsonify({"error": "server_error", "message": str(exc)}), 500
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
