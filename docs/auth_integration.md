# Auth + validation integration (for Person 2)

Two modules to plug into `api/server.py`:

- `api/auth.py` — `check_auth(headers)` and `send_unauthorized(handler)`
- `api/validation.py` — `validate_transaction(body, partial=False)`

Credentials come from `API_USERNAME` / `API_PASSWORD` env vars, falling back to
`admin` / `password123` for local dev.

## Imports

If you run the server as `python api/server.py`, the `api/` folder is on the path,
so import the modules directly:

```python
from auth import check_auth, send_unauthorized
from validation import validate_transaction
```

(If you run it as `python -m api.server` from the repo root, use
`from api.auth import ...` instead.)

## Auth check

First thing in every handler. `self.headers` works as-is, no conversion needed.

```python
def do_GET(self):
    if not check_auth(self.headers):
        send_unauthorized(self)
        return
    # ... existing GET logic


def do_DELETE(self):
    if not check_auth(self.headers):
        send_unauthorized(self)
        return
    # ... existing DELETE logic
```

Same two lines at the top of `do_POST` and `do_PUT`. `send_unauthorized` writes the
full response (401, `WWW-Authenticate`, JSON body), so just `return` after it.

## Validation

Auth first, then parse the body, then validate. Invalid JSON is a 400 too.

```python
import json

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
        return None   # validate_transaction rejects None as "not a JSON object"
```

POST — full check:

```python
def do_POST(self):
    if not check_auth(self.headers):
        send_unauthorized(self)
        return

    body = self.read_json()
    ok, errors = validate_transaction(body)
    if not ok:
        self.send_json(400, {"errors": errors})
        return

    # assign the next id, save, then:
    self.send_json(201, new_record)
```

PUT — `partial=True`, only the fields sent get checked:

```python
def do_PUT(self):
    if not check_auth(self.headers):
        send_unauthorized(self)
        return

    # 404 here if the id doesn't exist

    body = self.read_json()
    ok, errors = validate_transaction(body, partial=True)
    if not ok:
        self.send_json(400, {"errors": errors})
        return

    record.update(body)
    self.send_json(200, record)
```

## Things to know

- Required on POST: `type`, `amount`, `timestamp`. Everything else is optional and
  can be `null`, like in `parsed_transactions.json`.
- `id` in the body is rejected as an unknown field — the server assigns it.
- `type` must be one of the 11 parser types.
- `tests/test_api.sh` reads the new id from the POST response, so return the created
  record (or `{"transaction": {...}}`) with an `id` field.
- Unit tests: `python -m unittest discover tests`. End-to-end: start the server, then
  `bash tests/test_api.sh`.
