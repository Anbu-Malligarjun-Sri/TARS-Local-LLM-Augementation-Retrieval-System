# Phase 5: audience persona, browser voice and immediate Stop

Status: local units 14–15 implemented; microphone/acoustic/browser acceptance remains pending. Phase 4's sandbox integration gate remains open independently.

## Contract

- A versioned deterministic persona policy resolves owner/parent/friend/professional/unknown style; friends need explicit playful consent. Sensitive/urgent/code requests suppress jokes. Honesty is invariant; legacy honesty settings mean directness. No random prefix/suffix/cue-light modifications to model output.
- Audience preview is not caller authentication. Non-owner previews have no personal memory/history or tools and use dedicated conversations; changing a style never authorizes access. Contact identity and carrier connections remain Phase 6.
- Per-turn persona context avoids mutating shared provider settings. Existing provider-independent memory remains available only to owner conversations. Held-out fixtures check policy and prompts, while live output evaluations are reported separately.
- Replace Send with a labeled rectangular Stop control while thinking/streaming. Cancel before first token, abort REST streams, discard late events, retain partial text, stop playback and recognition. Report cancellation failures truthfully.
- Browser voice uses Web Speech recognition interim/final transcripts and sentence-level local speech synthesis. Require an explicit browser-service audio disclosure checkbox and user microphone action; owner selected Tamil and English; initial Tamil (India), with English (India) selectable. Do not claim vendor recognition is offline. Final transcript review is the default; automatic send is a separate option. No raw audio is stored by TARS. Unsupported browser/service/permission/no-speech errors retain text fallback.
- Push-to-talk avoids speaker echo by cancelling playback before recording. Explicit interrupt-and-listen is supported; no full-duplex acoustic echo cancellation or continuous background listening is claimed. Silence/max-duration bounds, teardown/session/mute cleanup, bounded speech queues and code/URL suppression are required.
- Measure first text, first actual speech start, recognition finalization and local interruption timings; bounded local samples report median/p95 with sample counts. Synthetic timing tests are not acoustic benchmarks. Actual microphone/language/noise and provider quality remain owner evaluation gates.

## Verification

Backend owner/preview isolation, tone consent/urgency/formatting and cancellation while providers block; frontend send-to-Stop transition, late event containment, credentialed cancellable SSE, mocked recognition/playback cleanup, local-only voice selection and metrics. Run full deterministic suites, typecheck/lint/build; preserve existing data and back up before activating runtime changes. No real calls or speech vendor activity without owner action.
