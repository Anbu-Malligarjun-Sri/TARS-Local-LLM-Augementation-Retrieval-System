# Phase 3: tools, projects, research and local calendar

Phase 3 adds ten governed tools to the running TARS application. Open **Tools &
projects** in the sidebar. Existing pairing, conversations and personal memories
continue to use the Phase 1/2 runtime.

## What you can use

- **Projects:** create, edit and archive projects with notes. Show archived projects
  and edit/save them to restore active status.
- **Tasks:** create, edit, prioritize, set an explicit timezone-aware due time,
  mark todo/doing/blocked/done, archive or reopen. Show completed tasks to reopen.
- **Research:** public search or fetch a public HTTPS URL. Results include evidence,
  source type, URL and retrieval timestamp. Search snippets are labeled as leads;
  fetching a page provides page evidence. Inspect the full bounded result in Tool
  evidence or Activity.
- **Calendar:** import your chosen local `.ics` file and read the next seven days
  (API supports 1–31 days). The original calendar/file is never edited.
- **Permissions:** revoke/re-enable individual read tools. Writes always require
  approval of exact validated arguments; no reusable write grants are supported.
- **Activity:** inspect run IDs, completed/failed/interrupted state and stored
  results. Permission-denial and validation events are also retained in the audit
  API. Runtime data is private and ignored by Git.

Chat commands:

```text
/research Python programming official documentation
/fetch https://www.python.org/
/projects
/tasks
/calendar
/calendar 2026-11-23
```

`research ...`, `search the web for ...`, `show my projects`, `show my tasks` and
`show my calendar` are also recognized. Reads use the same gateway as the UI.
Chat writes are deliberately not inferred from natural language: make the concrete
change in Tools, review its arguments, then click **Approve and run**.

## Research behavior and limits

The key-free search adapter currently consumes Bing's public RSS search response.
This is a best-effort provider without an availability contract; upstream failures
are reported. Direct public URL fetch is an independent fallback. No account/API
key was purchased or created. A live search returned results and fetching Python's
homepage/docs succeeded. A site with an unverifiable TLS certificate was rejected;
there is no insecure TLS fallback.

`/research` searches, then attempts at most two public result-page fetches. Each
fetch independently obeys its read grant and network policy. Only the explicit
query is sent to search; private personal memory is not appended. Bounded source
excerpts are passed to the selected model as untrusted reference data, without
private conversation context. Source links/timestamps and run IDs are appended
by the application. If summarization fails, retrieved sources remain available and
TARS says the model could not summarize them. A generated summary is not a guarantee
of source correctness or a comprehensive research report.

Sources and model text cannot invoke additional tools, change grants, approve a
write or run shell commands. The UI blocks Markdown images to prevent automatic
tracking/exfiltration requests. Public fetching uses pinned public DNS addresses,
hostname-verified TLS, no cookies/credentials/proxies, validated redirect hops,
600 KB response and 14 KB extracted-text caps, finite socket/overall read budgets,
and a restricted text/HTML/XML content-type list. Private/reserved/mixed DNS and
IPv6 translation/tunneling addresses are denied. DNS resolution still uses the OS
resolver; its own timeout is not a hard killable worker deadline.

## Calendar setup

Choose **Calendar** in Tools, select your actual exported `.ics` file, confirm the
label/timezone, click **Review snapshot import**, inspect the data, then approve.
No personal calendar snapshot was supplied during implementation, so the live
calendar correctly reports **not configured** until you import one. Synthetic
calendar fixtures were used only in temporary test databases.

Snapshots are limited to 45 KB UTF-8 and 350 components. They are stored
transactionally in `calendar_snapshots` within the canonical SQL database, rather
than as independently mutable files. This gives import and its tool result one
atomic transaction. A new import replaces only that owner's current snapshot;
the original `.ics` file stays unchanged. Tool-result/history retention is separate.
There is no background calendar polling, remote calendar login, calendar edit,
invitation send or meeting booking.

The import timezone defaults to Asia/Calcutta; floating event times use that
explicit timezone. All-day and recurring events, EXDATE exclusions, overrides,
cancellations and daylight-saving offsets are supported by the installed
[icalendar](https://icalendar.readthedocs.io/en/latest/how-to/usage.html) and
[recurring-ical-events](https://recurring-ical-events.readthedocs.io/en/latest/user-guide/examples.html)
libraries. Dense/sub-daily recurrence, EXRULE and excessive historical recurrence
are rejected rather than silently approximated. Output is capped at 200 events.
Daily/weekly recurrences beginning over ten years before the requested window,
and monthly recurrences over a century old, need a bounded export.

Calendar reads show imported time, snapshot age, timezone, stale status after
24 hours and truncation. Snapshot freshness is measured from import, not a claim
that the export was current. An empty snapshot window does not establish that you
are free; live availability may have changed. There are no caller/contact calendar
read APIs in Phase 3.

## Permissions and retry semantics

Single-owner mode seeds five scoped read grants once, valid for up to a year:
projects.list, tasks.list, calendar.read, web.search and web.fetch. Revocation is
persistent and default grants are never re-created on restart. An authenticated
owner can issue a five-minute one-use approval for an exact tool/argument hash.
Approval changes, expiry and reuse are rejected. Unknown/extra fields are rejected.

Every run uses an owner-scoped UUID request key. Reusing the same key for the same
completed local write returns its result; using it for different arguments fails.
Local writes, approval consumption, entity event and result commit in the same
transaction. Failed local writes roll back entity changes and record a failed run.
No external side-effect tools are implemented, so this is not a claim of exactly-once
email/call execution. Those require their own reconciliation policies later.

Network reads record running/completed/failed outcomes outside the write transaction.
If the process exits during a read, the next gateway startup marks it interrupted.
Use a new key for an explicit read retry; duplicate in-flight keys return current
state rather than issuing duplicate requests. Denials and errors retain audit codes
without copying credentials into logs. Results and event snapshots can contain
private information and remain in SQL/backups until separately managed.

Private project/task/calendar tools are declined for cloud-capable chat routing.
Use local-only routing for these turns. Direct owner UI reads stay local and do not
send their result to an LLM. Memory/conversation privacy markers remain enforced.
Read grants cannot be turned into write grants through model output or sliders.

## API and operation

Authenticated endpoints under `/api/tools`:

- `GET /`: schemas/descriptions; `GET /grants`, `PUT /grants/{tool}`.
- `POST /approvals`: exact tool and arguments for owner review.
- `POST /run`: tool, arguments, UUID request_key, optional approval_id.
- `GET /runs`, `GET /audit`: owner-only run evidence and audit events.

The schema additions are additive to the existing canonical repository. A canonical
backup was created before live startup. Existing conversations, imports, claims and
source JSON are preserved. One backend process remains required; model/network
cancellation is cooperative and tools use finite I/O/data budgets rather than hard
process isolation. Durable long jobs/coding workers remain Phase 4.

The UI and explicit command bridge are implemented; this is not an autonomous
model-native planning loop. Provider-independent command dispatch makes the initial
tools usable with existing local/cloud adapters without assuming native tool-call
support. Additional connectors should enter through the same gateway and new specs.

## Verification

Backend tests cover authentication, exact approval binding, idempotency/concurrent
writes, owner isolation, revoked/expired permissions, failed-run rollback, optimistic
versions, restart interruption, prompt-injection containment, DNS/redirect/response
limits, ICS recurrence/exceptions/all-day/stale/DST cases and Phase 1/2 regressions.
Frontend tests verify review before mutation, provenance/relationship display and
remote-image suppression. Typecheck, lint and production build are required.
Live checks exercise public search/page retrieval, synthetic project/task actions,
and model-backed research. The synthetic project was archived and its test task
completed; no real owner calendar was overwritten.
