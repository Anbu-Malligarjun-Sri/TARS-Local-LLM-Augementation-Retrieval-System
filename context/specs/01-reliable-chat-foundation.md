# Phase 1: reliable private chat foundation

Status: IMPLEMENTED for local single-owner operation. Automated checks recorded in the progress tracker; cooperative cancellation and single-process limits documented in `docs/PHASE_1_SETUP.md`. Live-provider/browser smoke verification remains an operational check.

## Goal

Make existing text chat a trustworthy base for private memory and tools. Preserve working provider/RAG behavior while eliminating cross-session ambiguity, ungoverned cloud fallback and misleading UI capabilities. Deliver units 01–04 separately.

## Design

Keep the current UI shell and API facade. Introduce explicit owner/device/session/turn identities and a versioned event contract. Default to private local access until authentication is configured. Reuse the current model adapters behind interfaces; do not add telephony, graph infrastructure or coding workers in this phase.

## Implementation

### Unit 01: baseline and regression coverage

Record dependency/runtime versions; choose and lock a tested environment. Ensure CI collects deterministic `tests/`, not import-time live-call scripts. Fix the three known frontend lint errors without broad primitive refactoring. Add feature tests for stream lifecycle, intentional disconnect and settings behavior; document current unsupported behavior. Add explicit TypeScript checking to validation. Separate opt-in live-provider checks from unit tests.

### Unit 02: owner and session boundary

Implement an explicit single-owner authentication and device session model, with a local pairing/bootstrap design documented before coding. Keep provider secrets server-side. Enforce ownership for chat/history/settings/index/search and WebSockets; configure explicit origins and payload/rate bounds. Do not place reusable secrets in WebSocket URL query strings. Require an explicit conversation for history/mutation; remove dependence on a process-global active conversation in API paths. Restrict ingestion paths to an allowlisted root. Maintain a documented legacy-ID compatibility/import strategy.

### Unit 03: turn lifecycle and provider policy

Define events with schema version, conversation/turn/message IDs, sequence and payload; include start, delta, complete, error and cancelled. Serialize SSE as JSON; include IDs before chunks. Scope buffers by turn and provide cancellation/reconnect semantics. Use async clients or bounded offload for blocking SDK/retrieval calls. Serialize turns per conversation, allow independent sessions concurrently and define what happens to partial messages on failure.

Add explicit local-only/cloud-permitted routing configuration. Apply eligibility to every fallback; report actual provider/model. Bound deadlines and attempts. Do not send a private-only request to the cloud when local inference fails. Reject unsupported provider options through capability checks rather than assuming every OpenAI-compatible endpoint accepts identical parameters.

### Unit 04: durable settings and truthful interface

Persist supported owner settings across restart; load them before frontend synchronization so browser defaults do not overwrite server preferences on mount. Label directness clearly while preserving truthfulness. Disable settings without implemented semantics. Fix intentional WS close/reconnect timers. Display actual capability/health information; remove fabricated confidence/source/CPU claims. Disable browser voice until real capture is implemented. Ensure saved and active sessions survive reload using an explicit authoritative persistence path.

## Dependencies

Reuse current FastAPI/Pydantic/React test stack where possible. Choose minimal authentication and persistence dependencies in the relevant unit and record rationale/version. Durable settings may use a small transactional local store behind an interface before Phase 2 database migration. Do not provision external services for this phase.

## Verify when done

- [ ] Deterministic backend and meaningful frontend tests pass; build, lint and explicit type checking pass.
- [ ] Unauthorized callers cannot read/mutate history/settings or use administrative ingestion.
- [ ] Two concurrent sessions preserve their own messages, streaming chunks and settings scope.
- [ ] Multiline/code responses survive REST/SSE/WS serialization unchanged.
- [ ] Interrupted generation emits a terminal error/cancel and leaves a recorded recoverable turn state.
- [ ] Deliberate disconnect/unmount does not reconnect; no stale chunks overwrite a newer session.
- [ ] Local-only failure results in no cloud request, verified with provider spies.
- [ ] Supported settings survive restart; unsupported controls cannot imply working behavior.
- [ ] Health/capability UI reports unavailable services honestly; microphone is not presented as functional.
- [ ] Existing private JSON/vector data and unrelated user changes are preserved.
- [ ] Tracker records completed units, commands/results, limitations and next spec.

## Rollout and rollback

Keep adapters compatible with existing chat contracts during cutover or explicitly version the API and migrate the frontend together. Back up any settings/session storage before migration. Do not remove old conversation data. Retain a documented restore path and a local-only disable switch for cloud providers.
