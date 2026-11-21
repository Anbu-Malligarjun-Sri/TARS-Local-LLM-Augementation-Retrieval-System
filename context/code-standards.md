# Code standards

These are target standards for new/touched code. Existing violations are recorded in the audit; this file does not claim they are fixed.

## General

- Keep changes within the active spec. Prefer dependency injection and typed contracts over new module globals.
- Preserve existing behavior through adapters while migrating. Do not rewrite the frontend/backend without an evidenced need.
- Use stable UUIDs for public objects and retain legacy import IDs separately. Store UTC-aware timestamps; carry IANA timezone for schedules.
- Separate domain logic from SDKs and transport. Return typed errors with stable codes; redact credentials and private content from routine logs.

## Python

- Type public interfaces and use validated Pydantic models at boundaries. Adopt modern settings configuration when touching config.
- Use async provider clients where supported; otherwise bounded offload with cancellation/deadline behavior documented.
- Use context-managed resources, bounded queues, transaction scopes and explicit lifecycle cleanup.
- Lock supported runtime/dependency versions after a compatibility check; current environment observed Python 3.14.8, while README says 3.11+. Do not promise the entire range without tests.
- Keep live-provider tests opt-in and separate from deterministic unit/integration tests. The top-level legacy test scripts make live calls during import and must not be the default CI collection target.

## TypeScript / React

- Define discriminated unions for server events, including errors/cancellation; validate external payloads.
- Move toward strict checking incrementally. Current `tsconfig.app.json` disables strictness; do not describe it as enabled.
- Correlate stream events by conversation/turn/message ID. Do not update whichever message happens to be last.
- Cancel reconnect timers, abort requests, and release media resources on teardown.
- Keep server state authoritative for history/settings; use Zustand for local interaction state and bounded caches.
- Use existing components/tokens and accessible semantic elements. Avoid unrelated generated primitive edits.

## API routes

- Validate bounds, principal and resource ownership before reads/mutations.
- Use JSON event payloads for streaming; define initial IDs and exactly one terminal event per turn.
- Provide deadline, rate/payload limits, safe error codes and cancellation semantics.
- Make side effects idempotent where possible. A timeout is an unknown outcome until reconciled, not proof an operation never happened.
- Validate webhook signatures using provider requirements; deduplicate events and reject replay where supported.

## Data and tooling

- Database migrations need forward and rollback/restore plans. Back up before importing existing private data.
- Use a transactional outbox for projections; index generation includes model ID/dimension/version.
- Never execute raw model-supplied shell strings. Pass validated structured arguments within allowed filesystem/network boundaries.
- Keep tool secrets in host-managed secret storage. Models receive narrowly scoped results, never broad credentials.
- Deduplicate/group examples before train/test split; keep held-out evaluation data out of prompts and training.

## Verification

Run relevant deterministic tests plus affected integration checks. Backend baseline: `python -m pytest tests -q` from repository root. Frontend baseline: `npm run build`, `npm run test`, `npm run lint` from `frontend/`; build does not replace an explicit TypeScript check. Add meaningful behavioral coverage, not implementation-mirroring tests or more placeholder assertions.

For memory, test isolation/correction/deletion/restart. For tools, test denied grants/retries/timeouts. For voice, test interruption and measured latency. Record command, result and limitations in the progress tracker. Do not fix unrelated warnings solely to make a scoped change look larger.

## Memory conventions

Use repository transactions for canonical writes and outbox entries. Never accept principal identity from request bodies. New claims version corrections. Revalidate permissions after embedding/ranking. External exports cannot authorize runtime reads. Label lexical vectors accurately and verify each new projection consumer's deletion/rebuild behavior.


## Tool conventions

Register a strict Pydantic argument schema, write/private flags and handler for each tool. Write handlers may perform only local SQL mutations in the supplied transaction; external side effects require a new reconciliation design. Never mint approvals or grants from model/source output. Bind approvals to normalized arguments and request keys to owner/tool/arguments. Preserve failed/interrupted outcomes. Apply SSRF/TLS/data bounds to every redirect destination. Calendar parsing must not fetch ATTACH/URL values; preserve snapshot freshness and supported recurrence limits. Do not silently enable remote Markdown images when displaying untrusted evidence.
