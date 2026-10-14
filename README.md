# Tenexus

**The trusted link between landlords and tenants.**

Tenexus is a real estate software development project for CMPSC 460. It aims to create a web application that connects landlords, tenants, and maintenance vendors while using AI to improve communication and request management.

## Project Overview

Tenexus focuses on organizing tenant maintenance requests, property information, and communication between landlords and tenants.

The main problem is determining whether a tenant request should be:

- **ANSWER:** Respond using an approved FAQ.
- **VENDOR:** Route the request to a maintenance vendor.
- **ESCALATE:** Send the request to the landlord for human review.

## Technologies

| Technology | Purpose |
|---|---|
| Python | Core application and programming prototypes |
| Racket | Functional programming and DSL development |
| SQLite | Database and declarative programming |
| Flask | Planned web application |
| HTML, CSS, JavaScript | Planned frontend |
| Bootstrap | Planned interface styling |
| uv | Python dependency management |
| pytest | Automated Python testing |
| RackUnit | Racket testing |
| Git/GitHub | Version control |

## Project Structure

```text
Tenexus/
├── src/
│   ├── models/               # Python classes
│   ├── prototypes/
│   │   ├── imperative/       # Imperative programming
│   │   └── object_oriented/  # Object-oriented programming
│   ├── agents/               # AI agent documentation
│   ├── dsl/
│   │   ├── DSL_1.rkt         # KeyRules
│   │   └── DSL_2.rkt         # KeyFAQ
│   ├── webapp/               # Planned Flask application
│   └── main.py
├── tests/                    # Automated tests
├── documentation/            # Documentation and AI agent results
├── pyproject.toml
├── uv.lock
└── README.md
```

## Installation

**Requirements:**
- Python
- uv
- Racket / DrRacket

Clone the repository:

```bash
git clone <repository-url>
cd Tenexus
```

Install Python dependencies:

```bash
uv sync
```

## Running the Project

Run the main Python program:

```bash
uv run python -m src.main
```

Run the imperative prototype:

```bash
uv run python -m src.prototypes.imperative.workflow
```

Run the object-oriented prototype:

```bash
uv run python -m src.prototypes.object_oriented.main
```

Run the Racket DSLs:

```bash
racket src/dsl/DSL_1.rkt
racket src/dsl/DSL_2.rkt
```

Run Python tests:

```bash
uv run python -m pytest
```

Run Racket tests:

```bash
raco test src/dsl/DSL_1.rkt
raco test src/dsl/DSL_2.rkt
```

## Programming Paradigms

Tenexus demonstrates four programming paradigms:

1. **Imperative:** Python request processing using variables, loops, and conditions.
2. **Object-Oriented:** Python classes representing tenants, landlords, properties, vendors, and maintenance requests.
3. **Functional:** Racket functions and immutable-data processing.
4. **Declarative:** SQLite rules and queries.

The completed application will integrate all four paradigms.

## AI Agents

Tenexus includes two AI assistants created using an AI bot platform.

**Agent 1 — Company Structuring Assistant**

Reviews departments, responsibilities, organizational structure, and development workflows.

**Agent 2 — DSL Racket Builder**

Assists with generating, reviewing, and testing Racket domain-specific languages.

Both agents require human review of their outputs.

## Racket DSLs

**DSL_1.rkt — KeyRules**

Defines maintenance request-routing rules. Emergencies are escalated, maintenance issues are routed to vendors, and unknown requests require human review.

**DSL_2.rkt — KeyFAQ**

Stores approved property-specific FAQ answers. Supports questions about trash collection and parking, with unknown questions escalated for human review.

## Development Status

**Implemented or drafted:**
- Project structure and Python environment
- Core object-oriented models
- Imperative programming prototype
- Object-oriented programming prototype
- Two AI assistants
- KeyRules and KeyFAQ DSL source code

**Remaining work:**
- Functional programming prototype
- Declarative programming prototype
- Flask web application and SQLite integration
- Tenant-facing AI classification
- Comprehensive testing and paradigm auditing
- Final integration and demonstration

## Project Goal

Develop a functional, AI-assisted landlord-tenant management application that demonstrates multiple programming paradigms, domain-specific languages, and human oversight.

## Authors

Stevens Blantrice and Ergi Demiraj

**Course:** CMPSC 460 — Programming Languages  
**Institution:** Pennsylvania State University