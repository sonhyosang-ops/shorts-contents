import unittest

from fastapi.testclient import TestClient

from edu_shorts.web_api import app


class WebApiTests(unittest.TestCase):
    def test_health_endpoint_does_not_require_secrets(self) -> None:
        response = TestClient(app).get("/health")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())
