#!/usr/bin/env bash
# run the server first (python api/server.py), then: bash tests/test_api.sh
# override with PORT=9000, API_USERNAME=..., API_PASSWORD=..., EXISTING_ID=...

PORT="${PORT:-8000}"
BASE="http://localhost:${PORT}"
USER="${API_USERNAME:-admin}"
PASS="${API_PASSWORD:-password123}"
EXISTING_ID="${EXISTING_ID:-1}"
JSON="Content-Type: application/json"

label() {
    echo
    echo "=================================================================="
    echo "== $1"
    echo "=================================================================="
}

label "1. GET /transactions (valid creds) - expect 200"
# full list is ~1700 records, only show the start
curl -s -i -u "$USER:$PASS" "$BASE/transactions" | head -c 1500
echo

label "2. GET /transactions (wrong creds) - expect 401"
curl -s -i -u "$USER:wrongpassword" "$BASE/transactions"
echo

label "3. GET /transactions (no creds) - expect 401"
curl -s -i "$BASE/transactions"
echo

label "4. GET /transactions/$EXISTING_ID - expect 200"
curl -s -i -u "$USER:$PASS" "$BASE/transactions/$EXISTING_ID"
echo

label "5. POST /transactions (new record) - expect 201"
POST_OUT=$(curl -s -i -u "$USER:$PASS" -X POST -H "$JSON" "$BASE/transactions" \
    -d '{"type": "payment", "amount": 5000, "timestamp": "27 Sep 2026 2:00:00 PM", "receiver": "Test User", "fee": 0}')
echo "$POST_OUT"
echo

# pull the new id out of the response body, works for {"id": ..} or {"transaction": {"id": ..}}
NEW_ID=$(printf '%s' "$POST_OUT" | sed '1,/^\r\{0,1\}$/d' | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    d = d.get("transaction", d) if isinstance(d, dict) else {}
    print(d.get("id", ""))
except Exception:
    pass
')
if [ -z "$NEW_ID" ]; then
    echo "!! couldn't read an id from the POST response, stopping"
    exit 1
fi
echo ">> created id: $NEW_ID"

label "6. PUT /transactions/$NEW_ID (update amount) - expect 200"
curl -s -i -u "$USER:$PASS" -X PUT -H "$JSON" "$BASE/transactions/$NEW_ID" \
    -d '{"amount": 7500}'
echo

label "7. GET /transactions/$NEW_ID (confirm amount is 7500) - expect 200"
curl -s -i -u "$USER:$PASS" "$BASE/transactions/$NEW_ID"
echo

label "8. DELETE /transactions/$NEW_ID - expect 200 or 204"
curl -s -i -u "$USER:$PASS" -X DELETE "$BASE/transactions/$NEW_ID"
echo

label "9. GET /transactions/$NEW_ID (after delete) - expect 404"
curl -s -i -u "$USER:$PASS" "$BASE/transactions/$NEW_ID"
echo

label "10. POST /transactions (invalid body) - expect 400"
curl -s -i -u "$USER:$PASS" -X POST -H "$JSON" "$BASE/transactions" \
    -d '{"type": "payment", "amount": "lots"}'
echo
