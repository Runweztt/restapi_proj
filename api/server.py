#!/usr/bin/env python3
"""
MoMo SMS REST API
Plain http.server implementation — CRUD over dsa/parsed_transactions.json,
secured with Basic Auth (api/auth.py) and validated (api/validation.py).
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from auth import check_auth, send_unauthorized
from validation import validate_transaction

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "dsa", "parsed_transactions.json")
ID_PATH = re.compile(r"^/transactions/(\d+)/?$")
LIST_PATH = "/transactions"


def load_transactions(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


TRANSACTIONS = load_transactions(DATA_FILE)
LOOKUP = {t["id"]: t for t in TRANSACTIONS}   # dict keyed by id — O(1) lookup, not a loop


def next_id():
    return (max(LOOKUP.keys()) + 1) if LOOKUP else 1


class TransactionHandler(BaseHTTPRequestHandler):
    server_version = "MoMoAPI/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"null")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _require_auth(self):
        if not check_auth(self.headers):
            send_unauthorized(self)
            return False
        return True

    def do_GET(self):
        if not self._require_auth():
            return

        if self.path.rstrip("/") == LIST_PATH:
            self.send_json(200, TRANSACTIONS)
            return

        match = ID_PATH.match(self.path)
        if match:
            record = LOOKUP.get(int(match.group(1)))
            if record is None:
                self.send_json(404, {"error": f"transaction {match.group(1)} not found"})
                return
            self.send_json(200, record)
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if not self._require_auth():
            return
        if self.path.rstrip("/") != LIST_PATH:
            self.send_json(404, {"error": "not found"})
            return

        body = self.read_json()
        ok, errors = validate_transaction(body)
        if not ok:
            self.send_json(400, {"errors": errors})
            return

        new_record = dict(body)
        new_record["id"] = next_id()
        for field in ("sender", "receiver", "transaction_id", "fee", "balance", "raw_body"):
            new_record.setdefault(field, None)

        TRANSACTIONS.append(new_record)
        LOOKUP[new_record["id"]] = new_record
        self.send_json(201, new_record)

    def do_PUT(self):
        if not self._require_auth():
            return
        match = ID_PATH.match(self.path)
        if not match:
            self.send_json(404, {"error": "not found"})
            return

        tx_id = int(match.group(1))
        record = LOOKUP.get(tx_id)
        if record is None:
            self.send_json(404, {"error": f"transaction {tx_id} not found"})
            return

        body = self.read_json()
        ok, errors = validate_transaction(body, partial=True)
        if not ok:
            self.send_json(400, {"errors": errors})
            return

        record.update(body)
        self.send_json(200, record)

    def do_DELETE(self):
        if not self._require_auth():
            return
        match = ID_PATH.match(self.path)
        if not match:
            self.send_json(404, {"error": "not found"})
            return

        tx_id = int(match.group(1))
        record = LOOKUP.pop(tx_id, None)
        if record is None:
            self.send_json(404, {"error": f"transaction {tx_id} not found"})
            return

        TRANSACTIONS.remove(record)
        self.send_json(200, {"deleted": tx_id})


def run(port=None):
    port = port or int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), TransactionHandler)
    print(f"MoMo SMS API running on http://localhost:{port}  ({len(TRANSACTIONS)} transactions loaded)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    run()