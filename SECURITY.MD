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