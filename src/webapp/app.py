"""Tenexus web application (Flask + SQLite).

Run:  python app.py      then open http://127.0.0.1:5000
"""
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

from ai import AIEngine
from models import DomainError, PermissionDenied
from repository import Repository
from workflow import NotFound, ValidationError, process_request, review_request, tenant_message

ROUTES = ("ANSWER", "VENDOR", "ESCALATE")


def create_app(db_path=None):
    app = Flask(__name__)
    db_path = db_path or os.environ.get("TENEXUS_DB") or str(Path(__file__).with_name("tenexus.db"))
    repo = Repository(db_path)
    if not repo.has_schema():
        repo.init_schema()
        repo.seed_demo()
    ai = AIEngine.trained()
    app.config.update(REPO=repo, AI=ai)

    def wants_json():
        return request.path.startswith("/api/")

    def fail(message, status):
        if wants_json():
            return jsonify({"error": message}), status
        return render_template("error.html", message=message, status=status), status

    @app.errorhandler(ValidationError)
    def _validation(e):
        return fail(str(e), 400)

    @app.errorhandler(DomainError)
    def _domain(e):
        return fail(str(e), 400)

    @app.errorhandler(PermissionDenied)
    def _denied(e):
        return fail(str(e), 403)

    @app.errorhandler(NotFound)
    def _notfound(e):
        return fail(str(e), 404)

    @app.errorhandler(404)
    def _404(e):
        return fail("Page not found.", 404)

    def present(row):
        """Add the tenant-facing text to a stored request row."""
        row = dict(row)
        row["tenant_message"] = tenant_message(row["route"], row["reason"], row["category"],
                                               row["answer_text"], row["vendor_name"], row["vendor_phone"])
        return row

    # ---------------- web pages ----------------
    @app.get("/")
    def portal():
        return render_template("portal.html", tenants=repo.list_tenants(), error=None, message="", selected=None)

    @app.post("/requests")
    def submit_form():
        raw_id = request.form.get("tenant_id", "")
        message = request.form.get("message", "")
        try:
            result = process_request(repo, ai, int(raw_id) if raw_id.isdigit() else None, message)
        except ValidationError as e:
            return render_template("portal.html", tenants=repo.list_tenants(), error=str(e),
                                   message=message, selected=raw_id), 400
        return redirect(url_for("request_page", request_id=result["id"]))

    @app.get("/requests/<int:request_id>")
    def request_page(request_id):
        row = repo.get_request(request_id)
        if row is None:
            raise NotFound("That request does not exist.")
        return render_template("request.html", r=present(row), audit=repo.audit_for(request_id))

    @app.get("/dashboard")
    def dashboard():
        landlords = repo.list_landlords()
        landlord_id = request.args.get("landlord_id", type=int) or landlords[0]["id"]
        if repo.load_landlord(landlord_id) is None:
            raise NotFound("That landlord account does not exist.")
        return render_template("dashboard.html", landlords=landlords, landlord_id=landlord_id,
                               queue=repo.queue(landlord_id), recent=repo.recent(landlord_id),
                               stats=repo.stats(landlord_id), agreement=repo.agreement(landlord_id),
                               routes=ROUTES)

    @app.post("/requests/<int:request_id>/review")
    def review_form(request_id):
        landlord_id = request.form.get("landlord_id", type=int)
        row = repo.get_request(request_id)
        if row is None:
            raise NotFound("That request does not exist.")
        route = row["route"] if request.form.get("action") == "approve" else request.form.get("route")
        review_request(repo, request_id, landlord_id, route)
        return redirect(url_for("dashboard", landlord_id=landlord_id))

    # ---------------- JSON API ----------------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/requests")
    def api_create():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("Send a JSON object with tenant_id and message.")
        result = process_request(repo, ai, data.get("tenant_id"), data.get("message"))
        return jsonify(result), 201

    @app.get("/api/requests/<int:request_id>")
    def api_get(request_id):
        row = repo.get_request(request_id)
        if row is None:
            raise NotFound("That request does not exist.")
        return jsonify({**present(row), "audit": repo.audit_for(request_id)})

    @app.get("/api/requests")
    def api_list():
        landlord_id = request.args.get("landlord_id", type=int)
        if landlord_id is None:
            raise ValidationError("landlord_id is required.")
        if repo.load_landlord(landlord_id) is None:
            raise NotFound("That landlord account does not exist.")
        return jsonify({"requests": [present(r) for r in repo.all_requests(landlord_id)]})

    @app.post("/api/requests/<int:request_id>/review")
    def api_review(request_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("Send a JSON object with landlord_id and route.")
        landlord_id = data.get("landlord_id")
        if isinstance(landlord_id, bool) or not isinstance(landlord_id, int):
            raise ValidationError("landlord_id must be a whole number.")
        req = review_request(repo, request_id, landlord_id, data.get("route"))
        return jsonify({"id": req.id, "status": req.status, "landlord_route": req.landlord_route})

    @app.get("/api/stats")
    def api_stats():
        landlord_id = request.args.get("landlord_id", type=int)
        if landlord_id is None:
            raise ValidationError("landlord_id is required.")
        if repo.load_landlord(landlord_id) is None:
            raise NotFound("That landlord account does not exist.")
        return jsonify({"routes": repo.stats(landlord_id), "ai_agreement": repo.agreement(landlord_id)})

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
