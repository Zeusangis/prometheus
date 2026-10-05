import uuid

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException

from models import db


def api_error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {
            400: "Invalid request.",
            404: "Resource not found.",
            405: "Method not allowed.",
            413: "Upload exceeds the permitted request size. Resume limit is 5 MB.",
        }
        return api_error(
            f"http_{error.code}", messages.get(error.code, "Request could not be completed."), error.code
        )

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        request_id = uuid.uuid4().hex
        current_app.logger.exception("Unexpected API error request_id=%s", request_id)
        return jsonify({"error": {
            "code": "internal_error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": request_id,
        }}), 500
