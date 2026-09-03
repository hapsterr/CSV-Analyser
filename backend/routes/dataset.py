import os
import logging
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from data.dataset_store import dataset_store
from masking.masking_service import MaskingService

logger = logging.getLogger(__name__)

dataset_bp = Blueprint("dataset", __name__)

ALLOWED_EXTENSIONS = {"csv"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@dataset_bp.route("/api/dataset/upload", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    try:
        filename = secure_filename(file.filename)
        df = pd.read_csv(file)

        if df.empty:
            return jsonify({"error": "CSV file is empty"}), 400

        if len(df.columns) == 0:
            return jsonify({"error": "CSV has no columns"}), 400

        masking = MaskingService()
        schema = masking.create_column_mapping(list(df.columns), df.dtypes)

        # Store the masking service with the dataset
        record = dataset_store.save(filename, df, schema)
        record.masking_service = masking

        # Store the real column mapping
        record.real_column_map = masking.get_reverse_mapping()

        # Log what the AI will see vs what's real (for debugging only, not production)
        logger.info(f"Dataset loaded: {filename}, rows={len(df)}, cols={len(df.columns)}")
        logger.info(f"Column mapping for AI: {masking.get_column_mapping()}")

        return jsonify({
            "dataset_id": record.dataset_id,
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "schema": schema,
        }), 201

    except pd.errors.EmptyDataError:
        return jsonify({"error": "CSV file is empty"}), 400
    except pd.errors.ParserError:
        return jsonify({"error": "Invalid CSV format"}), 400
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@dataset_bp.route("/api/dataset/<dataset_id>", methods=["GET"])
def get_dataset_info(dataset_id):
    record = dataset_store.get(dataset_id)
    if not record:
        return jsonify({"error": "Dataset not found"}), 404

    return jsonify({
        "dataset_id": record.dataset_id,
        "filename": record.filename,
        "rows": record.rows,
        "columns": record.columns,
        "schema": record.schema,
    })


@dataset_bp.route("/api/dataset/<dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id):
    if dataset_store.delete(dataset_id):
        return jsonify({"message": "Dataset deleted"}), 200
    return jsonify({"error": "Dataset not found"}), 404
