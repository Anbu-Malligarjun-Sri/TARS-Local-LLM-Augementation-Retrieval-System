# Progress tracker

**Product direction · 23 November 2026.** The [companion robot master roadmap](../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

Last updated: 2026-11-24 (Asia/Calcutta).

## Current phase

Companion R0 release scope and bilingual desktop baseline delivered. R1 local visitor-session service implemented. Open-ended sales-demo quality, real-browser audio and public deployment remain open. [Release record and measured results](../docs/COMPANION_R0_RELEASE.md)

Phase 5 units 14–15 local implementation delivered: versioned audience persona, isolated tone previews, opt-in Tamil/English browser recognition, sentence-level local speech and a rectangular Stop control. Real microphone/acoustic/code-switching acceptance remains pending. Phase 4 live coding execution remains blocked by sandbox provisioning; earlier external database/quality gates remain open.

## Current goal

The current companion increment is a private bilingual reference and a separate short-lived visitor demo for US buyers. Hardware price target USD 49–125. INR 2,000/month operating target and INR 3,000 hard demo ceiling. USD 99 is a worksheet assumption only.

Build a persistent TARS personal intelligence for routines/projects, interchangeable local/cloud models, graph memory, audience-aware personality, coding delegation and eventual phone assistance.

## Completed

- **24 November 2026, R0 / first R1 unit.** Removed the browser microphone locale from outgoing chat style. Persona v2 resolves the current request, honors explicit English/Tamil switches, scopes examples and dry humor to the answer language, and narrows canned English shortcuts. Playback selects compatible local voices from each sentence. Updated operator docs and added isolated synthetic bilingual acceptance scripts.
- Established the visitor allowlist, account/retention boundaries, asset inventory, cost worksheet and public quality gate. Implemented an independent loopback visitor service with 15-minute fixed expiry, capped admission, host/origin checks and idempotent begin/end. Exercised the documented PowerShell create/read/end flow on a temporary listener. Visitor inference, speech, UI, billing and deployment remain future R1 units.
- Verification: 98 backend and 21 frontend tests passed. Frontend typecheck and production build passed, lint completed with seven existing warnings. Confirmed HTTP 200 on desktop UI and authenticated health and the running schema's automatic locale. Local R0 Qwen run: 6/6 dominant scripts matched. Manual review caught inaccurate content, one malformed mixed-script word and an invented estimate. Saved synthetic timing/evaluation results in the release record. Browser audio remains mocked. No public deployment or paid provider was used.

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

Phase 5 owner-browser acceptance: actual recognition availability, microphone permission, Tamil/English names/noise/code-switching accuracy, installed local voices and measured acoustic latency. No audio was recorded or sent to a vendor during development tests. Codex sandbox/runtime provisioning remains an independent Phase 4 blocker.

## Next up

Implement the visitor turn/Stop contract with a synthetic provider, then the spend ledger. Compare bilingual model quality on the R0 fixtures. R2 board selection can proceed independently. Paid preorder and buyer isolation gates are in the master roadmap.

## Open questions

- What CPU/RAM/GPU/VRAM and always-on host are available?
- The demo target is INR 2,000/month with an INR 3,000 ceiling. Future phone and buyer service budgets remain open.
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


## Phase 5 session — 2026-11-21

- Owner requested Phase 5 plus Stop in the rectangular input action and selected Tamil and English. Added `05-persona-voice.md` before implementation. Initial voice language is Tamil (India), English (India) selectable; code-switching quality depends on the browser service.
- Added portable `tars-persona-1` policy and reviewed style examples, strict per-turn audience/playful/language settings, sensitive/technical humor suppression and truthful identity. Parent/professional/unknown modes are neutral/respectful; friend sarcasm needs explicit consent. Honesty remains invariant; legacy honesty means directness.
- Non-owner preview sessions have no personal memory/RAG/tools and cannot reuse owner/other-audience transcripts. Owner memory/routing policy is unchanged. Preview history carries audience metadata and restores the audience label. Contact authentication/overrides remain future work.
- Removed random model-output decoration and fictional identity claims; Markdown no longer removes arbitrary emphasized/code text as gestures.
- Replaced browser chat with authenticated cancellable SSE and known turn IDs. Send becomes rectangular STOP while thinking/streaming; partial text is retained and late events ignored. Backend cancellation acknowledges before blocked provider reads complete, retaining capacity/locks during safe cooperative drain. Pre-start Stop and reused IDs are handled.
- Added opt-in Web Speech single-utterance capture, live partials, editable final transcripts (automatic send optional), local-only sentence playback, bounded capture/queues/timeouts and explicit interrupt-and-listen. Stop/mute/session/language/consent/teardown clear audio; no automatic microphone restart. Browser-vendor STT disclosure is separate from local LLM routing. TARS stores sent transcripts, no raw audio.
- Page-local bounded timing samples show counts, median/p95 for text, utterance start, available speech finalization and local stop dispatch. No fake metrics; acoustic silence and provider shutdown are not inferred from dispatch. Unsupported speech or absent local voices keep text available.
- Verification: 80 backend tests and 19 frontend tests pass; typecheck, lint (7 existing warnings) and production build pass. Coverage includes 12 held-out policy cases, privacy/history/tool isolation, blocked-call/pre-start cancellation, split Tamil UTF-8 SSE, rectangular Stop/late-event behavior, Tamil transcript review/playback, speech consent/errors/timeouts and queue cleanup. Browser speech is mocked in tests.
- Local Qwen smoke evaluation used three synthetic previews in isolated SQL storage. First pass exposed an invented log-access aside and Tamil placeholder; strengthened reviewed prompts and repeated all cases. Final parent/friend/professional-Tamil replies were appropriate in these three samples. First-text median 7,974 ms / p95 14,993 ms, n=3; not a microphone latency or comprehensive style benchmark.
- Live authenticated cancellation before first token yielded start/cancelled and acknowledged in 32 ms (one smoke sample). Provider drained; only the synthetic probe turn was removed and original conversation JSON hashes were unchanged. Provider HTTP streams now explicitly close on generator cleanup.
- Created online memory/foundation backups before restarting the local backend; frontend remains running. Real microphone, speech vendor and acoustic playback were not activated by development tooling. No phone calls, new speech accounts, model training or source publication.
- Operational acceptance remains open for actual owner-browser recognition/voices and Tamil/English acoustic/accuracy/latency evaluation. Phase 4 provisioning blocker remains open.
