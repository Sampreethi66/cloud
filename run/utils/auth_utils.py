import os
from functools import wraps
from flask import request, jsonify

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        shared_token = os.getenv("UI_ACCESS_TOKEN")  # ✅ Always up-to-date
        user_token = (
            request.headers.get("X-Access-Token") or
            request.args.get("token")
        )
        if user_token and user_token == shared_token:
            return f(*args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 401
    return decorated

