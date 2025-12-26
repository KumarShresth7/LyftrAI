# Lyftr AI Backend Assignment

A containerized FastAPI service for ingesting "WhatsApp-like" messages with HMAC validation, idempotency, and analytics.

## How to Run

1. **Start the Stack**:
   ```bash
   make up
   # or: docker compose up -d --build

The API will be available at http://localhost:8000.

Check Logs:

Bash

make logs
Stop:

Bash

make down
Endpoints
POST /webhook: Accepts message JSON. Requires X-Signature header (HMAC-SHA256).

GET /messages: List messages with pagination (limit, offset) and filtering (from, since, q).

GET /stats: Returns analytics (top senders, counts).

GET /metrics: Prometheus metrics.

GET /health/live & /health/ready: Kubernetes-style probes.

Design Decisions
HMAC Verification: implemented as a FastAPI dependency (verify_signature). It reads the raw request body bytes to compute the SHA256 HMAC and compares it to the X-Signature header using hmac.compare_digest to prevent timing attacks.

Idempotency: Relies on the database layer. The message_id is the PRIMARY KEY. A try/except IntegrityError block catches duplicate inserts, logs them as result="duplicate", but returns HTTP 200 as required.

Pagination: Uses limit and offset. The response includes a meta object with the total count (calculated via a separate count query respecting current filters) to allow frontend clients to build paginators.

Stats: Implemented using SQL aggregations (SQLAlchemy func.count) for efficiency rather than loading all rows into Python.

Setup Used
Antigravity
