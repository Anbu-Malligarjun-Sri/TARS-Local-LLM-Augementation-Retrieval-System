# Architecture context

The owner turn transaction stores supported personal assertions with the source message in canonical SQL. Filtered lexical and semantic retrieval feed the selected model. The graph reads the same active claims. A trained subword language router handles Romanized Tamil. Paired media endpoints run Whisper Tiny for English, Whisper Small for Tamil, Piper for speech and YuNet/SFace for explicitly enrolled face profiles. Raw media stays in memory. [Implementation and operating limits](../docs/R1_DESKTOP_COMPANION.md)

The desktop persona resolves a reply locale from the current request before adding history, retrieved material or tool evidence. The browser microphone locale affects recognition. Sentence playback selects a matching local voice using the actual reply text. The independent `demo.api:app` R1 process serves three allowlisted static files, a multilingual scene catalogue, bounded visitor sessions and cancellable scripted SSE turns. A completed teaching turn stores one fictional nickname flag until visit expiry. Only the visitor page keeps the displayed transcript. Browser requests carry an expected visit ID to detect a changed cookie after another tab starts a new visit. It imports no owner modules and has bounded, expiring in-process credentials. [R0 release and R1 runbook](../docs/COMPANION_R0_RELEASE.md)

**Product direction · 23 November 2026.** The [companion robot master roadmap](../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

Updated 2026-11-21. Distinguish CURRENT from TARGET. Detailed rationale and audit: [architecture plan](../docs/TARS_ARCHITECTURE_PLAN.md).

## Stack

| Layer | Current | Target |
| --- | --- | --- |
| UI | React 18, Vite, TypeScript, Zustand, Tailwind, Radix/shadcn primitives | Retain; server-authoritative sessions/settings and typed events |
| Backend | FastAPI authenticated channels, per-session locks and bounded generation offload | Modular application; async or bounded offload; authenticated channels |
| Models | LM Studio, Ollama, OpenAI, legacy Gemini; failure fallback | Capability/privacy/budget router and versioned adapters |
| Memory | Transactional SQL conversations/claims and local relationship/vector projections; Chroma YAML Q&A remains separate | PostgreSQL canonical events/claims + Neo4j relationship projection + pgvector retrieval |
| Personality | Versioned per-turn audience policy/examples; isolated previews; output preserved | Versioned persona/examples and deterministic audience policy |
| Voice | Opt-in Web Speech recognition/local sentence playback; legacy CLI remains | Streaming STT/runtime/TTS; optional native audio adapter |
| Jobs | Durable SQL coding queue, leases/cancellation/artifacts | Durable Postgres jobs/outbox with worker leases |
| Phone | None | One selected carrier/media path, candidate LiveKit/SIP or Twilio Streams |
| Coding | Codex cloud CLI adapter; live sandbox provisioning blocked | Isolated Codex/Claude workers under scoped job contracts |

## System boundaries

- `src/interfaces/`: transport validation, authentication, event serialization; no long-running job execution.
- Existing `src/core/`: migration facade for current chat. Gradually extract `src/runtime/` orchestration and context building.
- Existing `src/ai/`: preserve behavior behind adapters; future `src/providers/` owns SDK specifics and capability registry.
- Future `src/memory/`: canonical claim lifecycle and bounded authorized retrieval; graph/index projections are internal details.
- `src/personality/`: expression and audience style. Permission decisions belong in future `src/policy/`.
- Future `src/tools/`: validated connectors; `src/jobs/`: durable jobs/scheduler; `src/agents/`: coding adapter execution.
- `src/voice/` and future `src/telephony/`: media and call lifecycle, both using the same runtime/policy/memory services.
- `frontend/src/services/`: API/event contracts; hooks orchestrate UI; store caches UI state rather than acting as the sole history database.
- `context/`: development context, not the user's personal-memory database.

Create future modules only when implementing their scoped unit.

## Storage model

Postgres becomes canonical for owner/contact records, conversations/messages, claims/sources, preferences, persona versions, tasks/jobs, grants, call sessions and audit/outbox events. Neo4j is a rebuildable relationship projection. pgvector is a rebuildable semantic projection with embedding model/version/dimension metadata. Raw documents/media live in private file/object storage with retention metadata; credentials live in a secret store.

Claims record source event, validity interval, sensitivity, allowed audiences, confidence/verification and supersession. Commit state + outbox atomically; project idempotently. Never make direct independent writes to three stores. Use UTC storage and explicit user timezone display.

Import existing JSON through stable UUID mappings and hashes. Preserve old files/backups. Shadow-test retrieval before retiring Chroma. Data removal includes derived indexes and cache invalidation; backups expire according to documented retention.

## Auth and access model

Target: authenticated owner and explicitly paired devices; contacts/callers are separate lower-trust principals. Bind every session, memory retrieval and tool call to a principal. Backend verifies ownership, audience access and scoped permissions. Caller ID and familiar speech are identity hints, not authorization. No browser-held provider secrets. Prefer local/private access during foundation work; explicit origins and protected WebSockets are required before remote use.

## AI and background work

The runtime builds a bounded context packet with persona version, relevant source-linked memory, current request and allowed tools. Routing applies privacy before capability/latency/cost. Tools are schema-validated and policy-checked in code. Job states are queued/running/waiting-for-approval/completed/failed/cancelled; retries use idempotency and outcome reconciliation.

Typed events include schema version, conversation/turn/message/job IDs, sequence, timestamp and payload. Shared terminal completion/error/cancel semantics serve REST, WS and voice. Do not silently restart a partially delivered response with a different model.

## Invariants

1. Personal memory and persona are independent of any model's weights or vendor conversation ID.
2. Private-only data never reaches a cloud model through fallback.
3. Retrieval and output both enforce audience/owner permissions; humor cannot grant access.
4. Retrieved text/caller claims/tool output cannot change system policy or create owner grants.
5. Every external side effect has scoped authorization, an audit record and retry semantics.
6. Graph/semantic projections derive from canonical sourced records and honor corrections/deletions.
7. Concurrent turns cannot share mutable conversation buffers or person-specific global settings.
8. Long operations do not block voice/chat event loops; workers support cancellation and time budgets.
9. TARS identifies itself as an assistant on third-party calls; factual honesty is not adjustable.
10. UI claims and task success reflect measured results, not random/static confidence or status labels.
11. User data, secrets and runtime indexes are not new source-controlled artifacts.
12. Documentation marks planned versus implemented behavior explicitly.

## Implemented Phase 1 delta (2026-11-21)

The API now authenticates one owner via configured bootstrap/bearer token and hashed device cookies, uses explicit session UUIDs and per-session turn locks, offloads generation to four threads, persists settings/device sessions/turn outcomes in ignored `.runtime/foundation.sqlite3`, and emits correlated JSON stream events. Cancellation is cooperative; single-process operation is required with JSON history. Cloud inference is opt-in, including fallback. UI capabilities are labeled honestly. PostgreSQL/graph memory remains a Phase 2 target. See `docs/PHASE_1_SETUP.md` for operating limits.

## Implemented Phase 2 local delta (2026-11-21)

`src/memory/` now owns canonical SQL history, source events, claims, import manifests and projection outbox. Desktop default is SQLite under `.runtime/`; optional PostgreSQL connector is unverified against a live server. `DurableMemoryStore` replaces JSON writes by default while preserving originals for rollback. Local graph/vector tables are rebuildable; all retrieval filters canonical ownership/audience/state/cloud permissions before ranking and again before returning. Optional Neo4j/pgvector modules are explicit export mirrors, not active read dependencies or continuously synchronized projections.

The initial lexical vector model is labeled as lexical; LM Studio semantic embeddings are optional. Memory input is explicit owner assertion through UI/API or `/remember`, not autonomous inference. Correction supersedes and forget redacts an entire chain, source events and local projections. Independent transcripts/backups/exports have separate retention. The single-owner API does not accept caller-selected principals. A local-mode conversation is marked private against later cloud routing. See `docs/PHASE_2_MEMORY.md` for remaining gates and backend-switch limitations.

## Implemented Phase 2 local delta

`src/memory/` owns SQL history, sourced claims, imports and projection outbox. SQLite is the runnable desktop default; the optional PostgreSQL connector is not live-verified. Local relationship/vector projections are rebuildable; retrieval filters canonical owner/audience/state/cloud permissions before ranking and before returning. Optional Neo4j/pgvector modules are explicit operator exports, not continuously synchronized runtime dependencies. See `docs/PHASE_2_MEMORY.md` for deployment/quality gates and backend-switch limits.

Memory input is explicit owner assertion via UI/API or `/remember`. Correction supersedes and forget redacts the full chain and local indexes. Transcripts/backups have separate retention. Lexical vectors are labeled accurately; semantic LM Studio embeddings are optional. Local-context sessions reject later cloud routing. One API process remains required.


## Implemented Phase 3 delta

`src/tools/` contains a typed gateway, owner project/task store, bounded public HTTPS research adapter, ICS snapshot connector and explicit read-intent bridge. Authenticated routes are in `src/interfaces/tools_api.py`; UI lives in `frontend/src/components/tools/`. Additive SQL tables store scoped grants, argument-bound approvals, run/results/audit, versioned projects/tasks/entity events and owner calendar snapshots. Local writes and completion results commit together. Network reads commit outcome separately and become interrupted on gateway restart if unfinished.

No model/source text can grant permission, approve an action or select arbitrary follow-up tools. `/research` deterministically reads at most two public result pages. Private project/calendar output is blocked in cloud-capable chat; UI reads stay local. Calendar import stores a snapshot atomically in SQL, leaves the original file unchanged and never edits the source calendar. Dense historical/sub-daily recurrence is rejected. Public fetch pins validated IPs, verifies hostname TLS and blocks private destinations, unsupported content and oversized bodies. External write/coding/job tools remain future scope. See `docs/PHASE_3_TOOLS.md` for exact limits and defaults.


## Phase 4 local implementation and open integration gate

`src/jobs/` supplies canonical durable approval/queue/event state, filtered independent source snapshots, artifacts and a separate leased worker. `src/agents/codex.py` adapts the installed Codex cloud CLI behind a mandatory native sandbox probe. `src/interfaces/jobs_api.py` exposes authenticated preparation/review/approve/cancel/evidence APIs. Approval is separate from chat routing and binds the exact selected source, objective, provider and limits. Source Git objects/history and runtime/private data are not copied. Named acceptance profiles run in the same restrictive sandbox; no automatic patch application exists.

The owner selected Codex cloud per approved job. Local queue/API/UI tests pass; live execution is blocked because Windows app runtime sandbox provisioning is unavailable, including after installing the standalone official CLI/daemon. Jobs fail closed before cloud calls. Token limits use observed usage, not a hard monetary cap. See `docs/PHASE_4_CODING.md`. Earlier future-scope wording above describes the Phase 3 checkpoint; Phase 4 supersedes its coding-queue status.


## Phase 5 implementation and acoustic acceptance gate

`src/personality/policy.py` composes versioned per-turn expression without mutating shared provider settings. Strict audience preview history isolation is checked before memory/tools/RAG; owner policy is unchanged. Legacy honesty is directness, factual honesty invariant. Random output decoration and frontend arbitrary gesture stripping are removed.

The browser uses authenticated SSE with chosen turn UUIDs, abortable readers and exact message updates. Server cancellation yields promptly even during blocked synchronous reads, retaining per-conversation locks/capacity until safe drain. `frontend/src/services/voice.ts` and `useBrowserVoice.ts` adapt opt-in browser recognition and local-only sentence synthesis. Tamil/English, editable transcripts, bounded capture/playback, push-to-talk interruption and page-local measured timings are implemented. Recognition can be vendor-backed with separate explicit consent; this is not offline/full-duplex acoustic voice. Actual speech availability/quality/latency remain owner-browser gates. See `docs/PHASE_5_VOICE.md`.
