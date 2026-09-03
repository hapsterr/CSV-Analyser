import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
CORS(app, origins=[frontend_url], supports_credentials=True)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

from routes.health import health_bp
from routes.dataset import dataset_bp
from routes.analyze import analyze_bp

app.register_blueprint(health_bp)
app.register_blueprint(dataset_bp)
app.register_blueprint(analyze_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
