# Research Runtime Governance Principles v0.1

**Status:** `DEFINED`  
**Scope:** Runtime resource ownership and failure expression  
**Capability effect:** `NONE`  
**Production capability:** `NOT CLAIMED`

## Principle RR-01

```text
Long-running research tasks must not own transactional resources.
```

Provider retrieval, Search, LLM generation, agent execution and backtesting may be long-running. They must not retain a DB connection, open transaction, quota lock or equivalent transactional resource while waiting on external or unbounded work.

## Required Runtime Shape

```text
authenticate
  -> checkout
  -> verify
  -> release

quota admission
  -> checkout / lock
  -> decide
  -> release

Provider / Search / LLM / Agent / Backtest
  -> no transactional resource ownership

result accounting
  -> checkout / lock
  -> commit or rollback
  -> release
```

## Admission Gate

Every new or changed long-running consumer, including Gildata, Wind, Choice, iFinD, LLM agents and backtest engines, must answer:

1. Which transactional resources can the task acquire?
2. At what exact boundary are they released?
3. Can Provider latency, retries or LLM latency extend ownership?
4. Are success, timeout, exception and cancellation cleanup proven?
5. Can checkout/checkin or lock acquisition/release be observed without exposing credentials or user data?
6. Does resource exhaustion produce an explicit degraded state rather than healthy-looking empty output?

If a long-running phase retains a transactional resource, design admission is `REJECTED` until the ownership boundary is shortened or an explicitly reviewed isolation mechanism exists.

## Evidence Rule

```text
Static finally/close path
  != runtime release proof

Process restart
  != root-cause proof

HTTP 200
  != resource-lifecycle proof

Disk instrumentation
  != active runtime instrumentation
```

Runtime acceptance requires traceable acquisition and release evidence for success, timeout, exception and cancellation. Evidence must distinguish the source file on disk from the code loaded by live workers.

## Failure Expression

Resource exhaustion must be expressed as an explicit service-degraded or unavailable state. It must not be converted into synthetic evidence, an empty healthy result, a Provider capability claim or a Trust Gate bypass.

## Origin And Boundary

RR-01 was extracted from the 2026-07-30 看票分析 incident. The incident currently provides confirmed code-level evidence and partial runtime evidence; Stage A instrumentation activation is still pending a low-traffic restart window. Defining this governance principle does not prove that the incident is remediated or that any Provider is production capable.
