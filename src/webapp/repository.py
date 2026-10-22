"""Storage layer: runs the SQL in schema.sql and returns domain objects."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from models import Landlord, MaintenanceRequest, Property, Tenant, Vendor

SCHEMA = Path(__file__).with_name("schema.sql")
NOW = "strftime('%Y-%m-%d %H:%M:%f', 'now')"


class Repository:
    def __init__(self, db_path):
        self.db_path = str(db_path)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------- setup ----------
    def init_schema(self):
        with self.connect() as db:
            db.executescript(SCHEMA.read_text())

    def has_schema(self):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM sqlite_master WHERE name = 'requests'").fetchone() is not None

    def seed_demo(self):
        """Demo data only: made-up landlords, tenants, vendors and FAQ answers."""
        with self.connect() as db:
            db.executescript("""
            INSERT INTO landlords (id, name, email) VALUES
                (1, 'Ana Rivera', 'ana@example.com'), (2, 'Jo Park', 'jo@example.com');
            INSERT INTO properties (id, landlord_id, address) VALUES
                (1, 1, '1420 Spruce St'), (2, 2, '88 Market St');
            INSERT INTO tenants (id, property_id, name, email) VALUES
                (1, 1, 'Sam Carter', 'sam@example.com'),
                (2, 1, 'Maya Lopez', 'maya@example.com'),
                (3, 2, 'Dev Patel', 'dev@example.com');
            INSERT INTO vendors (landlord_id, name, trade, phone) VALUES
                (1, 'Liberty Plumbing',   'plumber',     '555-0101'),
                (1, 'Brightside Electric','electrician', '555-0102'),
                (1, 'Comfort Air HVAC',   'hvac',        '555-0103'),
                (1, 'FixRight Appliance', 'appliance',   '555-0104'),
                (1, 'Pest Away',          'pest',        '555-0105'),
                (2, 'Market Plumbing',    'plumber',     '555-0201');
            INSERT INTO faq (property_id, question, answer) VALUES
                (1, 'When is trash day? What day is garbage pickup? Where do I put the trash and recycling?',
                    'Trash and recycling go out Tuesday night. Bins are by the back gate.'),
                (1, 'What are the quiet hours? How late can I play music? Noise rules',
                    'Quiet hours are 10 pm to 7 am.'),
                (1, 'When is rent due? How do I pay my rent? Rent payment date',
                    'Rent is due on the 1st of each month. Contact your landlord for payment options.'),
                (1, 'Where can my guests park? Is guest parking allowed? Parking policy',
                    'Guests may park in the marked visitor spots behind the building.'),
                (1, 'What are the laundry room hours? When does the laundry room close? Where is the laundry',
                    'The laundry room is open 8 am to 9 pm daily.'),
                (2, 'When is trash day? What day is garbage pickup? Where do I put the trash and recycling?',
                    'Trash goes out Friday morning.');
            """)

    # ---------- reading ----------
    def list_tenants(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT t.id, t.name, p.address FROM tenants t JOIN properties p ON p.id = t.property_id ORDER BY t.id")]

    def list_landlords(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT id, name FROM landlords ORDER BY id")]

    def load_landlord(self, landlord_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM landlords WHERE id = ?", (landlord_id,)).fetchone()
        return Landlord(row["id"], row["name"], row["email"]) if row else None

    def load_tenant(self, tenant_id):
        """Build a Tenant with their Property, Landlord and the landlord's vendors."""
        with self.connect() as db:
            t = db.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
            if t is None:
                return None
            p = db.execute("SELECT * FROM properties WHERE id = ?", (t["property_id"],)).fetchone()
            l = db.execute("SELECT * FROM landlords WHERE id = ?", (p["landlord_id"],)).fetchone()
            vendors = db.execute("SELECT * FROM vendors WHERE landlord_id = ? ORDER BY id", (l["id"],)).fetchall()
        landlord = Landlord(l["id"], l["name"], l["email"])
        prop = Property(p["id"], p["address"], landlord)
        for v in vendors:
            prop.add_vendor(Vendor(v["name"], v["trade"], v["phone"]))
        return Tenant(t["id"], t["name"], t["email"], prop)

    def faqs_for(self, property_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT id, question, answer FROM faq WHERE property_id = ? ORDER BY id", (property_id,))]

    def get_request(self, request_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM request_details WHERE id = ?", (request_id,)).fetchone()
        return dict(row) if row else None

    def load_request(self, request_id):
        row = self.get_request(request_id)
        if row is None:
            return None
        return MaintenanceRequest.restore(self.load_tenant(row["tenant_id"]), row)

    def audit_for(self, request_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT step, step_name, detail FROM audit_log WHERE request_id = ? ORDER BY step", (request_id,))]

    def queue(self, landlord_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM landlord_queue WHERE landlord_id = ? ORDER BY urgency DESC, created_at ASC, id ASC",
                (landlord_id,))]

    def recent(self, landlord_id, limit=15):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM request_details WHERE landlord_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
                (landlord_id, limit))]

    def all_requests(self, landlord_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM request_details WHERE landlord_id = ? ORDER BY id", (landlord_id,))]

    def stats(self, landlord_id):
        counts = {"ANSWER": 0, "VENDOR": 0, "ESCALATE": 0}
        with self.connect() as db:
            for r in db.execute("SELECT route, total FROM request_stats WHERE landlord_id = ?", (landlord_id,)):
                counts[r["route"]] = r["total"]
        return counts

    def agreement(self, landlord_id):
        with self.connect() as db:
            row = db.execute("SELECT reviewed, agreed, agreement_pct FROM ai_agreement WHERE landlord_id = ?",
                             (landlord_id,)).fetchone()
        return dict(row) if row else {"reviewed": 0, "agreed": 0, "agreement_pct": None}

    # ---------- writing ----------
    def save_request(self, req):
        with self.connect() as db:
            cur = db.execute(
                """INSERT INTO requests (tenant_id, property_id, message, category, confidence, urgency, route,
                                         reason, vendor_name, vendor_phone, answer_text, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (req.tenant.id, req.property.id, req.message, req.category, req.confidence, req.urgency,
                 req.route, req.reason, req.vendor_name, req.vendor_phone, req.answer_text, req.status))
        req.id = cur.lastrowid
        return req.id

    def save_audit(self, request_id, entries):
        with self.connect() as db:
            db.executemany("INSERT INTO audit_log (request_id, step, step_name, detail) VALUES (?, ?, ?, ?)",
                           [(request_id, s, n, d) for s, n, d in entries])

    def save_review(self, req):
        with self.connect() as db:
            db.execute(f"UPDATE requests SET landlord_route = ?, status = ?, reviewed_at = {NOW} WHERE id = ?",
                       (req.landlord_route, req.status, req.id))
