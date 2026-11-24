# Ordered build plan

**Product direction · 23 November 2026.** The [companion robot master roadmap](../../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

Phase 0 planning and Phase 1 are implemented. Phase 2 local milestones are delivered; external integration and quality gates remain pending. Phase 3 units 09–11 are implemented (local ICS selected); Phase 4 units 12–13 are implemented locally; live sandbox/cloud execution remains blocked by runtime provisioning. Phase 5 units 14–15 are implemented locally; real microphone/acoustic/browser acceptance remains pending. Units 16 onward are planned. Introduce dependencies only when their unit uses them. Estimates and phase acceptance gates: [detailed plan](../../docs/TARS_ARCHITECTURE_PLAN.md).

| Unit | Phase | Visible outcome | Depends on |
| --- | --- | --- | --- |
| 01 | 1 | Reproducible dependency/test baseline and meaningful regression coverage | Planning |
| 02 | 1 | Private owner/device access and session ownership; unauthorized history/settings denied | 01 |
| 03 | 1 | Correlated streaming, error/cancel lifecycle, async isolation, explicit routing privacy | 02 |
| 04 | 1 | Persisted supported settings and truthful UI capabilities/status | 03 |
| 05 | 2 | Canonical database/events and repeatable JSON import with legacy-ID map | 04 |
| 06 | 2 | Sourced personal claims with correction/forget semantics and isolation | 05 |
| 07 | 2 | Rebuildable graph/vector projections and model-independent context retrieval | 06 |
| 08 | 2 | Memory inspection/correction UI and cross-model recall demonstration | 07 |
| 09 | 3 | Governed tool registry, scoped grants, audit/idempotency | 08 |
| 10 | 3 | Sourced web research and project/task tools | 09 |
| 11 | 3 | First calendar read integration with freshness and disclosure control | 09 |
| 12 | 4 | Durable jobs with cancellation/leases and isolated coding worker | 10 |
| 13 | 4 | Coding diff/test artifacts and review flow; second adapter only if needed | 12 |
| 14 | 5 | Audience persona policies and held-out tone evaluations | 08 |
| 15 | 5 | Browser streaming voice and interruption with latency measurements | 10, 14 |
| 16 | 6 | Carrier feasibility confirmed; authenticated sandbox inbound media path | 11, 15 |
| 17 | 6 | Contact-aware screening, transfer/message-taking and outage fallback | 16 |
| 18 | 7 | Durable routines and notifications, quiet hours and deduplication | 11, 12 |
| 19 | 7 | Allowlisted owner calls with quotas, cancellation and emergency stop | 17, 18 |
| 20 | 8 | Dataset curation and optional local tuning compared to prompt baseline | 14 and collected evaluations |
| 21 | 8 | Restore/outage drills, cost/quality tuning and operational release gate | Applicable deployed units |

Before each unit, create a focused spec with goal, design, implementation, dependencies and verification. The first phase specification covers units 01–04, which should be implemented and checked separately. Do not mark an entire phase complete because one unit works.
