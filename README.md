# Tenexus

**The trusted link between landlords and tenants.**

Tenexus is a CMPSC 460 programming languages project that demonstrates an AI-assisted landlord–tenant maintenance request system. Tenants submit requests through a Flask web interface. The system recommends whether to answer a question, refer a maintenance issue to a vendor, or escalate the request for landlord review.

## Features

- Tenant portal for submitting and viewing maintenance requests
- Landlord dashboard for reviewing AI routing decisions
- AI-assisted request classification: `ANSWER`, `VENDOR`, or `ESCALATE`
- Landlord approval and correction of recommendations
- SQLite storage for requests, reviews, and audit history
- Four programming-paradigm prototypes and two Racket DSLs

The AI provides recommendations; uncertain or urgent requests are intended for human review. This is a course demonstration, not a production-ready property-management service.

## Technologies

Python, Flask, SQLite, HTML, CSS, Racket, uv, pytest, and RackUnit.

## Project Structure

```text
Tenexus/
├── src/
│   ├── webapp/              # Main Flask application, AI, database, and frontend
│   │   ├── app.py
│   │   ├── ai.py
│   │   ├── models.py
│   │   ├── workflow.py
│   │   ├── repository.py
│   │   ├── schema.sql
│   │   ├── templates/
│   │   ├── static/
│   │   └── tests/
│   ├── models/              # Standalone OOP coursework models
│   ├── prototypes/          # Imperative, OOP, functional, and declarative examples
│   ├── dsl/                 # KeyRules and KeyFAQ in Racket
│   └── main.py              # Standalone OOP demonstration
├── tests/                   # Coursework model and prototype tests
├── documentation/           # AI agent development notes
├── pyproject.toml
├── uv.lock
└── README.md
```

The standalone `src/models/` classes support the coursework examples. The Flask application currently uses its own models in `src/webapp/models.py`.

## Setup

Requirements: Python 3.14 or newer, [uv](https://docs.astral.sh/uv/), and Racket for the Racket exercises.

```powershell
git clone <your-repository-url>
cd Tenexus
uv sync
```

## Run the Web Application

From the repository root:

```powershell
cd src/webapp
uv run python app.py
```

Open **http://127.0.0.1:5000**. The application creates and seeds a local SQLite database if needed. Stop the server with **Ctrl+C**.

## Run Tests

From the repository root, test the coursework examples:

```powershell
uv run python -m pytest tests/ -v
```

To test the Flask application:

```powershell
cd src/webapp
uv run python -m unittest discover -s tests -v
```

## Run Other Examples

From the repository root:

```powershell
uv run python -m src.main
uv run python -m src.prototypes.imperative.workflow
uv run python -m src.prototypes.object_oriented.main
racket src/prototypes/functional/triage.rkt
racket src/dsl/DSL_1.rkt
racket src/dsl/DSL_2.rkt
```

The declarative prototype uses `src/prototypes/declarative/triage.sql` and has a Python test in the same directory.

## Programming Paradigms and DSLs

- **Imperative (Python):** Routes requests with conditions and procedural logic.
- **Object-oriented (Python):** Models properties, landlords, tenants, vendors, and requests.
- **Functional (Racket):** Uses functions to process triage rules.
- **Declarative (SQLite):** Expresses request rules using SQL.
- **KeyRules (Racket):** Defines request-routing rules.
- **KeyFAQ (Racket):** Defines approved answers to tenant FAQs.

## Limitations

This project uses demonstration data. It does not provide production authentication or secure multi-user deployment. AI classifications can be inaccurate and require human oversight. Run Flask locally for development only.

## Authors

Stevens Blantrice and Ergi Demiraj  
CMPSC 460 — Programming Languages  
Pennsylvania State University
