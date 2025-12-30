# auth.py

import jwt
import datetime
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "crowdcount-secret-key"  # keep constant

def generate_token(username, role):
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def token_required(required_role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Token missing"}), 401

            token = auth_header.split(" ")[1]

            try:
                decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            if required_role and decoded["role"] != required_role:
                return jsonify({"error": "Access denied"}), 403

            request.user = decoded
            return f(*args, **kwargs)

        return wrapper
    return decorator
