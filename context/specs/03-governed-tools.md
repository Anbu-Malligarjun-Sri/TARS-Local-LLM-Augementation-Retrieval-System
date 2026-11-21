# Phase 3: governed tools and useful assistance

Status: implementation in progress. Units 09–11.

## Goal

Provide sourced internet research, persistent owner projects/tasks and a read-only local ICS calendar through a governed tool gateway, authenticated API/UI and explicit chat intents. Owner selected local `.ics` integration on 2026-11-21.

## Design

- Reuse the canonical memory repository transaction boundary. Add tool tables without rewriting legacy/history/claim data.
- Registry owns schema validation, capability grants, concrete approval, idempotency and audit. Reads and local writes are distinct. Models/retrieved text cannot issue grants or approvals. No shell/code execution or external write connectors in Phase 3.
- Reads may run under explicit scoped grants; local changes require a concrete user approval of tool + exact arguments. An API/UI action can approve its own concrete change. Chat only executes read intents; writes stay reviewable in the Tools UI.
- Public HTTPS fetching validates DNS, pins a public IP with hostname TLS verification, rejects credentials/private hosts/ports, revalidates redirects, bounds size/time/content types and never forwards cookies/secrets. Search sends only the explicit query; private context is never appended. Results have URL/title/retrieval time and evidence text; quoted web content is untrusted.
- Projects/tasks are owner-scoped, versioned and idempotent. No destructive delete tools; archive/complete are recoverable status changes. Optional repository directories/notes are not automatically scanned.
- Calendar is an owner-provided UTF-8 ICS snapshot under ignored `.runtime/calendar/`. Parse using established ICS/recurrence libraries; bound date windows/event counts, handle timezone/all-day/recurrence exceptions, expose source freshness and no calendar writes. Re-import replaces snapshot atomically; no background sync claim.
- Default cloud routing must not see private project/calendar output. Decline private tools if cloud mode is enabled; use local mode for these turns.
- Explicit `/research`, `/fetch`, `/projects`, `/tasks`, `/calendar` intents work across model adapters. No claim of an autonomous model tool loop. Answer generation is bounded and source links are appended deterministically.

## Units

09: typed registry, persistent grants/approvals/runs, revocation, exact argument binding, idempotency and failure reconciliation.
10: safe public web fetch/search, projects/tasks, authenticated review UI, source-backed chat answers and run evidence.
11: local ICS import, bounded availability reads, freshness/status UI and chat use.

## Acceptance

Denied/revoked grants cannot execute. Approval cannot be reused for different arguments. Duplicate request keys do not repeat writes; concurrent duplicates are reconciled. Tool errors do not masquerade as success. Prompt injection cannot cause additional tool calls. SSRF/DNS/redirect/path escapes are rejected. Cross-owner project/task reads fail. ICS timezone/recurrence exceptions/all-day/staleness tested. Existing Phase 1/2 checks pass, UI exposes sources/actions/errors and live smoke checks run on safe public pages and synthetic local data.

## Operational bounds

No sending mail, calendar edits, remote filesystem access or coding agents yet. Source text and audit results may contain private data and have separate retention from personal facts. Keep one API process until shared cancellation/worker coordination exists. Search provider availability can change; expose provider failures and allow direct public URL fetch.
