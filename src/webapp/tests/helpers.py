import os
import tempfile

from ai import AIEngine
from repository import Repository

_AI = AIEngine.trained()          # train once, reuse in every test


def fresh_repo(testcase):
    """A brand-new seeded SQLite file for one test, cleaned up afterwards."""
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    repo = Repository(os.path.join(tmp.name, "test.db"))
    repo.init_schema()
    repo.seed_demo()
    return repo


def shared_ai():
    return _AI


def insert_request(repo, **kw):
    """Insert a raw row directly (bypasses the app) so SQL rules can be tested on their own."""
    row = dict(tenant_id=1, property_id=1, message="my sink is leaking", category="plumbing",
               confidence=0.8, urgency=5, route="VENDOR", reason="test", status="REFERRED",
               created_at="2026-01-01 10:00:00.000", landlord_route=None, reviewed_at=None)
    row.update(kw)
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    with repo.connect() as db:
        return db.execute(f"INSERT INTO requests ({cols}) VALUES ({marks})", tuple(row.values())).lastrowid
