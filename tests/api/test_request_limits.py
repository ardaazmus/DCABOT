import asyncio
import json
import unittest

from dcabot.server import api


def _run_request(
    path: str,
    body: bytes,
    *,
    include_content_length: bool = True,
    receive_calls: list[int] | None = None,
    chunks: list[bytes] | None = None,
    content_length_override: int | None = None,
) -> list[dict[str, object]]:
    if chunks is not None:
        messages = [
            {"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1}
            for index, chunk in enumerate(chunks)
        ]
    elif include_content_length:
        messages = [{"type": "http.request", "body": body, "more_body": False}]
    else:
        midpoint = min(4 * 1024 + 1, len(body))
        messages = [
            {"type": "http.request", "body": body[:midpoint], "more_body": True},
            {"type": "http.request", "body": body[midpoint:], "more_body": False},
        ]
    sent: list[dict[str, object]] = []

    async def receive():
        if receive_calls is not None:
            receive_calls.append(1)
        return messages.pop(0)

    async def send(message: dict[str, object]):
        sent.append(message)

    headers = [(b"content-type", b"application/json")]
    if include_content_length:
        declared_content_length = len(body) if content_length_override is None else content_length_override
        headers.append((b"content-length", str(declared_content_length).encode()))
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

    def test_validation_rejects_oversized_chunked_body_without_content_length(self):
        body = b'{"dataset_id":"' + b"a" * 5_000 + b'"}'
        receive_calls: list[int] = []

        messages = _run_request(
            "/api/historical-runs/validate",
            body,
            include_content_length=False,
            receive_calls=receive_calls,
        )

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")
        self.assertEqual(receive_calls, [1])
    def test_small_json_limit_is_cumulative_across_chunked_body(self):
        body = b'{"anchor":"' + b"1" * 5_000 + b'"}'
        receive_calls: list[int] = []

        messages = _run_request(
            "/api/preview",
            body,
            include_content_length=False,
            receive_calls=receive_calls,
            chunks=[body[:2_048], body[2_048:4_097], body[4_097:]],
        )

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")
        self.assertEqual(receive_calls, [1, 1])

    def test_small_json_limit_rejects_body_larger_than_declared_content_length(self):
        body = b'{"anchor":"' + b"1" * 5_000 + b'"}'
        receive_calls: list[int] = []

        messages = _run_request(
            "/api/preview",
            body,
            receive_calls=receive_calls,
            chunks=[body[:4_096], body[4_096:]],
            content_length_override=1,
        )

        self.assertEqual(messages[0]["status"], 413)
        self.assertEqual(dict(messages[0]["headers"])[b"content-type"], b"application/problem+json")
        self.assertEqual(json.loads(messages[1]["body"])["code"], "REQUEST_TOO_LARGE")
        self.assertEqual(receive_calls, [1, 1])
    def test_data_quality_keeps_upload_budget_separate_from_small_json_limit(self):
        body = b"x" * 5_000

        messages = _run_request("/api/data-quality", body)

        self.assertEqual(messages[0]["status"], 422)
