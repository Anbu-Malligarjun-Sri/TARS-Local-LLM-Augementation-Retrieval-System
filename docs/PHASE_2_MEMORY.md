# Phase 2: using personal memory

The local Phase 2 path works without a model or a database service. PostgreSQL,
pgvector and Neo4j deployment adapters are provided but have not been exercised
against live services in this environment: Docker's engine is not running.

## Start and use

Use the Phase 1 pairing/startup process. The default `MEMORY_BACKEND=sql` uses
`.runtime/memory.sqlite3`. On first engine initialization it snapshots and imports
legacy JSON. Source files and the Chroma science/character index are left intact.
The current repository snapshot imported 25 files / 119 messages successfully.

Open **Personal memory** in the left sidebar. Add a subject, relationship and
value, for example `Me → works_on → TARS`. Or type:

```text
/remember My mother | prefers | respectful warm replies
```

This is an explicit owner assertion, not an independently verified fact.
Automatic extraction of arbitrary conversation statements is intentionally not
enabled. No fine-tuning or provider session is required. The next relevant turn,
in any conversation/model using the runtime, retrieves that claim and its source.
The same context code is used by streaming and non-streaming calls.

The UI supports search, source inspection, correction, forgetting, export and
relationship inspection. Graph inspection shows directed edges and nodes as a
table. It is not a graphical canvas. Correcting supersedes the old claim; forgetting
redacts the full correction chain and assertion sources and deletes local indexes.
Conversation transcripts have separate retention and may still contain the fact.
Backups, exported files and original JSON snapshots also remain until separately
expired. This implements logical deletion, not forensic erasure of storage media.

## Privacy and retrieval

Memories default to owner-only/private and local-only. API callers cannot supply
a principal. Future non-owner channels must pass a separately authenticated
principal/audience to the repository. The shared runtime applies filtering before
ranking and graph traversal. There is no phone/caller memory endpoint yet.

With `ALLOW_CLOUD=true`, only memories whose cloud permission is enabled are
retrieved, even if the initial model is local (a fallback might reach cloud).
A conversation used in SQL local-only mode is marked local-only; switching that
session to cloud-capable routing is rejected to avoid leaking old context through
its transcript. Start a new conversation or continue locally. These flags govern
personal-memory context; explicitly enabling cloud still permits ordinary new
user messages/history to reach the configured cloud provider.

Offline retrieval uses exact terms, bounded relationship expansion and versioned
hashed word vectors (`lexical-sha256-v1`, 128 dimensions). These vectors are **not
semantic embeddings**. Set `MEMORY_EMBEDDINGS=lm_studio` for the configured semantic
embedding model, then rebuild. Query/document task prefixes are handled separately.
Changing models or dimensions requires rebuilding; mismatched vectors are ignored.
If embeddings are offline, keyword/graph retrieval still works and rebuild reports
an error without deleting canonical facts. The UI displays projection lag/model.

## Data and migration

Canonical tables hold owner-scoped conversations/messages, sourced claims,
assertion events, an import manifest and a transactional projection outbox. Local
edge/vector tables are derived. Projection writes recheck active claim state so a
concurrent forget cannot resurrect a memory. Reads always join/filter against
canonical claims; an old projection is never authorization evidence.

Legacy IDs become stable UUIDs and retain `legacy_id`. Hashes prevent silent
reimport of edited originals. Re-running an unchanged import is a no-op, including
after a conversation was cleared. Corrupt input/collisions roll back the import.
Legacy message order and original timestamp metadata are retained; timezone-less
historical creation timestamps use a documented UTC assumption, since the original
files do not record a timezone. This preserves ordering, not guaranteed historical
wall-clock accuracy. New timestamps are UTC-aware. SQL history is untrimmed; model
context remains bounded to recent turns and a limited memory context budget.

Useful commands from the repository root:

```powershell
python -m src.memory.manage import
python -m src.memory.manage status
python -m src.memory.manage rebuild
python -m src.memory.manage backup --destination .runtime/backups/manual.sqlite3
```

Backup paths must be new; existing backups are never overwritten. Stop the server
before restoring a tested backup to `MEMORY_DB_PATH`. SQLite online backups use its
backup API. For PostgreSQL, use `pg_dump`/restore in the deployment's operational
process. Test restoration in a separate location before replacing live state.
To roll back to original JSON, set `MEMORY_BACKEND=legacy` and restart. SQL-era
turns will remain in SQL; they are not automatically copied back into old JSON.
The authentication/settings foundation database remains separate. Continue using
one API process: turn locks, auth throttles and cancellation are process-local.

## Optional external deployment

Install `requirements-memory.txt` in a compatible environment. Set strong
`TARS_POSTGRES_PASSWORD` and `TARS_NEO4J_PASSWORD` environment variables before
`docker compose -f compose.memory.yaml up -d`. No services are started by this
implementation. Both are bound to loopback and use persistent dedicated volumes.

Set `MEMORY_DATABASE_URL` to the PostgreSQL connection string to use PostgreSQL
as canonical storage; this creates schema version 1 and imports legacy files.
**It does not migrate new SQLite-era claims/messages.** Export/back up existing
SQLite state and plan that migration before switching an active installation.
Never treat backend selection as a data-copy operation.

Neo4j/pgvector mirrors are explicit operator exports, not live runtime dependencies.
Set `MEMORY_NEO4J_URI`, `MEMORY_NEO4J_USER`, `MEMORY_NEO4J_PASSWORD`, or
`MEMORY_PGVECTOR_URL` as appropriate, then run:

```powershell
python -m src.memory.mirror neo4j
python -m src.memory.mirror pgvector
```

Use dedicated databases. Neo4j export atomically replaces only `TarsMemory` nodes
for the owner. pgvector export replaces that owner's rows and tags model/dimension.
These external snapshots contain private data and remain until re-exported or
removed; the runtime neither queries them nor promises immediate deletion there.
Local outbox lag describes local projections only. Continuous external projection
sync, pgvector-native search benchmarking, live-service migration/restore drills
and graph-canvas UI remain follow-up integration work.

The adapter APIs follow the official [Psycopg transaction documentation](https://www.psycopg.org/psycopg3/docs/basic/transactions.html),
[Neo4j managed transaction documentation](https://neo4j.com/docs/python-manual/current/transactions/)
and [pgvector reference](https://github.com/pgvector/pgvector).

## Verification scope

Tests cover restart/model-independent context, correction/forget, audience and
cloud isolation, migration idempotency, corrupt inputs, backups, concurrent append,
projection failure/deletion races and authenticated CRUD. Models are fakes; no
claim of live semantic quality or identical model personality is made. The original
50-scenario recall/quality benchmark and external service gates remain pending.
