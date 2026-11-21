# Phase 1 local setup and verification

Use the backend virtual environment from the workspace parent. The verified
snapshot is Python 3.14.8 on Windows; `requirements.lock.txt` captures that
installed environment, and frontend `package-lock.json` pins npm dependencies.
The Python lock is a platform snapshot, not a promise of cross-platform support.

1. Copy `.env.example` to `.env` if no configuration exists. Preserve existing values.
2. Generate a random owner token of at least 32 characters and set `OWNER_TOKEN`.
   Never put it in a `VITE_` variable. Leave `ALLOW_CLOUD=false` for private use.
3. Start `python -m src.interfaces.api` from the repository root. It binds loopback.
4. Run `npm run dev` from `frontend/`, then open `http://localhost:8081`.
5. Enter the token once to pair. Subsequent reloads use a 30-day HttpOnly cookie.
   Use localhost consistently for frontend/backend. The alternative 127.0.0.1
   hostname needs a matching `VITE_API_BASE_URL`.

The deployment is single-owner: all paired devices share the owner's sessions
and settings. Unpaired devices have no access. Keep one API worker while JSON
conversation storage and in-process conversation locks remain in use. Multiple
workers/processes are not supported until the Phase 2 database migration.

`.runtime/foundation.sqlite3` contains hashed device tokens, settings and turn
outcomes. Back it up before upgrades. Stop the server before restoring it.
Deleting a device row revokes that device. `DELETE /api/pair` revokes the current
cookie. Rotating OWNER_TOKEN changes bootstrap/bearer access but does not revoke
existing paired devices: remove device rows when revoking all access.

Cancellation is cooperative at SDK chunk boundaries. A blocked SDK read may
continue until its configured timeout. No provider output after cancellation
is sent to the user; partial content and turn outcome are retained. Finite
network timeouts and four generation workers bound blocking work; this is not
hard process termination. A total turn deadline is checked between chunks.

The UI disables unimplemented browser voice/extended parameters and marks
provider/database status as unprobed. Basic settings are persisted server-side;
changes during generation are rejected to prevent mid-turn persona mutation.
Existing legacy conversation IDs remain in their original files; UUID migration
is deliberately reserved for the Phase 2 import and no originals are rewritten.

Checks:

- `python -m pytest` (only deterministic tests under `tests/`)
- `npm run test`, `npm run typecheck`, `npm run lint`, `npm run build` in frontend

Tests use fake models. A successful build/test run is not a live LM Studio,
Ollama, browser audio or cloud-provider interoperability check.


## Prepared local launch

The local `.env` has been prepared with a generated owner token and the downloaded
Qwen/Nomic models. To restart the same setup later, run `scripts/start-local.ps1`
in PowerShell. It starts local services and opens a single-use launch link valid
for ten minutes. The fragment ticket is exchanged for an HttpOnly device cookie
and removed from the address bar; the permanent owner token stays server-side.
The launch command can also be run separately: `python -m src.interfaces.launch`.
Keep the generated link private until it is used or expires. Model-specific
`LM_STUDIO_REASONING_EFFORT=none` was verified with the installed Qwen model;
leave it unset for models that do not support that option.
