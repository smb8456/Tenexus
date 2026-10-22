"""Web app: pages, JSON API, validation and error handling."""
import os
import tempfile
import unittest

from app import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.app = create_app(os.path.join(tmp.name, "api.db"))
        self.client = self.app.test_client()

    def create(self, message="My sink is leaking under the cabinet", tenant_id=1):
        return self.client.post("/api/requests", json={"tenant_id": tenant_id, "message": message})

    # ---- JSON API ----
    def test_health(self):
        self.assertEqual(self.client.get("/api/health").json, {"status": "ok"})

    def test_create_request_returns_the_decision(self):
        r = self.create()
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.json["route"], r.json["vendor_name"]), ("VENDOR", "Liberty Plumbing"))
        self.assertEqual(len(r.json["audit"]), 10)

    def test_get_request_by_id(self):
        rid = self.create().json["id"]
        r = self.client.get(f"/api/requests/{rid}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["category"], "plumbing")
        self.assertEqual(len(r.json["audit"]), 10)

    def test_list_requests_for_a_landlord(self):
        self.create()
        self.create(tenant_id=3)                       # belongs to the other landlord
        r = self.client.get("/api/requests?landlord_id=1")
        self.assertEqual(len(r.json["requests"]), 1)

    def test_validation_errors_are_400_json(self):
        for payload in ({"tenant_id": 1, "message": "hi"}, {"tenant_id": 1}, {"message": "My sink is leaking"},
                        {"tenant_id": "1", "message": "My sink is leaking"}):
            with self.subTest(payload=payload):
                r = self.client.post("/api/requests", json=payload)
                self.assertEqual(r.status_code, 400)
                self.assertIn("error", r.json)

    def test_non_json_body_is_400(self):
        r = self.client.post("/api/requests", data="not json", content_type="text/plain")
        self.assertEqual(r.status_code, 400)

    def test_unknown_things_are_404(self):
        self.assertEqual(self.client.get("/api/requests/999").status_code, 404)
        self.assertEqual(self.create(tenant_id=999).status_code, 404)
        self.assertEqual(self.client.get("/api/stats?landlord_id=999").status_code, 404)
        self.assertEqual(self.client.get("/nope").status_code, 404)

    def test_missing_landlord_id_is_400(self):
        self.assertEqual(self.client.get("/api/stats").status_code, 400)
        self.assertEqual(self.client.get("/api/requests").status_code, 400)

    def test_review_through_the_api(self):
        rid = self.create().json["id"]
        denied = self.client.post(f"/api/requests/{rid}/review", json={"landlord_id": 2, "route": "VENDOR"})
        self.assertEqual(denied.status_code, 403)
        bad = self.client.post(f"/api/requests/{rid}/review", json={"landlord_id": 1, "route": "MAYBE"})
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post(f"/api/requests/{rid}/review", json={"landlord_id": 1, "route": "VENDOR"})
        self.assertEqual((ok.status_code, ok.json["status"]), (200, "REVIEWED"))
        stats = self.client.get("/api/stats?landlord_id=1").json
        self.assertEqual(stats["ai_agreement"]["agreement_pct"], 100.0)
        self.assertEqual(stats["routes"]["VENDOR"], 1)

    # ---- web pages ----
    def test_pages_render(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        self.assertEqual(self.client.get("/dashboard?landlord_id=2").status_code, 200)
        self.assertEqual(self.client.get("/dashboard?landlord_id=999").status_code, 404)

    def test_tenant_form_submission_shows_the_result(self):
        r = self.client.post("/requests", data={"tenant_id": "1", "message": "I smell gas in the kitchen"},
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"911", r.data)
        self.assertIn(b"Audit trail", r.data)

    def test_tenant_form_shows_an_error_for_bad_input(self):
        r = self.client.post("/requests", data={"tenant_id": "1", "message": "hi"})
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"too short", r.data)

    def test_landlord_dashboard_review_buttons_work(self):
        rid = self.create().json["id"]
        page = self.client.get("/dashboard?landlord_id=1")
        self.assertIn(b"Needs your review", page.data)
        self.assertIn(b"My sink is leaking", page.data)
        r = self.client.post(f"/requests/{rid}/review", data={"landlord_id": "1", "action": "approve"},
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Nothing is waiting for you", r.data)

    def test_dashboard_review_by_wrong_landlord_is_403(self):
        rid = self.create().json["id"]
        r = self.client.post(f"/requests/{rid}/review", data={"landlord_id": "2", "action": "approve"})
        self.assertEqual(r.status_code, 403)

    def test_user_text_is_escaped_on_the_page(self):
        rid = self.create("<script>alert(1)</script> my sink is leaking").json["id"]
        page = self.client.get(f"/requests/{rid}")
        self.assertNotIn(b"<script>alert(1)</script>", page.data)
        self.assertIn(b"&lt;script&gt;", page.data)


if __name__ == "__main__":
    unittest.main()
