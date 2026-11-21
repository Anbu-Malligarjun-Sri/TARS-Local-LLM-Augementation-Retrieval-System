# Phase 4: durable isolated coding delegation

Status: local implementation verified; live sandbox/cloud acceptance gate blocked by native runtime provisioning. Units 12–13. Owner selected Codex cloud with explicit per-job approval on 2026-11-21.

## Goal

Create bounded coding jobs, approve the exact source snapshot/limits, run Codex in an isolated copy, and return reviewable diffs plus actual verification evidence without changing the source repository. Persist queue state across restarts and support cancellation, leases and finite budgets.

## Decisions

- First adapter is installed Codex CLI (`codex exec --json`); no desktop chat automation. Cloud coding is separately enabled from chat cloud routing, and each job requires a disclosure/action approval.
- Use a filtered independent snapshot repository instead of a linked worktree: original Git objects may contain personal conversations/runtime databases, and worktrees share those objects. Snapshot selected source files only, retain content hashes/HEAD/dirty status, and never copy `.env`, personal data, credentials, symlinks/reparse points, `.git`, runtime state, vendor directories or tool hooks/config.
- Each job is created in waiting_for_approval. Approval binds objective, selected paths, exact file hashes, check profiles, provider/CLI default model selection, timeout and token budget. No background work begins from chat/model output or unapproved jobs.
- Codex uses a custom filesystem permission profile: deny disk by default, allow minimal tool runtime reads, allow only the job workspace writes and deny command networking. Ignore user/project config/hooks/rules; preserve existing provider login only for the trusted Codex process. Never bypass sandbox/approvals on failure. Preflight actual write/read/network boundaries before enabling execution.
- Only named trusted acceptance profiles are available; no raw shell strings. Agent and check processes run under the same OS sandbox. Tests use installed dependencies, do not auto-install packages and report missing dependencies as errors.
- Durable jobs use worker leases/heartbeats, explicit cancellation/deadline/output/token limits and process-tree termination. Expired runs become interrupted and require explicit approval of a new attempt; they are not blindly replayed.
- Artifacts include base manifest, changed files, patch, agent result/usage/events, check exit codes/output and failure/limitation notes. Mark completion separately from passing checks. No automatic apply, commit, push, merge or deploy to the owner repository.

## Verification

Test owner/approval/idempotency isolation, path traversal/link/secret exclusions, unchanged source data, changed-snapshot detection, concurrency/leases/restart/cancel, sandbox fail-closed behavior, artifact path bounds, untracked diffs and truthful check results. Run complete backend/frontend checks. Exercise a small synthetic Git repository through the actual installed Codex adapter after explicit bounded job approval, and validate actual sandbox boundaries using generated canaries only.

## Result

See `docs/PHASE_4_CODING.md` and the progress tracker for verification evidence. Synthetic queue/API/UI/worker tests pass. Native preflight fails on this host before cloud source disclosure; no live coding success is claimed.
