# Kan Piao DB Session Hotfix Validation

**Date:** 2026-07-30  
**Implementation:** `COMPLETE`  
**Production deployment:** `NOT AUTHORIZED / NOT PERFORMED`

## Target Boundary

The Finance Suite Git repository does not contain the production FastAPI backend. The patch therefore targets the exact read-only production snapshot from:

```text
/home/ubuntu/finance-suite-web/app/auth.py
SHA-256: d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804

/home/ubuntu/finance-suite-web/app/routers/api.py
SHA-256: 2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889
```

`production_backend.patch` followed by `pool_lifecycle_instrumentation.patch` was checked and applied against those exact files. The resulting files byte-match the isolated test candidate.

## Implemented Behavior

1. Authentication opens and closes its own short `SessionLocal` scope before route execution.
2. The detached `User` retains the scalar identity/tier fields needed by consumers.
3. `/api/analyze` no longer receives a request-scoped DB dependency.
4. Quota read and usage write each use an independent short session.
5. SQLAlchemy pool timeout becomes HTTP 503 with `Retry-After: 5`, not an opaque HTTP 500.
6. Per-request, non-PII pool observations record quota release, the LLM boundary and usage-write release.
7. Provider, search, LLM, QC and Trust behavior are unchanged.
8. Pool sizing and Provider fallback order are unchanged.

## Verification

Executed against an isolated copy of the production backend with a temporary SQLite database and a deliberately constrained `QueuePool(pool_size=1, max_overflow=0)`:

```text
6 passed
```

Covered assertions:

- Auth connection returns before route work.
- Forced auth pool exhaustion returns explicit HTTP 503.
- Quota read and usage write return connections to the pool.
- Forced quota-read pool exhaustion returns explicit HTTP 503.
- 36 concurrent simulated requests can perform the short DB prefix and wait externally without retaining DB connections.
- The `analyze` signature contains no request-scoped `db` dependency.

Candidate SHA-256 after both patches:

```text
app/auth.py
62d75b5d2bc0b1818ead5f93054cbc77bc8df080690723eb0518fe583e7389cf

app/routers/api.py
07f69b005db54dab00813cf0c2e9be7156a14d2dc07811dfc208d9cca3a3dfb8
```

The eight warnings are existing `datetime.utcnow()` deprecation warnings and are outside this incident fix.

## Remaining Deployment Gate

Before production application:

1. Reconfirm both target SHA-256 hashes.
2. Back up both target files with timestamp and checksum.
3. Apply the patch to a staging copy and run the included tests with production dependencies.
4. Run authenticated stock-analysis smoke for golden inputs.
5. Define worker restart, health check, connection-count observation and rollback commands.
6. Obtain explicit production deployment authorization.

No production file, configuration, database, process or service was changed in this window.
