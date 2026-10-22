import sqlite3
import unittest
from pathlib import Path

SQL = (Path(__file__).parent / "triage.sql").read_text()

NINE = [
    ("I smell gas in the kitchen", "ESCALATE"),
    ("I am locked out of my apartment", "ESCALATE"),
    ("There is smoke coming from the outlet", "ESCALATE"),
    ("Water is coming through the ceiling", "ESCALATE"),
    ("My sink is leaking", "VENDOR"),
    ("The toilet is clogged", "VENDOR"),
    ("The light switch in the hall is broken", "VENDOR"),
    ("When is trash day?", "ANSWER"),
    ("What are the quiet hours?", "ANSWER"),
]


def make_db(messages):
    db = sqlite3.connect(":memory:")
    db.executescript(SQL)
    db.executemany("INSERT INTO requests (message) VALUES (?)", [(m,) for m in messages])
    return db


class DeclarativeTriageTests(unittest.TestCase):
    def test_nine_requests_route_as_expected(self):
        db = make_db([m for m, _ in NINE])
        rows = db.execute("SELECT message, route FROM triage_result").fetchall()
        self.assertEqual(dict(rows), dict(NINE))

    def test_counts_view(self):
        db = make_db([m for m, _ in NINE])
        counts = dict(db.execute("SELECT route, total FROM route_counts").fetchall())
        self.assertEqual(counts, {"ANSWER": 2, "VENDOR": 3, "ESCALATE": 4})

    def test_priority_picks_safety_over_vendor(self):
        db = make_db(["smoke from the outlet"])
        row = db.execute("SELECT route, urgency FROM triage_result").fetchone()
        self.assertEqual(row, ("ESCALATE", 10))

    def test_bad_route_is_rejected_by_the_database(self):
        db = make_db([])
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO rules (priority, keyword, route, urgency) "
                       "VALUES (9, 'x', 'MAYBE', 1)")


if __name__ == "__main__":
    unittest.main()
