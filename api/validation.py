import math

REQUIRED_FIELDS = ("type", "amount", "timestamp")
# can be sent as null, same as in parsed_transactions.json
OPTIONAL_STR_FIELDS = ("sender", "receiver", "transaction_id", "raw_body")
OPTIONAL_NUM_FIELDS = ("fee", "balance")
ALLOWED_FIELDS = set(REQUIRED_FIELDS + OPTIONAL_STR_FIELDS + OPTIONAL_NUM_FIELDS)

VALID_TYPES = {
    "received", "payment", "airtime", "bank_deposit", "transfer",
    "merchant_payment", "withdrawal", "bundle_purchase", "reversal",
    "failed", "non_transaction",
}


def _is_number(value):
    # bool is a subclass of int, so rule it out explicitly
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    # json.loads accepts NaN / Infinity
    return math.isfinite(value)


def validate_transaction(body, partial=False):
    if not isinstance(body, dict):
        return False, ["body must be a JSON object"]

    errors = []

    if partial and not body:
        return False, ["body must not be empty"]

    # id is assigned by the server, so it lands here too
    for field in sorted(set(body) - ALLOWED_FIELDS):
        errors.append(f"unknown field: {field}")

    if not partial:
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append(f"missing required field: {field}")

    if "type" in body and body["type"] not in VALID_TYPES:
        errors.append("type must be one of: " + ", ".join(sorted(VALID_TYPES)))

    if "amount" in body:
        if not _is_number(body["amount"]):
            errors.append("amount must be a number")
        elif body["amount"] < 0:
            errors.append("amount must not be negative")

    if "timestamp" in body:
        ts = body["timestamp"]
        if not isinstance(ts, str) or not ts.strip():
            errors.append("timestamp must be a non-empty string")

    for field in OPTIONAL_STR_FIELDS:
        if field in body and body[field] is not None and not isinstance(body[field], str):
            errors.append(f"{field} must be a string or null")

    for field in OPTIONAL_NUM_FIELDS:
        if field in body and body[field] is not None:
            if not _is_number(body[field]):
                errors.append(f"{field} must be a number or null")
            elif body[field] < 0:
                errors.append(f"{field} must not be negative")

    return not errors, errors
