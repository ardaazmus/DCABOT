import asyncio
import json
import unittest

from dcabot.server import api


def _run_request(path: str, body: bytes, *, include_content_length: bool = True) -> list[dict[str, object]]:
    if include_content_length:
        messages = [{"type": "http.request", "body": body, "more_body": False}]
    else:
        midpoint = len(body) // 2
        messages = [
            {"type": "http.request", "body": body[:midpoint], "more_body": True},
            {"type": "http.request", "body": body[midpoint:], "more_body": False},
        ]
    sent: list[dict[str, object]] = []

    async def receive():
        return messages.pop(0)

    async def send(message: dict[str, object]):
        sent.append(message)

    headers = [(b"content-type", b"application/json")]
    if include_content_length:
        headers.append((b"content-length", str(len(body)).encode()))
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 1),
    }
    asyncio.run(api.app(scope, receive, send))
    return sent


class RequestLimitApiTests(unittest.TestCase):
    def test_preview_rejects_oversized_json_body_before_handler(self):
        body = b'{"anchor":"' + b"1" * 5_000 + b'"}'

        messages = _run_request("/api/preview", body)

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")

    def test_simulation_rejects_oversized_json_body_before_validation(self):
        body = b'{"dataset_id":"' + b"a" * 5_000 + b'"}'

        messages = _run_request("/api/historical-runs/simulate", body)

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")

    def test_base_limit_simulation_rejects_oversized_json_body_before_validation(self):
        body = b'{"dataset_id":"' + b"a" * 5_000 + b'"}'

        messages = _run_request("/api/historical-runs/simulate-base-limit", body)

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")

    def test_historical_run_save_rejects_oversized_json_body_before_validation(self):
        body = b'{"execution_id":"' + b"a" * 5_000 + b'"}'

        messages = _run_request("/api/historical-runs", body)

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")

    def test_preview_rejects_oversized_chunked_body_without_content_length(self):
        body = b'{"anchor":"' + b"1" * 5_000 + b'"}'

        messages = _run_request("/api/preview", body, include_content_length=False)

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")

    def test_data_quality_keeps_upload_budget_separate_from_small_json_limit(self):
        body = b"x" * 5_000

        messages = _run_request("/api/data-quality", body)

        self.assertEqual(messages[0]["status"], 422)
