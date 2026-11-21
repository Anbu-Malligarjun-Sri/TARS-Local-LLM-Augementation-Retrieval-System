# Phase 2: durable shared memory

Status: local units 05–08 implemented and tested. Full Phase 2 remains in progress pending external-service and live-quality gates.

## Goal

Persist complete conversations, source-linked owner claims and relationships outside model weights. Import legacy JSON once without modifying originals; inspect, correct, forget, export and retrieve memories through authenticated APIs/UI and every model adapter.

## Design and decisions

Use a transactional repository with SQLite as the zero-service desktop default and PostgreSQL as an optional deployment backend. Docker daemon is unavailable in this environment. Keep SQL relationship/vector projections rebuildable from claims through an outbox; provide optional external Neo4j and pgvector projection adapters. Do not claim external integration verification without running those services. Existing Chroma science/character knowledge remains separate.

Only explicit owner-authored structured memories are verified. No automatic model-generated facts or policies are promoted. Every claim has a source event, owner, validity, sensitivity, audience and supersession state. Local lexical vectors are a degraded retrieval fallback, explicitly labeled; optional LM Studio embeddings enable semantic retrieval. Privacy filters run before ranking and context assembly.

## Implementation

1. Schema versioning, owner-scoped repository, transactional conversation messages, stable legacy UUID mappings and hash-checked idempotent import. Snapshot source JSON before import. Verify counts before enabling SQL history; preserve originals.
2. Source events and claims: add, inspect, correct with supersession, forget including source redaction and derived deletion. Owner-only defaults; cloud disclosure requires per-claim opt-in as well as global provider opt-in.
3. Outbox and reproducible graph/vector projections; authorized bounded hybrid retrieval. Fall back to canonical data if a projection is stale. Build context for all providers, with fact/source IDs. Keep personal facts out of model weights.
4. Authenticated memory management UI and APIs, graph inspection, backup/export and restore verification.

## Verification

Test repeat import, corrupt/changed files, untrimmed history, concurrent writes, owner/audience/cloud isolation, correction, forget, rebuild, backup restoration, provider-independent prompt context and API auth. Run existing backend tests and frontend test/typecheck/lint/build. External services and live embedding tests are opt-in.

## Rollback

Set MEMORY_BACKEND=legacy before restarting to use untouched JSON originals (new SQL-era turns will not appear there). Export/backup SQL before rollback. Do not delete the SQL database or source snapshots. Backups contain private data and forgotten material until explicitly expired; the UI describes this limit.
