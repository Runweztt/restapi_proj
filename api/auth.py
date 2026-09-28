import base64
import binascii
import hmac
import json
import os

# dev defaults - set API_USERNAME / API_PASSWORD env vars in any real deployment
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password123"


def _expected_credentials():
    username = os.environ.get("API_USERNAME", DEFAULT_USERNAME)
    password = os.environ.get("API_PASSWORD", DEFAULT_PASSWORD)
    return username.encode("utf-8"), password.encode("utf-8")


def check_auth(headers):
    header = headers.get("Authorization") if headers is not None else None
    if not header:
        return False

    scheme, _, encoded = header.partition(" ")
    if scheme.lower() != "basic" or not encoded:
        return False

    try:
        decoded = base64.b64decode(encoded.strip(), validate=True).decode("utf-8")
    except (binascii.Error, ValueError):
        return False

    if ":" not in decoded:
        return False
    # first colon only, password is allowed to have colons
    username, password = decoded.split(":", 1)

    expected_user, expected_pass = _expected_credentials()
    # check both before returning so a bad username doesn't return faster
    user_ok = hmac.compare_digest(username.encode("utf-8"), expected_user)
    pass_ok = hmac.compare_digest(password.encode("utf-8"), expected_pass)
    return user_ok and pass_ok


def send_unauthorized(handler):
    body = json.dumps({"error": "Unauthorized"}).encode("utf-8")
    handler.send_response(401)
    handler.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
