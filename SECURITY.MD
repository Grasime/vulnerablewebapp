# Security Measures — SecureBank

## Authentication
- Passwords hashed using Werkzeug's `generate_password_hash` (scrypt algorithm), never stored in plaintext
- Per-password random salt (handled automatically by scrypt/Werkzeug)
- JWT-based stateless authentication via Flask-JWT-Extended
- JWT secret key loaded from environment variable (.env), never hardcoded in source

## Database
- SQLAlchemy ORM used throughout — all queries parameterized, preventing SQL injection
- Foreign key constraints enforce referential integrity (Account.user_id → User.id)
- Unique constraints on username and email at the database level

## Secrets Management
- .env file excluded from git via .gitignore
- .env file excluded from Docker builds via .dockerignore

## Containerization
- Multi-stage dependency install ordering for build efficiency
- .dockerignore excludes venv, instance/ (local DB), and .git from image builds

## Business Logic
- Account created atomically alongside User at registration (no orphaned users without accounts)
- Balance stored as integer (pence) to avoid floating-point rounding errors in financial calculations

## SAST Findings (Bandit)
- B201 (debug=True): Fixed — debug mode now controlled via FLASK_DEBUG environment variable, defaults to False (fail-safe)
- B104 (binding to 0.0.0.0): Reviewed, accepted — required for the app to be reachable from outside its Docker container; not a concern in this deployment context

## SAST Findings (Bandit)
- B201 (debug=True): Fixed — debug mode now controlled via FLASK_DEBUG environment variable, defaults to False (fail-safe)
- B104 (binding to 0.0.0.0): Reviewed, suppressed inline (# nosec B104) with justification — required for the app to be reachable from outside its Docker container; not a concern in this deployment context
- Bandit integrated into CI pipeline (.github/workflows/security.yml) — runs on every push/PR to main, fails the build on any unreviewed finding

## SAST Findings (Semgrep)
- python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host: Same underlying issue as Bandit B104, suppressed inline (# nosemgrep) with justification — required for Docker container networking
- Semgrep (p/security-audit ruleset) integrated into CI pipeline — runs on every push/PR to main

## Container Image Scanning (Trivy)
- `trivy image securebank`: 22 findings (19 HIGH, 3 CRITICAL), all in Debian OS-level packages from the python:3.12-slim base image (bsdutils, gzip, perl-base, util-linux, ncurses, etc.)
- None have a fixed version currently available upstream (Debian maintainers have not yet shipped patches)
- Reviewed and accepted: none of these packages are invoked by application code; attack surface is not exposed through the app's functionality
- Will be re-evaluated on future image rebuilds as upstream patches become available

## CI/CD Pipeline
Automated security pipeline runs on every push/PR to main (.github/workflows/security.yml):
1. Dependency installation
2. Bandit (Python SAST)
3. Semgrep (multi-language SAST, security-audit ruleset)
4. Docker image build
5. Trivy filesystem scan (dependency CVEs)
6. Trivy container image scan (OS-level CVEs in base image)

All findings reviewed and either fixed or explicitly documented/suppressed with justification (see above).

## Race Condition Protection
- SELECT ... FOR UPDATE applied to both sender_account and recipient_account queries in /transfer, locking rows for the duration of the transaction
- Note: SQLite does not support true row-level locking (locks at whole-database-file granularity). This still serializes concurrent transfer attempts and prevents the double-spend race condition, but a production deployment would use PostgreSQL for proper row-level locking granularity
- Only Account rows require locking (only table mutated during a transfer); User rows are read-only in this route

## Input Validation & Information Disclosure
- /register validates presence of username, password, email; rejects requests with missing/empty fields
- Minimum password length of 8 characters enforced at registration
- /login returns identical error message and status code (401, "Invalid username or password") for both nonexistent usernames and incorrect passwords — prevents username enumeration (CWE-203)
- Verified via manual testing: confirmed byte-identical responses for both failure paths