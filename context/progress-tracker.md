# Progress tracker

Last updated: 2026-11-21 (Asia/Calcutta).

## Current phase

Phase 4 units 12–13 local implementation delivered: durable approved coding queue, filtered snapshots, Codex cloud adapter and review UI. Live execution acceptance remains BLOCKED by the Windows Codex sandbox provisioning service; no live cloud coding success is claimed. Phases 1–3 remain available. External database/quality gates and personal ICS import remain pending.

## Current goal

Build a persistent TARS personal intelligence for routines/projects, interchangeable local/cloud models, graph memory, audience-aware personality, coding delegation and eventual phone assistance.

## Completed

- Reviewed backend/provider/RAG/memory/personality/voice/API/CLI and frontend chat/state/settings/status architecture.
- Parsed dataset inventory: 17 YAML files, 526 entries, 407 unique exact Q&A pairs.
- Counted existing conversation metadata: 25 files, 119 messages; private message text not copied into docs.
- Created `docs/TARS_ARCHITECTURE_PLAN.md` with current-state evidence, target architecture, phases and release gates.
- Instantiated the supplied six-file methodology in root `context/` and added Codex/Claude entry points.
- Added ordered build plan and the first phase specification.

## Verification baseline

| Command | Result |
| --- | --- |
| `..\.venv\Scripts\python.exe -m pytest tests -q -o faulthandler_timeout=20` | 3 passed, 2 deprecation warnings; approved outside-sandbox run. Initial sandbox run stalled in Windows asyncio socket initialization before application request handling. |
| Frontend `npm run build` | Passed; old Browserslist data and >500 kB chunk warnings |
| Frontend `npm run test` | 1 placeholder test passed; not meaningful feature coverage |
| Frontend `npm run lint` | 3 errors, 9 warnings; errors in command/textarea empty interfaces and Tailwind `require` |

Live model, microphone, carrier, training and deployment behavior was not exercised. Existing backend tests use fakes. No claims of end-to-end production readiness.

## In progress

Phase 4 live sandbox/cloud integration remains open. The official standalone CLI and local daemon were installed; the native probe still reports app runtime provisioning service unavailable and refuses helper fallback. Execution stops before cloud disclosure. Repair the supported runtime, rerun canaries, then approve a small synthetic live job. Do not weaken sandbox policy.

## Next up

Refresh TARS at localhost:8081 and open Coding jobs. Local snapshot preparation, source review and approval/cancel are available; readiness exposes the execution blocker. See `docs/PHASE_4_CODING.md`. Finish the live Phase 4 gate before claiming operational coding delegation. Phase 5 audience persona/voice remains planned.

## Open questions

- What CPU/RAM/GPU/VRAM and always-on host are available?
- What monthly infrastructure/model/phone spend is acceptable?
- Which personal data may go to which cloud providers?
- Which spoken languages, voice and contact language preferences are needed?
- Which phone country/carrier and number arrangement: separate assistant number, forwarding or porting?
- Calendar decision resolved: local read-only ICS snapshots first; future remote services remain optional.
- Which contact groups may receive playful responses; what are the exact quiet-hour and urgent-call rules?

These block only dependent deployment/integration decisions, not initial local foundation work.

## Architecture decisions

| ID / date | Status | Decision and reason |
| --- | --- | --- |
| A01 / 2026-11-21 | Proposed | Keep FastAPI/React; migrate incrementally to preserve useful existing work |
| A02 / 2026-11-21 | Proposed | External memory/persona independent of provider; fine-tuning is optional model-specific optimization |
| A03 / 2026-11-21 | Proposed | PostgreSQL canonical records, Neo4j graph and pgvector derived projections; outbox avoids conflicting truths |
| A04 / 2026-11-21 | Proposed | Apply privacy/capability/budget eligibility to fallback, not just primary routing |
| A05 / 2026-11-21 | Proposed | Streaming STT/TTS first, phone pilot later; select one media path after carrier validation |
| A06 / 2026-11-21 | Proposed | Coding harnesses run as isolated durable jobs; no raw unbounded shell execution |
| A07 / 2026-11-21 | Proposed | Honesty remains invariant; directness/humor vary by audience, privacy permissions do not |
| A08 / 2026-11-21 | Implemented docs | Root context is canonical; supplied methodology stays unchanged as reference |

## Session notes

Repository is nested beneath workspace root: `TARS-Local-LLM-Augementation-Retrieval-System/`. Baseline commit was `33f57fa`. Initial Git status already included modified `data/vector_db/chroma.sqlite3`, three untracked conversation files, and an untracked vector-index directory. Preserve those user changes. The methodology folder was added by the owner during review. Frontend build may regenerate ignored `dist/` output.

Use root `AGENTS.md`/`CLAUDE.md` to restore project context. The context files are development memory, separate from the planned runtime personal memory. Update this tracker after every meaningful unit, with evidence rather than aspirational completion marks.

## Phase 1 implementation session — 2026-11-21

- Added single-owner bearer/bootstrap authentication, hashed 30-day HttpOnly device sessions, revocation, explicit origins, rate limits, input bounds and restricted ingestion roots.
- Required explicit conversation UUIDs; authenticated paired devices all belong to the one owner. No multi-owner tenancy is claimed.
- Added versioned JSON SSE/WS events, turn/message IDs, sequence/timestamp, durable turn outcomes, per-conversation serialization, bounded generation threads and cooperative cancellation. Provider calls have finite timeouts; cloud routing defaults off, including fallbacks; private endpoints must be loopback.
- Added transactional SQLite settings and startup restore, atomic JSON conversation replacement, settings-change guard during active turns and initial frontend settings hydration.
- Added pairing UI/session resume, intentional disconnect cleanup, session-aware late-event filtering, persisted active browser sessions, backend history refresh, stop response and explicit unavailable controls/status.
- Fixed baseline lint errors; added deterministic pytest collection and a Windows Python 3.14.8 installed dependency snapshot (`requirements.lock.txt`). Existing npm lock retained.
- Verification: 10 backend tests passed, including auth/revocation/origin rejection, cloud eligibility, multiline SSE errors, cancellation, settings restart and concurrent session isolation. Frontend: 3 tests pass (2 meaningful transport tests plus existing placeholder); TypeScript checking, lint and production build pass. Seven pre-existing Fast Refresh warnings remain; Browserslist/bundle-size and Chroma deprecation warnings remain.
- Limits: SDK cancellation is cooperative at chunk/read-timeout boundaries; one process only; existing JSON history retains its legacy trimming behavior. Legacy UUID import mapping is reserved for Phase 2. UI provider status is unprobed rather than a connectivity claim. Live providers and browser rendering were not manually exercised. No deployment, calls, training or existing private-data migration performed.

## Phase 2 session — 2026-11-21

- Added `context/specs/02-shared-memory.md` before implementation. Architecture adjustment: SQLite is the runnable desktop canonical store; optional PostgreSQL uses the same repository contract. The environment has Docker CLI but no running daemon or external DB drivers. This avoids making memory depend on unprovisioned services.
- Added versioned canonical SQL tables for conversations/messages, source events, owner claims, import manifests and outbox, plus rebuildable local edge/vector projections. Legacy history is no longer trimmed in SQL; prompt history remains bounded.
- Imported 25 existing files / 119 messages into ignored `.runtime/memory.sqlite3`, with original JSON untouched, content-hash snapshots and stable UUID mappings. Changed/corrupt input and ID collisions fail safely; repeat import does not resurrect cleared history.
- Added source-linked owner assertions, audience/sensitivity/cloud permissions, expiry, correction/supersession, correction-chain forget/redaction, export, graph inspection and SQLite online backup. Conversation/backup retention remains independent and visible in UI.
- Added shared provider-independent personal context, optional LM Studio semantic embeddings, and explicitly labeled offline lexical vectors/keyword/graph fallback. Local-context sessions cannot switch to cloud-capable routing and disclose old transcripts.
- Added authenticated memory CRUD/search/source/graph/rebuild/export APIs, sidebar Personal memory dialog, server conversation listing and browser history hydration, and explicit `/remember` command. No unreviewed automatic memory extraction.
- Added optional PostgreSQL repository path, Neo4j/pgvector operator mirrors, dedicated Compose configuration and optional driver requirements. None were started or live-verified. These mirrors are manual snapshots; immediate external deletion/continuous sync is not claimed.
- Verification: 21 backend tests (9 repository/continuity tests, 2 memory API tests and 10 existing Phase 1 tests); 6 frontend tests. Typecheck, lint (7 existing warnings) and production build pass. Existing Chroma deprecation, Browserslist and bundle-size warnings remain. External DB and semantic-quality tests are pending.
- Runtime docs: `docs/PHASE_2_MEMORY.md`; private runtime state/snapshots/backups stay ignored. No real personal facts were added by the implementation tests; test facts use temporary databases.


Final data verification: repeated the real import (0 new files), restored a fresh SQLite backup in a separate location, and verified 25 conversations / 119 messages / 25 import records. SHA-256 hashes of all original JSON files remained unchanged. A rendered React dialog test verifies memory facts, provenance and relationship inspection; frontend total is 6 passing tests.


## Local launch and live verification — 2026-11-21

- Started the installed LM Studio daemon/API and loaded existing Qwen 3.5 9B and Nomic embed-text-v1.5 models. No cloud credentials were configured; no account, paid API key or new model download was needed.
- Created ignored `.env` with a generated owner credential, local-only routing, live semantic embeddings, 512 output tokens and model-specific reasoning disabled after observing excessive initial reasoning latency.
- Backend runs at 127.0.0.1:8000; Vite frontend at localhost:8081. Background process IDs/logs live under ignored `.runtime/`.
- Verified a genuine generated REST reply (HTTP 200, about 20 seconds), semantic embedding requests and cross-conversation synthetic fact recall. Removed only the temporary verification fact and its test transcript afterward.
- Added local-operator single-use ten-minute launch tickets that exchange a URL fragment for an HttpOnly cookie without putting the permanent owner token in the URL. Added a repeatable `scripts/start-local.ps1` launcher.
- Regression checks: 23 backend tests and 6 frontend tests pass; type checking/build pass. Launch tests cover expiry and one-use enforcement. Browser automation could not open Edge because that browser connector is unavailable; a direct user launch link is provided instead.

Live WebSocket verification also passed: first text arrived in 11.4 seconds and the stream completed. Backend and frontend were left running for owner testing.


## Phase 3 session — 2026-11-21

- Implemented `context/specs/03-governed-tools.md` for units 09–11. Added ten schema-validated tools under `src/tools/`: projects list/create/update, tasks list/create/update, calendar read/import, web search/fetch.
- Persistent scoped read grants, exact one-use five-minute approvals, expiry/revocation, owner-bound request keys, atomic local writes/result/audit, optimistic versions and restart interruption state are enforced outside model output. No shell or external-write tools exist.
- Added secure public HTTPS fetch with DNS pinning/public-address policy, TLS/redirect validation, finite data/time bounds and safe HTML/XML parsing. Key-free public Bing RSS search is best-effort. `/research` attempts at most two follow-up page reads and appends actual source links/timestamps/run IDs.
- Added owner projects/tasks and recoverable archive/complete operations. Added bounded ICS import/recurrence/timezone/exception/all-day reads with snapshot age and stale flags. The user chose local `.ics`; no real calendar was supplied or overwritten. Calendar data is transactionally stored in SQL, not an independently mutable file.
- Added authenticated tool APIs and Tools & projects dialog: concrete review before writes, research evidence, project/task forms/status, calendar import, permission switches, run history. Markdown images are suppressed to prevent untrusted output from causing automatic network requests.
- Explicit read commands work across existing model adapters; source/model text cannot trigger another tool or approval. This is not a model-native autonomous planning loop. Private project/calendar chat tools require local-only routing.
- Verified live public search, Python homepage/docs retrieval, approved synthetic project/task creation and completion, and generated `/research` answer with real links (about 40 seconds on local Qwen). Synthetic project archived, task completed. One site's unverifiable certificate was correctly rejected; no TLS bypass used.
- Backed up canonical memory before startup, activated new backend on loopback and left frontend running. Restarted the pre-existing LM Studio service/models when live summarization initially found them stopped.
- Verification: 45 backend tests and 8 frontend tests; type checking, lint (7 pre-existing warnings) and production build pass. Tests include prompt injection containment, approval mismatch/expiry, concurrent idempotency, grant revocation, private-mode boundaries, SSRF/redirect/content bounds, recurrence exception/DST cases, rendered review flow and image suppression. No manual browser automation claimed: the updated browser skill file was unavailable, so rendered React and live API checks were used.
- Installed maintained calendar/recurrence/timezone/safe XML dependencies and refreshed the installed dependency snapshot. Existing conversations, private memories and original JSON were preserved. Runtime docs: `docs/PHASE_3_TOOLS.md`.


## Phase 4 session — 2026-11-21

- Owner selected Codex cloud with explicit per-job approval. Added scoped spec before code. Cloud coding is a separate opt-in from local chat; no API key/account was invented or copied.
- Added additive canonical SQL coding_jobs/coding_events, owner-bound idempotency, immutable snapshot/contract approval hashes, 45-second renewable leases, heartbeat, finite deadlines/output/observed token budgets, cancellation and restart interruption without automatic replay.
- Added filtered independent Git snapshots instead of shared-object worktrees, to avoid exposing historical private data. Registered repository aliases, path/hash/byte manifests, source review, link/config/private-data exclusions, isolated baseline/workspace and unchanged originals. Filtering does not guarantee inline secret detection.
- Added installed Codex CLI adapter, filtered child environment, ignored config/rules/hooks/extra integrations/subagents, restrictive filesystem/network policy, mandatory generated-canary preflight and sandboxed acceptance profiles. No unsandboxed fallback or automatic source apply/merge/push.
- Added worker process-tree cleanup and artifacts: new/deleted/changed files, downloadable patch (including missing-final-newline markers), agent/usage/check evidence, failures and explicit limitations. Large result bodies are fetched only for selected jobs.
- Added authenticated API and sidebar Coding jobs review UI with separate cloud checkbox/approval, source preview, readiness probe, status/cancel and patch/check review. Added background worker launcher and setup/recovery guide.
- Verification: 62 backend tests, 9 frontend tests; typecheck, lint and production build pass. Tests use synthetic repositories and mocked coding adapters; actual subprocess timeout/output/stream-tail behavior is covered. Seven pre-existing lint warnings and existing build/Chroma advisories remain.
- Live blocker: bundled CLI 0.171.0-alpha.13 and official npm CLI 0.171.0 both fail native sandbox provisioning. Installed/started official local daemon; probe still returns `app runtime provisioning service is unavailable; refusing helper fallback`. No live cloud coding or live sandboxed test pass claimed. No source was sent in generated canary probes.
- Runtime cloud coding opt-in follows owner selection; provider login remains managed by official Codex. Private runtime files/installations/logs stay ignored. Created an online canonical-memory backup before activating the backend/worker. Verified live authenticated snapshot preparation/source inspection/cancellation without cloud approval, and confirmed all original conversation JSON hashes remain unchanged. Services are running locally.
- Next: repair supported Codex desktop/runtime provisioning; rerun readiness canaries and an explicitly approved synthetic live job. Phase 4 operational acceptance remains open.
