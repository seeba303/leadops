import unittest

from fastapi.testclient import TestClient
from leadops.api import create_app

LEAD = {
    "name": "Ana",
    "email": "ana@example.com",
    "company": "Example",
    "industry": "SaaS",
    "company_size": 50,
    "job_title": "VP Sales",
    "source": "inbound",
}


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_health_and_schema(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertIn("/v1/qualify", self.client.get("/openapi.json").json()["paths"])

    def test_qualification_and_replay(self):
        body = {"leads": [LEAD]}
        response = self.client.post("/v1/qualify", json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decisions"][0]["score"], 100)
        self.assertEqual(
            response.json(), self.client.post("/v1/qualify", json=body).json()
        )

    def test_normalized_duplicates_first_wins(self):
        result = self.client.post(
            "/v1/qualify",
            json={"leads": [LEAD, {**LEAD, "email": " ANA@EXAMPLE.COM "}]},
        ).json()
        self.assertEqual((result["processed"], result["duplicates"]), (1, 1))

    def test_invalid_input_does_not_echo_contact(self):
        response = self.client.post(
            "/v1/qualify", json={"leads": [{**LEAD, "email": "private-invalid-value"}]}
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-invalid-value", response.text)

    def test_bounds_and_types(self):
        for changes in (
            {"company_size": 0},
            {"company_size": True},
            {"company_size": "50"},
            {"name": " "},
            {"company": "x" * 201},
            {"unexpected": 1},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(
                    self.client.post(
                        "/v1/qualify", json={"leads": [{**LEAD, **changes}]}
                    ).status_code,
                    422,
                )
        for items in ([], [LEAD] * 101):
            self.assertEqual(
                self.client.post("/v1/qualify", json={"leads": items}).status_code, 422
            )

    def test_malformed_json(self):
        self.assertEqual(
            self.client.post(
                "/v1/qualify", content="{", headers={"content-type": "application/json"}
            ).status_code,
            422,
        )

    def test_batch_is_atomic(self):
        response = self.client.post(
            "/v1/qualify", json={"leads": [LEAD, {**LEAD, "email": "bad"}]}
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("decisions", response.json())
