import unittest

from api.validation import validate_transaction


def valid_body():
    return {
        "type": "payment",
        "amount": 1000.0,
        "timestamp": "10 May 2024 4:31:46 PM",
        "receiver": "Jane Smith",
        "sender": None,
        "fee": 0.0,
    }


class PostValidationTests(unittest.TestCase):

    def test_valid_post(self):
        ok, errors = validate_transaction(valid_body())
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_int_amount_ok(self):
        body = valid_body()
        body["amount"] = 500
        self.assertTrue(validate_transaction(body)[0])

    def test_missing_field(self):
        body = valid_body()
        del body["amount"]
        ok, errors = validate_transaction(body)
        self.assertFalse(ok)
        self.assertIn("missing required field: amount", errors)

    def test_string_amount(self):
        body = valid_body()
        body["amount"] = "1000"
        ok, errors = validate_transaction(body)
        self.assertFalse(ok)
        self.assertIn("amount must be a number", errors)

    def test_bool_amount(self):
        body = valid_body()
        body["amount"] = True
        ok, errors = validate_transaction(body)
        self.assertFalse(ok)
        self.assertIn("amount must be a number", errors)

    def test_negative_amount(self):
        body = valid_body()
        body["amount"] = -5
        ok, errors = validate_transaction(body)
        self.assertFalse(ok)
        self.assertIn("amount must not be negative", errors)

    def test_nan_amount(self):
        body = valid_body()
        body["amount"] = float("nan")
        self.assertFalse(validate_transaction(body)[0])

    def test_non_dict_body(self):
        for body in ([], "payment", 42, None):
            ok, errors = validate_transaction(body)
            self.assertFalse(ok)
            self.assertEqual(errors, ["body must be a JSON object"])

    def test_bad_type(self):
        body = valid_body()
        body["type"] = "refund"
        self.assertFalse(validate_transaction(body)[0])

    def test_client_cannot_set_id(self):
        body = valid_body()
        body["id"] = 9999
        ok, errors = validate_transaction(body)
        self.assertFalse(ok)
        self.assertIn("unknown field: id", errors)

    def test_reports_all_errors(self):
        ok, errors = validate_transaction({"amount": "x", "extra": 1})
        self.assertFalse(ok)
        self.assertGreaterEqual(len(errors), 4)


class PutValidationTests(unittest.TestCase):

    def test_valid_partial_put(self):
        ok, errors = validate_transaction({"amount": 2500}, partial=True)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_partial_null_optional(self):
        self.assertTrue(validate_transaction({"receiver": None}, partial=True)[0])

    def test_empty_put(self):
        ok, errors = validate_transaction({}, partial=True)
        self.assertFalse(ok)
        self.assertEqual(errors, ["body must not be empty"])

    def test_unknown_field(self):
        ok, errors = validate_transaction({"amount": 10, "hacked": True}, partial=True)
        self.assertFalse(ok)
        self.assertIn("unknown field: hacked", errors)

    def test_partial_still_checks_present_fields(self):
        self.assertFalse(validate_transaction({"amount": -1}, partial=True)[0])
        self.assertFalse(validate_transaction({"fee": "0"}, partial=True)[0])


if __name__ == "__main__":
    unittest.main()
