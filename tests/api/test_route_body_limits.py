"""Every route that reads a request body must have an explicit byte budget.

Found 2026-09-24: 14 body-reading routes (indicators, regime, correlation,
preview/full, testnet DCA session actions, …) had none, so a single request
could make the server buffer an arbitrarily large JSON body.
"""
import asyncio
import json
import unittest

from dcabot.server import api


def _post(path: str, size: int) -> tuple[int, dict]:
    body = b'{"x":"' + b"a" * size + b'"}'
    messages = [{"type": "http.request", "body": body, "more_body": False}]
    sent: list[dict] = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "method": "POST", "path": path, "raw_path": path.encode(), "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(api.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload or b"{}")


class RouteBodyLimitTests(unittest.TestCase):
    def test_every_body_reading_route_is_bounded(self):
        unbounded = sorted(
            route.path
            for route in api.app.router.routes
            if (getattr(route, "methods", None) or set()) & {"POST", "PUT", "PATCH"}
            and route.path not in api.ROUTE_BODY_LIMITS
        )
        self.assertEqual(unbounded, [])

    def test_oversized_series_is_rejected_before_parsing(self):
        for path in ("/api/indicators/sma", "/api/risk/regime", "/api/preview/full"):
            with self.subTest(path=path):
                status, body = _post(path, api.ROUTE_BODY_LIMITS[path] + 1)
                self.assertEqual((status, body.get("code")), (413, "REQUEST_TOO_LARGE"))


if __name__ == "__main__":
    unittest.main()
