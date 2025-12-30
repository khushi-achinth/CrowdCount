import jwt
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "crowdcount_secret_key"
ALGORITHM = "HS256"


def generate_token(username, role):
    payload = {
        "user": username,
        "role": role
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def extract_token():
    """
    Extract JWT from:
    Authorization: Bearer <token>
    OR
    Authorization: <token>
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    return auth_header


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            verify_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 403
        return fn(*args, **kwargs)
    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            payload = verify_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 403

        if payload.get("role") != "admin":
            return jsonify({"error": "Admin only"}), 403

        return fn(*args, **kwargs)
    return wrapper
