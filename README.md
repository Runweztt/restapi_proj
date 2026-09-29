# MoMo SMS Transactions REST API

A REST API for mobile money SMS transactions, written in plain Python with `http.server` (no frameworks). We parse `modified_sms_v2.xml` into JSON, serve it through CRUD endpoints behind Basic Auth, and compare linear search against dictionary lookup on the real data.

- **Report (PDF):** [REST API Report](https://drive.google.com/file/d/17L58C38-cUT5ii1lCHKKVP7WG7kxj5Tc/view?usp=sharing) covers API security, endpoint docs, DSA results and the Basic Auth reflection
- **API docs:** [docs/api_docs.md](docs/api_docs.md) has every endpoint with request/response examples and error codes
- **Team participation sheet:** [Task sheet](https://docs.google.com/spreadsheets/d/1UfplZzWEAz3vaYvWOnUa6ftfkUAlF84FQNPcENlbFKg/edit?usp=sharing)

## Team

| Member | Role |
|---|---|
| IRADUKUNDA CYUSA Kevin | Data parsing & DSA (search algorithms) |
| UWERA Sylvie | API implementation & documentation |
| Emmanuel Amarikwa | Authentication, security & testing |

## What's in it

- All 1,691 SMS records parsed into JSON. Every record has the same 10 keys; fields that don't apply to a transaction type are `null`.
- GET, POST, PUT and DELETE on `/transactions`.
- Basic Auth on every endpoint. Credentials come from env vars and are compared in constant time. Anything wrong returns `401`.
- POST and PUT bodies are validated (required fields, valid `type`, non-negative numbers, no unknown fields). All errors come back together in one `400`.
- Linear search vs dictionary lookup, timed on the full dataset.
- Standard library only, nothing to `pip install`.

## Project structure

```
.
├── api/
│   ├── server.py              # HTTP server and CRUD routing
│   ├── auth.py                # Basic Auth check and 401 response
│   └── validation.py          # request body validation
├── dsa/
│   ├── parser.py              # XML -> JSON
│   ├── search_compare.py      # linear search vs dict lookup timing
│   ├── inspect.py             # quick look at the raw SMS bodies
│   └── parsed_transactions.json
├── docs/
│   └── api_docs.md            # endpoint documentation
├── screenshots/               # curl test evidence
├── tests/
│   ├── test_auth.py           # unit tests for auth
│   ├── test_validation.py     # unit tests for validation
│   └── test_api.sh            # curl tests against the running server
└── README.md
```

## Setup

You need Python 3.8+ and curl (already on Windows 10/11, macOS and Linux). On Windows, use Git Bash to run the `.sh` test script.

```bash
git clone https://github.com/Runweztt/restapi_proj.git
cd restapi_proj
```

`dsa/parsed_transactions.json` is already in the repo. To regenerate it from the XML:

```bash
python dsa/parser.py
```

Credentials are read from `API_USERNAME` and `API_PASSWORD`. If they're not set the server falls back to `admin` / `password123`, which is fine locally but shouldn't be used anywhere else.

```bash
# macOS / Linux / Git Bash
export API_USERNAME=admin
export API_PASSWORD=password123
```

```powershell
# Windows PowerShell
$env:API_USERNAME="admin"
$env:API_PASSWORD="password123"
```

Start the server:

```bash
python api/server.py
```

```
MoMo SMS API running on http://localhost:8000  (1691 transactions loaded)
```

Set `PORT` to use a different port. `Ctrl+C` stops it.

## Endpoints

| Method | Endpoint | Description | Success |
|---|---|---|---|
| GET | `/transactions` | List all transactions | 200 |
| GET | `/transactions/{id}` | Get one transaction | 200 |
| POST | `/transactions` | Create a transaction | 201 |
| PUT | `/transactions/{id}` | Update some fields of a transaction | 200 |
| DELETE | `/transactions/{id}` | Delete a transaction | 200 |

Errors: `400` bad body, `401` missing or wrong credentials, `404` not found. Full examples are in [docs/api_docs.md](docs/api_docs.md).

## Usage

With the server running, in another terminal:

```bash
# get one transaction
curl -u admin:password123 http://localhost:8000/transactions/1

# create one
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"type": "payment", "amount": 5000, "timestamp": "2026-09-29 10:00:00"}'

# update it (use the id the POST returned)
curl -u admin:password123 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" -d '{"amount": 7500}'

# delete it
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/1692
```

In PowerShell, `curl` is actually `Invoke-WebRequest`. Use `curl.exe` and escape the quotes in the JSON:

```powershell
curl.exe -u admin:password123 -X PUT http://localhost:8000/transactions/1692 -H "Content-Type: application/json" -d '{\"amount\": 7500}'
```

Data lives in memory, so anything you create, change or delete is gone after a restart. The server reloads from `dsa/parsed_transactions.json` each time.

## Testing

Unit tests for auth and validation, no server needed:

```bash
python -m unittest discover tests
```

These cover valid and wrong credentials, a missing header, the wrong scheme (`Bearer`), malformed base64, passwords containing colons, missing fields, string/bool/negative amounts, empty PUT bodies and unknown fields.

End-to-end curl tests, with the server running:

```bash
bash tests/test_api.sh
```

This goes through all 10 cases in order: GET with good creds, wrong creds, no creds, GET by id, POST, PUT, GET to confirm, DELETE, GET again (404), and an invalid POST (400).

Screenshots from our manual curl runs are in [`screenshots/`](screenshots/):

| Screenshot | Test | Result |
|---|---|---|
| [092527](screenshots/Screenshot%202026-09-29%20092527.png) | GET with valid credentials | 200 OK |
| [092834](screenshots/Screenshot%202026-09-29%20092834.png) | GET with wrong password | 401 Unauthorized |
| [093007](screenshots/Screenshot%202026-09-29%20093007.png) | POST new transaction | 201 Created |
| [093456](screenshots/Screenshot%202026-09-29%20093456.png) | PUT amount 5000 → 7500 | 200 OK |
| [093542](screenshots/Screenshot%202026-09-29%20093542.png) | DELETE transaction 1692 | 200 OK |
| [094131](screenshots/Screenshot%202026-09-29%20094131.png) | GET the deleted transaction | 404 Not Found |

## DSA comparison

We timed both on all 1,691 records, 2,000 lookups per id:

- Linear search walks the list until it finds the id, so it's O(n). The further down the id is, the longer it takes: about 160 ms for id 1690.
- Dictionary lookup hashes the id and jumps straight to the record, O(1). It stayed around 0.3 ms no matter which id, so up to 500× faster.

That's why the API keeps an `id -> record` dict for GET, PUT and DELETE by id. The full table and reflection are in the [report](https://drive.google.com/file/d/17L58C38-cUT5ii1lCHKKVP7WG7kxj5Tc/view?usp=sharing).

## Security

Basic Auth does the job for this assignment, but it's weak on its own. The credentials are just base64 (anyone sniffing plain HTTP can read them), they go out with every request, and they never expire. A real deployment should at least run over HTTPS, and ideally switch to tokens (JWT or OAuth2) with rate limiting. More on this in the [report](https://drive.google.com/file/d/17L58C38-cUT5ii1lCHKKVP7WG7kxj5Tc/view?usp=sharing).
