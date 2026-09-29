**Team participation sheet:** [Task sheet](https://docs.google.com/spreadsheets/d/1UfplZzWEAz3vaYvWOnUa6ftfkUAlF84FQNPcENlbFKg/edit?usp=sharing)
https://docs.google.com/spreadsheets/d/1UfplZzWEAz3vaYvWOnUa6ftfkUAlF84FQNPcENlbFKg/edit?usp=sharing

## Documentation

- [API documentation](docs/api_docs.md): every endpoint with request, response and error examples
- [Project report (PDF)](REST_API_Report.pdf): API security introduction, endpoint documentation, DSA results and Basic

# MoMo SMS Transactions REST API

A secure REST API for mobile money SMS transaction data, built in plain Python with `http.server`. It parses `modified_sms_v2.xml` into JSON, exposes full CRUD endpoints protected by HTTP Basic Authentication, and compares linear search against dictionary lookup for finding records.

## Team

| Member | Role |
|---|---|
| IRADUKUNDA CYUSA Kevin | Data parsing & DSA (search algorithms) |
| UWERA Sylvie | API implementation & documentation |
| Emmanuel Amarikwa | Authentication, security & testing |

## Features

- **XML parsing:** all 1,691 SMS records converted into JSON transaction objects.
- **CRUD endpoints:** list, view, create, update and delete transactions.
- **Basic Authentication:** every endpoint returns `401 Unauthorized` without valid credentials. Credentials are read from environment variables and compared in constant time.
- **Input validation:** POST and PUT bodies are checked for required fields, valid types and non-negative amounts. All errors are returned together with a `400`.
- **DSA comparison:** linear search versus dictionary lookup, timed on the real dataset.
- **No external dependencies:** Python standard library only.

## Project Structure

```
.
├── api/
│   ├── server.py              # HTTP server and CRUD routing
│   ├── auth.py                # Basic Auth check and 401 response
│   └── validation.py          # Request body validation
├── dsa/
│   ├── <parser_script>.py     # Parses the XML into JSON
│   ├── <search_script>.py     # Linear search vs dictionary lookup timing
│   └── parsed_transactions.json
├── docs/
│   └── api_docs.md            # Full endpoint documentation
├── screenshots/               # curl test evidence
├── tests/
│   └── test_api.sh            # Automated endpoint tests
├── REST_API_Report.pdf        # Project report
└── README.md
```

## Requirements

- Python 3.8 or newer
- curl (included with Windows 10/11, macOS and Linux)
- Git Bash on Windows, to run `tests/test_api.sh`

## Setup

**1. Clone the repository**

```bash
git clone <repo-url>
cd <repo-folder>
```

**2. Parse the XML data** (optional: `dsa/parsed_transactions.json` is already included)

```bash
python dsa/<parser_script>.py
```

**3. Set credentials**

The API reads `API_USERNAME` and `API_PASSWORD`. If they are not set, it falls back to the development defaults `admin` / `password123`.

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

**4. Start the server**

```bash
python api/server.py
```

You should see:

```
MoMo SMS API running on http://localhost:8000  (1691 transactions loaded)
```

To use a different port, set the `PORT` environment variable. Stop the server with `Ctrl+C`.

## Endpoints

| Method | Endpoint | Description | Success |
|---|---|---|---|
| GET | `/transactions` | List all transactions | 200 |
| GET | `/transactions/{id}` | Get one transaction | 200 |
| POST | `/transactions` | Create a transaction | 201 |
| PUT | `/transactions/{id}` | Partially update a transaction | 200 |
| DELETE | `/transactions/{id}` | Delete a transaction | 200 |

Error codes: `400` invalid body, `401` bad or missing credentials, `404` not found. Full request and response examples are in [docs/api_docs.md](docs/api_docs.md).

## Usage

With the server running, open a second terminal:

```bash
# Get one transaction
curl -u admin:password123 http://localhost:8000/transactions/1

# Create a transaction
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"type": "payment", "amount": 5000, "timestamp": "2026-09-29 10:00:00"}'

# Update it (use the id returned by the POST)
curl -u admin:password123 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" -d '{"amount": 7500}'

# Delete it
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/1692
```

**Windows PowerShell:** `curl` is an alias for `Invoke-WebRequest`, so use `curl.exe` and escape the quotes inside JSON:

```powershell
curl.exe -u admin:password123 -X PUT http://localhost:8000/transactions/1692 -H "Content-Type: application/json" -d '{\"amount\": 7500}'
```

**Note:** data is held in memory. Changes are lost when the server restarts, and the dataset reloads from `dsa/parsed_transactions.json`.

## Testing

**Automated tests.** With the server running:

```bash
bash tests/test_api.sh
```

This runs all 10 required cases, including valid and invalid credentials and every CRUD operation.

**Screenshots.** Manual curl test evidence is in [`screenshots/`](screenshots/):

| Screenshot | Test | Result |
|---|---|---|
| `01_get_success.png` | GET with valid credentials | 200 OK |
| `02_unauthorized.png` | GET with wrong password | 401 Unauthorized |
| `03_post_created.png` | POST new transaction | 201 Created |
| `04_put_updated.png` | PUT amount 5000 → 7500 | 200 OK |
| `05_delete_success.png` | DELETE transaction 1692 | 200 OK |
| `06_get_after_delete_404.png` | GET deleted transaction | 404 Not Found |

## DSA Comparison

Both methods were timed on the full dataset of 1,691 records, averaged over 2,000 runs per id:

- **Linear search** scans the list one record at a time: O(n). Its time grows with the id's position, reaching about 160 ms for the last record.
- **Dictionary lookup** hashes the id straight to the record: O(1). It stays around 0.3 ms regardless of position, up to 500× faster.

The API uses dictionary lookup for all id-based operations. The full results table and reflection are in the report.

## Security

Basic Auth is implemented as required, but it is weak on its own: credentials are only base64-encoded, sent with every request, and never expire. In production this API should run over HTTPS and move to token-based authentication (JWT or OAuth2) with rate limiting. See the report for the full reflection.

 