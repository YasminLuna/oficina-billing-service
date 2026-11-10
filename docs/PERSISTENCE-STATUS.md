# Billing SQL persistence

The prototype includes a transactional SQLite repository with atomic quote state
transitions and tests. The FastAPI endpoints still use their original in-memory
store. **Do not deploy this as a production-ready billing system.**

Required before deployment:
- PostgreSQL implementation, schema migration and connection management.
- Wire repository into FastAPI dependency injection.
- Persist payments, webhook events and idempotency keys.
- Mercado Pago payment verification, webhook authentication and retries.
- Transactional outbox and distributed Saga compensation.
- Service-to-service authorization and OpenTelemetry.
