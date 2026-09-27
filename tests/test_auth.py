import base64
import io
import json
import os
import unittest
from email.message import Message
from unittest import mock

from api.auth import check_auth, send_unauthorized

TEST_ENV = {"API_USERNAME": "admin", "API_PASSWORD": "password123"}


def basic(creds):
    if isinstance(creds, str):
        creds = creds.encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(creds).decode("ascii")}


# pin the creds so a real API_USERNAME/API_PASSWORD in the shell doesn't break tests
@mock.patch.dict(os.environ, TEST_ENV)
class CheckAuthTests(unittest.TestCase):

    def test_valid_credentials(self):
        self.assertTrue(check_auth(basic("admin:password123")))

    def test_wrong_password(self):
        self.assertFalse(check_auth(basic("admin:wrong")))

    def test_wrong_username(self):
        self.assertFalse(check_auth(basic("root:password123")))

    def test_missing_header(self):
        self.assertFalse(check_auth({}))

    def test_empty_header(self):
        self.assertFalse(check_auth({"Authorization": ""}))

    def test_bearer_scheme(self):
        token = base64.b64encode(b"admin:password123").decode("ascii")
        self.assertFalse(check_auth({"Authorization": "Bearer " + token}))

    def test_malformed_base64(self):
        self.assertFalse(check_auth({"Authorization": "Basic not-base64!!"}))

    def test_non_utf8_bytes(self):
        self.assertFalse(check_auth(basic(b"\xff\xfe:\xfd")))

    def test_no_colon(self):
        self.assertFalse(check_auth(basic("adminpassword123")))

    def test_password_containing_colon(self):
        with mock.patch.dict(os.environ, {"API_PASSWORD": "pa:ss:word"}):
            self.assertTrue(check_auth(basic("admin:pa:ss:word")))
            self.assertFalse(check_auth(basic("admin:pa")))

    def test_http_server_message_headers(self):
        # http.server hands handlers an email.message.Message subclass
        headers = Message()
        headers["Authorization"] = basic("admin:password123")["Authorization"]
        self.assertTrue(check_auth(headers))


class FakeHandler:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.wfile = io.BytesIO()

    def send_response(self, code):
        self.status = code

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass


class SendUnauthorizedTests(unittest.TestCase):

    def test_sends_401_with_challenge(self):
        handler = FakeHandler()
        send_unauthorized(handler)
        self.assertEqual(handler.status, 401)
        self.assertEqual(handler.headers["WWW-Authenticate"], 'Basic realm="MoMo API"')
        self.assertEqual(handler.headers["Content-Type"], "application/json")
        self.assertEqual(json.loads(handler.wfile.getvalue()), {"error": "Unauthorized"})


if __name__ == "__main__":
    unittest.main()
