-- DECLARATIVE layer: tables with constraints, and views that declare the results we want.
PRAGMA foreign_keys = ON;

CREATE TABLE landlords (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email TEXT NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%')
);

CREATE TABLE properties (
    id          INTEGER PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES landlords(id),
    address     TEXT NOT NULL UNIQUE
);

CREATE TABLE tenants (
    id          INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    name        TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email       TEXT NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%')
);

CREATE TABLE vendors (
    id          INTEGER PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES landlords(id),
    name        TEXT NOT NULL,
    trade       TEXT NOT NULL CHECK (trade IN ('plumber','electrician','hvac','appliance','pest')),
    phone       TEXT NOT NULL
);

CREATE TABLE faq (
    id          INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL
);

CREATE TABLE requests (
    id             INTEGER PRIMARY KEY,
    tenant_id      INTEGER NOT NULL REFERENCES tenants(id),
    property_id    INTEGER NOT NULL REFERENCES properties(id),
    message        TEXT NOT NULL CHECK (length(message) BETWEEN 5 AND 1000),
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    category       TEXT NOT NULL CHECK (category IN
                   ('plumbing','electrical','heating','appliance','pests','lockout','safety','noise','question')),
    confidence     REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    urgency        INTEGER NOT NULL CHECK (urgency BETWEEN 0 AND 10),
    route          TEXT NOT NULL CHECK (route IN ('ANSWER','VENDOR','ESCALATE')),
    reason         TEXT NOT NULL,
    vendor_name    TEXT,
    vendor_phone   TEXT,
    answer_text    TEXT,
    status         TEXT NOT NULL CHECK (status IN
                   ('NEW','TRIAGED','ANSWERED','REFERRED','ESCALATED','REVIEWED')),
    landlord_route TEXT CHECK (landlord_route IN ('ANSWER','VENDOR','ESCALATE')),
    reviewed_at    TEXT,
    -- a request is reviewed exactly when the landlord's route is filled in
    CHECK ((landlord_route IS NULL) = (reviewed_at IS NULL))
);

CREATE TABLE audit_log (
    id         INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    step       INTEGER NOT NULL CHECK (step BETWEEN 1 AND 10),
    step_name  TEXT NOT NULL,
    detail     TEXT NOT NULL
);

-- Every request with the names a dashboard needs.
CREATE VIEW request_details AS
SELECT r.*, t.name AS tenant_name, p.address AS property_address, p.landlord_id AS landlord_id
FROM requests r
JOIN tenants t    ON t.id = r.tenant_id
JOIN properties p ON p.id = r.property_id;

-- What the landlord still has to look at: not an FAQ answer, not yet reviewed.
-- Most urgent first, then oldest first.
CREATE VIEW landlord_queue AS
SELECT * FROM request_details
WHERE route <> 'ANSWER' AND reviewed_at IS NULL
ORDER BY urgency DESC, created_at ASC, id ASC;

-- Requests per route, per landlord.
CREATE VIEW request_stats AS
SELECT landlord_id, route, COUNT(*) AS total
FROM request_details
GROUP BY landlord_id, route;

-- How often the landlord agreed with the AI.
CREATE VIEW ai_agreement AS
SELECT landlord_id,
       COUNT(*) AS reviewed,
       SUM(CASE WHEN landlord_route = route THEN 1 ELSE 0 END) AS agreed,
       ROUND(100.0 * SUM(CASE WHEN landlord_route = route THEN 1 ELSE 0 END) / COUNT(*), 1) AS agreement_pct
FROM request_details
WHERE reviewed_at IS NOT NULL
GROUP BY landlord_id;
