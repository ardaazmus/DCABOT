import asyncio
import json
import unittest

from starlette.requests import Request

from dcabot.server.api import create_data_quality


BAR_CSV = b"""open_time_us,close_time_us,open,high,low,close,base_volume,is_closed
1700000000000000,1700000060000000,100,101,99,100.5,2,true
"""


def make_request(filename: str, body: bytes, content_length: str | None = None) -> Request:
    headers = [(b"x-filename", filename.encode()), (b"content-type", b"text/csv")]
    if content_length is not None:
        headers.append((b"content-length", content_length.encode()))
    messages = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        return messages.pop(0)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/data-quality",
        "headers": headers,
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 1),
    }
    return Request(scope, receive)


class DataQualityApiContractTests(unittest.TestCase):
    def test_valid_upload_returns_deterministic_report(self):
        response = asyncio.run(create_data_quality(make_request("bars.csv", BAR_CSV)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        payload = json.loads(response.body)
        self.assertEqual(payload["data"]["status"], "PASS")
        self.assertEqual(payload["data"]["kind"], "bar")
        self.assertEqual(payload["data"]["row_count"], 1)

    def test_rejected_quality_report_returns_report_and_422(self):
        response = asyncio.run(create_data_quality(make_request("bars.csv", b"open,high\n100,101\n")))

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        payload = json.loads(response.body)
        self.assertEqual(payload["data"]["status"], "REJECTED")
        self.assertEqual(payload["data"]["issues"][0]["code"], "unsupported_schema")

    def test_declared_oversized_upload_is_rejected_before_body_read(self):
        request = make_request("bars.csv", b"", str(20 * 1024 * 1024 + 1))

        response = asyncio.run(create_data_quality(request))

        self.assertEqual(response.status_code, 422)
        payload = json.loads(response.body)
        self.assertEqual(payload["error"]["fields"]["file"], "Dosya çok büyük.")

    def test_quality_response_has_a_bounded_serialized_body(self):
        extra_headers = [f"x{index:05d}" for index in range(40_000)]
        header = "open_time_us,close_time_us,open,high,low,close,base_volume,is_closed," + ",".join(extra_headers)
        row = "1700000000000000,1700000060000000,100,101,99,100.5,2,true," + ",".join("x" for _ in extra_headers)

        response = asyncio.run(create_data_quality(make_request("bars.csv", f"{header}\n{row}\n".encode())))

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.media_type, "application/problem+json")
        self.assertEqual(json.loads(response.body)["code"], "QUALITY_RESPONSE_TOO_LARGE")
        self.assertLessEqual(len(response.body), 256 * 1024)
