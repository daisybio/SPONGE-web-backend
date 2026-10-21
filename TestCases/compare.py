"""Helpers to compare controller vs mock payloads under DuckDB nondeterminism."""
import json
from flask import Response


def normalize_payload(val):
    """Normalize Flask Responses and list order so equality is content-based."""
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], Response):
        return (val[0].get_json(), val[1])
    if isinstance(val, Response):
        return json.loads(val.get_data(as_text=True))
    if isinstance(val, list):
        return sorted(val, key=lambda x: json.dumps(x, sort_keys=True, default=str))
    return val


def assert_payloads_equal(test_case, mock_response, api_response):
    test_case.assertEqual(normalize_payload(mock_response), normalize_payload(api_response))
