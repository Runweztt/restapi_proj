# MoMo SMS Transactions API

A REST API over mobile money SMS transactions, built with Python's `http.server`. All endpoints are protected with HTTP Basic Authentication and return JSON.

## Base URL

```
http://localhost:8000
```

The port can be changed with the `PORT` environment variable.

## Authentication

Every request must include an `Authorization` header using Basic Auth:

```
Authorization: Basic base64(username:password)
```

With curl, the `-u` flag builds this header for you:

```bash
curl -u admin:password123 http://localhost:8000/transactions
```

Credentials are read from the `API_USERNAME` and `API_PASSWORD` environment variables. If they are not set, the development defaults `admin` / `password123` are used. Always set your own values outside local testing.

A missing, malformed, or incorrect header returns:

```
HTTP/1.0 401 Unauthorized
WWW-Authenticate: Basic realm="MoMo API"
Content-Type: application/json

{"error": "Unauthorized"}
```

Authentication is checked before anything else, including routing and validation.

## Transaction Object

| Field | Type | Required on POST | Notes |
|---|---|---|---|
| `id` | integer | No | Assigned by the server. Cannot be sent by the client. |
| `type` | string | Yes | One of the valid types listed below. |
| `amount` | number | Yes | Must not be negative. |
| `timestamp` | string | Yes | Must be a non-empty string. |
| `sender` | string or null | No | Defaults to `null`. |
| `receiver` | string or null | No | Defaults to `null`. |
| `transaction_id` | string or null | No | Defaults to `null`. |
| `fee` | number or null | No | Must not be negative. Defaults to `null`. |
| `balance` | number or null | No | Must not be negative. Defaults to `null`. |
| `raw_body` | string or null | No | Original SMS text. Defaults to `null`. |

**Valid `type` values:** `airtime`, `bank_deposit`, `bundle_purchase`, `failed`, `merchant_payment`, `non_transaction`, `payment`, `received`, `reversal`, `transfer`, `withdrawal`.

Numbers must be real JSON numbers. Booleans (`true`/`false`), `NaN`, and `Infinity` are rejected. Any field not listed above is rejected as unknown.

---

## Endpoints

### 1. List all transactions

`GET /transactions`

**Request**

```bash
curl -u admin:password123 http://localhost:8000/transactions
```

**Response: `200 OK`**

```json
[
  {
    "id": 1,
    "type": "received",
    "amount": 2000.0,
    "sender": "Jane Smith",
    "receiver": null,
    "transaction_id": "76662021700",
    "fee": null,
    "balance": null,
    "timestamp": "10 May 2024 4:30:58 PM",
    "raw_body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. ..."
  },
  ...
]
```

**Errors**

| Code | When |
|---|---|
| 401 | Missing or invalid credentials |

---

### 2. Get one transaction

`GET /transactions/{id}`

**Request**

```bash
curl -u admin:password123 http://localhost:8000/transactions/1
```

**Response: `200 OK`**

```json
{
  "id": 1,
  "type": "received",
  "amount": 2000.0,
  "sender": "Jane Smith",
  "receiver": null,
  "transaction_id": "76662021700",
  "fee": null,
  "balance": null,
  "timestamp": "10 May 2024 4:30:58 PM",
  "raw_body": "You have received 2000 RWF from Jane Smith ..."
}
```

**Errors**

| Code | When | Body |
|---|---|---|
| 401 | Missing or invalid credentials | `{"error": "Unauthorized"}` |
| 404 | No transaction with that id | `{"error": "transaction 9999 not found"}` |
| 404 | id is not a number (e.g. `/transactions/abc`) | `{"error": "not found"}` |

Lookup uses a dictionary keyed by id, so it takes constant time regardless of dataset size.

---

### 3. Create a transaction

`POST /transactions`

**Request**

```bash
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"type": "payment", "amount": 5000, "timestamp": "2026-09-29 10:00:00"}'
```

**Response: `201 Created`**

```json
{
  "type": "payment",
  "amount": 5000,
  "timestamp": "2026-09-29 10:00:00",
  "id": 1692,
  "sender": null,
  "receiver": null,
  "transaction_id": null,
  "fee": null,
  "balance": null,
  "raw_body": null
}
```

The server assigns the next available id and fills any missing optional fields with `null`.

**Errors**

| Code | When | Example body |
|---|---|---|
| 400 | Body is not valid JSON or not an object | `{"errors": ["body must be a JSON object"]}` |
| 400 | Missing or invalid fields | see below |
| 401 | Missing or invalid credentials | `{"error": "Unauthorized"}` |
| 404 | Wrong path (e.g. `POST /transactions/5`) | `{"error": "not found"}` |

All validation errors are returned together. For example, sending `{"amount": -5}` returns:

```json
{
  "errors": [
    "missing required field: type",
    "missing required field: timestamp",
    "amount must not be negative"
  ]
}
```

---

### 4. Update a transaction

`PUT /transactions/{id}`

Partial update: send only the fields you want to change. Fields you send are validated with the same rules as POST, but nothing is required. The `id` cannot be changed.

**Request**

```bash
curl -u admin:password123 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" \
  -d '{"amount": 7500}'
```

**Response: `200 OK`**

Returns the full updated record:

```json
{
  "type": "payment",
  "amount": 7500,
  "timestamp": "2026-09-29 10:00:00",
  "id": 1692,
  "sender": null,
  "receiver": null,
  "transaction_id": null,
  "fee": null,
  "balance": null,
  "raw_body": null
}
```

**Errors**

| Code | When | Example body |
|---|---|---|
| 400 | Empty body `{}` | `{"errors": ["body must not be empty"]}` |
| 400 | Invalid field value or unknown field (including `id`) | `{"errors": ["unknown field: id"]}` |
| 401 | Missing or invalid credentials | `{"error": "Unauthorized"}` |
| 404 | No transaction with that id | `{"error": "transaction 9999 not found"}` |

---

### 5. Delete a transaction

`DELETE /transactions/{id}`

**Request**

```bash
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/1692
```

**Response: `200 OK`**

```json
{"deleted": 1692}
```

A later `GET /transactions/1692` returns `404`.

**Errors**

| Code | When | Body |
|---|---|---|
| 401 | Missing or invalid credentials | `{"error": "Unauthorized"}` |
| 404 | No transaction with that id | `{"error": "transaction 9999 not found"}` |

---

## Error Code Summary

| Code | Meaning | Body format |
|---|---|---|
| 200 | Success | Record, list, or `{"deleted": id}` |
| 201 | Transaction created | New record |
| 400 | Invalid request body | `{"errors": [...]}` |
| 401 | Authentication failed | `{"error": "Unauthorized"}` |
| 404 | Transaction or route not found | `{"error": "..."}` |
| 501 | Unsupported method (e.g. PATCH) | HTML error page from `http.server` |

## Notes

- **Windows PowerShell:** `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe` instead, and escape inner quotes in JSON bodies: `-d '{\"amount\": 7500}'`.
- **Storage is in memory.** Data is loaded from `dsa/parsed_transactions.json` at startup. Created, updated, and deleted records are lost when the server restarts.
- **Use HTTPS in production.** Basic Auth only base64-encodes credentials, so they are readable to anyone who intercepts plain HTTP traffic.