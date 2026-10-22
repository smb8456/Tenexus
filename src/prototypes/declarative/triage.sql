-- Prototype 4 - DECLARATIVE paradigm (SQL / SQLite).
-- Same problem: answer, send to a vendor, or escalate.
-- We do not write steps. We store the rules as DATA and DECLARE the result
-- we want as a view. SQLite decides how to compute it.

CREATE TABLE rules (
    id       INTEGER PRIMARY KEY,
    priority INTEGER NOT NULL,                       -- lower number = checked first
    keyword  TEXT    NOT NULL,
    route    TEXT    NOT NULL CHECK (route IN ('ANSWER', 'VENDOR', 'ESCALATE')),
    urgency  INTEGER NOT NULL CHECK (urgency BETWEEN 0 AND 10),
    detail   TEXT
);

CREATE TABLE requests (
    id      INTEGER PRIMARY KEY,
    message TEXT NOT NULL
);

INSERT INTO rules (priority, keyword, route, urgency, detail) VALUES
    (1, 'gas',            'ESCALATE', 10, 'safety keyword'),
    (1, 'smoke',          'ESCALATE', 10, 'safety keyword'),
    (1, 'fire',           'ESCALATE', 10, 'safety keyword'),
    (1, 'spark',          'ESCALATE', 10, 'safety keyword'),
    (1, 'carbon monoxide','ESCALATE', 10, 'safety keyword'),
    (2, 'locked out',     'ESCALATE',  8, 'lockout'),
    (2, 'lockout',        'ESCALATE',  8, 'lockout'),
    (2, 'lost my key',    'ESCALATE',  8, 'lockout'),
    (3, 'trash',          'ANSWER',    1, 'Trash and recycling go out Tuesday night.'),
    (3, 'garbage',        'ANSWER',    1, 'Trash and recycling go out Tuesday night.'),
    (3, 'recycling',      'ANSWER',    1, 'Trash and recycling go out Tuesday night.'),
    (3, 'quiet hours',    'ANSWER',    1, 'Quiet hours are 10 pm to 7 am.'),
    (3, 'noise',          'ANSWER',    1, 'Quiet hours are 10 pm to 7 am.'),
    (4, 'leak',           'VENDOR',    5, 'Liberty Plumbing'),
    (4, 'clog',           'VENDOR',    5, 'Liberty Plumbing'),
    (4, 'toilet',         'VENDOR',    5, 'Liberty Plumbing'),
    (4, 'drain',          'VENDOR',    5, 'Liberty Plumbing'),
    (4, 'light',          'VENDOR',    5, 'Brightside Electric'),
    (4, 'outlet',         'VENDOR',    5, 'Brightside Electric'),
    (4, 'switch',         'VENDOR',    5, 'Brightside Electric'),
    (4, 'breaker',        'VENDOR',    5, 'Brightside Electric');

-- The declared result: for every request, the best matching rule
-- (lowest priority number); if nothing matches, ESCALATE.
CREATE VIEW triage_result AS
SELECT r.id,
       r.message,
       COALESCE(m.route,   'ESCALATE')                         AS route,
       COALESCE(m.urgency, 5)                                  AS urgency,
       COALESCE(m.detail,  'no rule matched - landlord decides') AS detail
FROM requests r
LEFT JOIN rules m
       ON m.id = (SELECT ru.id
                  FROM rules ru
                  WHERE lower(r.message) LIKE '%' || ru.keyword || '%'
                  ORDER BY ru.priority, ru.id
                  LIMIT 1);

-- A second declared result: how many requests per route.
CREATE VIEW route_counts AS
SELECT route, COUNT(*) AS total
FROM triage_result
GROUP BY route;
