# SecureBank

*To be vulnerable... or not to be.*

Built as a hands-on way to actually learn AppSec, instead of just working through courses. This is a small banking API (no UI, cURL/Postman only) with two branches telling one story.

* **`main`** is a secure-by-design build: hashed passwords, JWT auth, transfer logic I manually tested for IDOR, row-level locking, and a CI/CD pipeline running Bandit, Semgrep, and Trivy on every push.
* **`vulnerable-version`** is the same app with two real vulnerabilities put back in on purpose. I wanted to answer a question I genuinely didn't know going in: would my own pipeline actually catch them?

Spoiler: one, yes. One, no. See [PR #1](https://github.com/Grasime/vulnerablewebapp/pull/1) and [SECURITY.md](./SECURITY.md) for the full breakdown.

## Tech Stack

* **Language & Framework**: Python 3.12, Flask
* **Database & ORM**: SQLite, SQLAlchemy (Flask-SQLAlchemy)
* **Authentication**: JWT-based stateless auth via Flask-JWT-Extended. Passwords hashed with Werkzeug's `generate_password_hash` (scrypt).
* **Containerization**: Docker (`python:3.12-slim` base image)
* **Secrets Management**: python-dotenv, environment-based configuration
* **CI/CD**: GitHub Actions
* **Security Tooling**:
  * [Bandit](https://bandit.readthedocs.io/) for Python SAST
  * [Semgrep](https://semgrep.dev/) for multi-language SAST (security-audit ruleset)
  * [Trivy](https://trivy.dev/) for dependency and container image vulnerability scanning

## Features

* **User registration**, with input validation and a minimum password length
* **Login**, returns a signed JWT on success. Invalid usernames and incorrect passwords get identical error responses, so the app doesn't leak which usernames exist.
* **Profile**, view your own account details through a JWT-protected route
* **Balance**, view your account balance (stored internally as integer pence so floating-point rounding never becomes a problem)
* **Transfer**, send money to another user:
  * Sender identity always comes from the verified JWT, never from the request body. I tested this against IDOR myself.
  * Amount has to be positive and the sender needs sufficient funds
  * Row-level locking (`SELECT ... FOR UPDATE`) to cut down on race conditions when transfers happen concurrently
  * Every transfer gets logged as a full transaction record

## Security Highlights

Full ongoing log of controls, findings, and decisions is in [SECURITY.md](./SECURITY.md). Short version:

* Every database query goes through the SQLAlchemy ORM. No raw string-built SQL on `main`.
* Passwords hashed with scrypt, never stored or logged in plaintext
* JWT secret loaded from environment variables, never committed to source
* IDOR protection manually verified: I crafted a request with a spoofed `sender` field and confirmed via direct database inspection that the server ignored it completely, using only the JWT-verified identity
* CI pipeline runs Bandit, Semgrep, and Trivy on every push and pull request to `main`

## The Vulnerable Branch: What I Actually Found

On `vulnerable-version` I put two real vulnerabilities back in, to see if my own CI pipeline would catch them.

| Vulnerability | Bandit | Semgrep | Notes |
|---|---|---|---|
| SQL injection in `/login` (raw f-string query) | Caught (`B608`) | Missed | Confirmed exploitable. Bypassed authentication with `' OR '1'='1' --` and got a valid JWT with no correct password. |
| Hardcoded weak JWT secret (`"secret"`) | Missed | Missed | Confirmed exploitable. Forged a fully valid JWT for any user ID entirely offline, with zero interaction with `/login`. |

Full details, payloads, and reasoning are in [SECURITY.md](./SECURITY.md). The PR is intentionally left open and unmerged, as a permanent artifact: [github.com/Grasime/vulnerablewebapp/pull/1](https://github.com/Grasime/vulnerablewebapp/pull/1)

This ended up being the most valuable part of the project. Automated SAST tooling has real, meaningful blind spots even for textbook vulnerabilities. A green pipeline isn't proof of security on its own, it still needs manual review and actually trying to break your own stuff.

## Running Locally

```bash
git clone git@github.com:Grasime/vulnerablewebapp.git
cd vulnerablewebapp

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# create a .env file with:
# JWT_SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
# FLASK_DEBUG=True

python3 app.py
```

Or with Docker:

```bash
docker build -t securebank .
docker run -p 5000:5000 --env-file .env securebank
```

## API Overview

| Method | Route | Auth Required | Description |
|---|---|---|---|
| POST | `/register` | No | Create a new user + account |
| POST | `/login` | No | Authenticate, receive a JWT |
| GET | `/profile` | Yes | View your username/email |
| GET | `/profile/balance` | Yes | View your account balance |
| POST | `/transfer` | Yes | Send money to another user |

Example:
```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123", "email": "alice@example.com"}'
```

## Project Structure

```
securebank/
├── app.py                          # Routes and application logic
├── models.py                       # SQLAlchemy models (User, Account, Transaction)
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── SECURITY.md                     # Full security documentation and findings log
└── .github/workflows/security.yml  # CI pipeline: Bandit, Semgrep, Trivy
```

## Roadmap

* [ ] Rate limiting on `/login` (brute-force protection)
* [ ] PostgreSQL migration for true row-level locking
* [ ] More deliberately-introduced vulnerabilities (IDOR variants, XSS, SSRF)
* [ ] Terraform/AWS deployment

