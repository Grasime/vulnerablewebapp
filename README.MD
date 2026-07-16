# SecureBank

*To be vulnerable... or not to be.*

Built as a hands-on way to actually learn AppSec, rather than just consuming courses — this is a small banking API (no UI, cURL/Postman only) with two branches telling one story:

- **`main`** — a secure-by-design build: hashed passwords, JWT auth, IDOR-tested transfer logic, row-level locking, and a CI/CD pipeline running Bandit, Semgrep, and Trivy on every push.
- **`vulnerable-version`** — the same app with two real vulnerabilities deliberately reintroduced, to answer a question I didn't know the answer to going in: *would my own pipeline catch them?*

(Spoiler: one, yes. One, no. See [PR #1](https://github.com/Grasime/vulnerablewebapp/pull/1) and [SECURITY.md](./SECURITY.md) for the full breakdown.)

## Tech Stack

- **Language & Framework**: Python 3.12, Flask
- **Database & ORM**: SQLite, SQLAlchemy (Flask-SQLAlchemy)
- **Authentication**: JWT-based stateless auth via Flask-JWT-Extended; passwords hashed with Werkzeug's `generate_password_hash` (scrypt)
- **Containerization**: Docker (`python:3.12-slim` base image)
- **Secrets Management**: python-dotenv, environment-based configuration
- **CI/CD**: GitHub Actions
- **Security Tooling**:
  - [Bandit](https://bandit.readthedocs.io/) — Python SAST
  - [Semgrep](https://semgrep.dev/) — multi-language SAST (security-audit ruleset)
  - [Trivy](https://trivy.dev/) — dependency & container image vulnerability scanning

## Features

- **User registration** — with input validation and minimum password length enforcement
- **Login** — returns a signed JWT on success; identical error responses for invalid usernames and incorrect passwords (prevents username enumeration)
- **Profile** — view your own account details via a JWT-protected route
- **Balance** — view your account balance (stored internally as integer pence to avoid floating-point rounding errors)
- **Transfer** — send money to another user, with:
  - Sender identity always derived from the verified JWT, never from the request body (IDOR-tested)
  - Positive-amount and sufficient-funds validation
  - Row-level locking (`SELECT ... FOR UPDATE`) to mitigate race conditions on concurrent transfers
  - A full transaction audit trail

## Security Highlights

See [SECURITY.md](./SECURITY.md) for the complete, ongoing log of controls, findings, and decisions. Highlights:

- Every database query goes through the SQLAlchemy ORM — no raw string-built SQL on `main`
- Passwords hashed with scrypt, never stored or logged in plaintext
- JWT secret loaded from environment variables, never committed to source
- Manually verified IDOR protection: crafted a request with a spoofed `sender` field and confirmed via direct database inspection that the server ignored it entirely, using only the JWT-verified identity
- CI pipeline runs Bandit, Semgrep, and Trivy on every push and pull request to `main`

## The Vulnerable Branch — What I Actually Found

On `vulnerable-version`, I deliberately reintroduced two real vulnerabilities to test whether my own CI pipeline would catch them:

| Vulnerability | Bandit | Semgrep | Notes |
|---|---|---|---|
| SQL injection in `/login` (raw f-string query) | ✅ Caught (`B608`) | ❌ Missed | Confirmed exploitable — bypassed authentication with `' OR '1'='1' --` and obtained a valid JWT with no correct password |
| Hardcoded weak JWT secret (`"secret"`) | ❌ Missed | ❌ Missed | Confirmed exploitable — forged a fully valid JWT for any user ID entirely offline, with zero interaction with `/login` |

**Full details, payloads, and reasoning in [SECURITY.md](./SECURITY.md).** The PR is intentionally left open, unmerged, as a permanent artifact: [github.com/Grasime/vulnerablewebapp/pull/1](https://github.com/Grasime/vulnerablewebapp/pull/1)

This was the most valuable part of the project — proof that automated SAST tooling has real, meaningful blind spots even for textbook vulnerabilities, and that it has to be paired with manual review and testing, not relied on alone.

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

Or via Docker:

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

- [ ] Rate limiting on `/login` (brute-force protection)
- [ ] PostgreSQL migration for true row-level locking
- [ ] Additional deliberately-introduced vulnerabilities (IDOR variants, XSS, SSRF)
- [ ] Terraform/AWS deployment
