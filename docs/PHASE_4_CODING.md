# Phase 4: approved Codex coding jobs

TARS can prepare a filtered copy of selected source files, ask for approval, queue it durably, and return a patch plus verification evidence. It never applies the patch to the original repository. The first adapter uses Codex cloud through the installed CLI and its existing official login. Chat and personal-memory routing remain separately local.

## Current verification status

The queue, approval boundary, isolated snapshot, worker lifecycle, API and review UI are implemented and tested. **Live cloud execution is blocked on this host.** Both the bundled Codex CLI and an official standalone npm installation fail the actual sandbox probe with:

```text
windows sandbox failed: app runtime provisioning service is unavailable; refusing helper fallback
```

The standalone local app-server daemon was installed/started using the official CLI, but this did not resolve provisioning. No cloud coding job or live acceptance run is claimed. No source was sent to Codex during these canary probes. A failed per-job probe stops execution before invoking the cloud agent. Do not bypass the sandbox or remove managed runtime restrictions to make the demo pass. Repair the supported desktop/runtime provisioning environment and rerun the probe; then validate a synthetic repository before approving real source.

## Configuration and startup

The owner selected **Codex cloud with explicit job approval** on 2026-11-21. Private `.env` has `CODING_ALLOW_CLOUD=true`; the example defaults to false. This is independent of `ALLOW_CLOUD` for chat. Set `CODING_CODEX_EXECUTABLE` to an absolute native CLI executable if the PATH entry points to an incomplete desktop package. This host uses the ignored `.runtime/codex-cli/` installation of `@openai/codex` 0.171.0. No API key was created or copied. Account availability and provider charges depend on the existing Codex account.

Optional `CODING_REPOSITORIES` is a JSON object mapping public aliases to trusted absolute local Git repository roots. The default alias `tars` points to this repository. Requests cannot choose arbitrary absolute paths.

Run from the repository root with the parent virtual environment:

```powershell
& ../.venv/Scripts/python.exe -m src.jobs.worker
```

For a hidden background worker, run `scripts/start-coding-worker.ps1`. The existing `scripts/start-local.ps1` also starts it. Worker PID and logs are in ignored `.runtime/`. Run the worker in the same supported runtime environment as the backend. The worker is a separate process, not an HTTP request or model-generated shell command. `--once` claims at most one queued job for diagnostics. A disabled cloud setting prevents claims.

## Owner flow

1. Open **Coding jobs** in the sidebar and check sandbox readiness. The probe uses generated canaries, never owner files.
2. Choose a registered repository, concrete objective and narrow relative source paths. Select named verification profiles and bounded time/token limits.
3. Prepare a snapshot. This does not start cloud execution. Inspect the exact file list and source previews; selected files include current working-tree edits. Known private/runtime/config/vendor paths, binary files and links are excluded. Filtering is not comprehensive secret detection: inspect inline source secrets yourself before disclosure.
4. Tick the cloud disclosure checkbox and approve the exact snapshot. Changes to the copy require preparing and approving a new job. No chat text or model output can approve it.
5. Inspect status, errors, changed files, patch and check outputs. Download the patch for manual review/application. To retry, prepare a new job and approve it separately; interrupted jobs never replay automatically.

Deadlines include preflight, generation and acceptance checks. Python syntax checks parse source; they do not prove behavior. `python-unittest` and `pytest` run the copied tests using already installed dependencies. Missing dependencies are a failed check; installation/network access is not automatic. A completed run is not independent proof that the objective is correct. The model is the Codex CLI/account default with user configuration ignored; no particular model version is guaranteed. Token budgets are checked against observed provider usage events, **not a hard spending cap** and cannot prevent costs already incurred.

## Isolation and lifecycle

- Each job has a UUID folder under `.runtime/coding/jobs/` with `baseline/`, `workspace/`, `manifest.json`, `preflight/` and `artifacts/`. The separate Git metadata has no original objects or history. This avoids the private history exposure of shared-object linked worktrees.
- Approval hashes bind the manifest and job contract, including objective, source paths, provider, checks and budgets. Source previews come from the immutable baseline, not a model-selected arbitrary path.
- Codex ignores user configuration/rules, disables extra integrations/hooks/subagents, filters inherited environment variables, and uses a deny-by-default filesystem policy with minimal runtime reads and job workspace writes. Command networking is disabled. The trusted CLI still uses its official provider authentication for the cloud request; that authentication is not copied into the job.
- The probe must demonstrate allowed workspace writing and denied outside reads/writes/networking. Both coding and executable acceptance checks use the required native sandbox. No full-access fallback exists.
- A 45-second renewable lease and process heartbeat track execution. Cancellation, elapsed deadlines and bounded output terminate the process tree. Restarted workers mark expired active jobs interrupted and require a newly approved attempt.
- Results include patch, hashes, check exit codes/output, sandbox evidence, agent usage/events, and truthful limitations. List polling omits large result bodies; detail fetches retrieve the selected result.

Runtime snapshots and artifacts contain source and remain private. Retention/deletion UI and automatic patch application are outside this phase. Avoid publishing `.runtime/` or its logs. External credential provisioning, Claude Code adapter, voice, telephony and autonomous schedules remain later work.

## Storage and recovery

The canonical repository gains additive `coding_jobs` and `coding_events` tables. Back up SQLite with its online backup API before activating the new worker/backend. No historical conversation import, rewrite or private data deletion is required. Rollback: stop the worker, revert application code, and leave the additive tables and private job folders inert; restore the pre-change backup only if needed, considering any newer owner data. Do not delete the memory database to reset coding jobs.

## Validation

Deterministic verification: `python -m pytest tests -q` (62 tests), and frontend `npm run test` (9 tests), `npm run typecheck`, `npm run lint`, `npm run build`. Mocked adapters exercise success/failure evidence without cloud access. Subprocess tests exercise actual deadlines/output bounds and stream completion. API/UI tests exercise explicit approval and source inspection. The seven existing Fast Refresh warnings, Chroma deprecation warning and build advisory warnings remain. Live sandbox/cloud integration is pending as described above.

Permission design references: [Codex permissions](https://learn.chatgpt.com/docs/permissions), [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox), [Codex sandbox design](https://openai.com/index/inside-the-codex-sandbox/).

Live local API verification also passed: unauthenticated access denied, empty-source snapshot prepared and inspected, then cancelled without any cloud approval. Original conversation JSON hashes were unchanged. An online memory backup was retained before activating the backend and worker; both services are running on the local host.
