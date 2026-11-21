# Phase 5: persona, Tamil/English browser voice and Stop

Phase 5 adds versioned audience expression, an opt-in browser speech path, and a rectangular **STOP** control in place of Send during processing. Owner chat keeps the existing shared memory and governed tools. The Phase 4 Codex sandbox provisioning blocker remains independent and unresolved.

## Try it

Refresh TARS at `http://localhost:8081/` after the backend update. Enter a message: the Send rectangle becomes **STOP** while thinking or streaming. Stop retains received text, ignores late events, cancels the HTTP response and asks the server to cancel the known turn ID. It also aborts microphone capture and clears current/queued speech. It does not stop the whole server or unrelated coding jobs; use their individual Cancel actions.

Open the microphone icon (**Voice settings**). Tamil (India) is the initial speech language; English (India) is also available. Select the main language for each utterance. Mixed Tamil/English recognition depends on the browser service and is not guaranteed. No language package or voice is silently downloaded.

Read and enable the separate browser-provider speech disclosure, then click **Start microphone**. Browser permission is still required. Partial transcripts are shown; the final transcript enters the editable message field. Review it and Send. Optionally select **Send final transcript automatically** for subsequent single-utterance turns. Transcript review is the default. This choice never starts another recording automatically.

Replies to dictated messages play sentence by sentence through a matching local voice. The Local voice menu lists only browser-reported local services. If no local Tamil/English voice exists, the reply remains text; there is no silent remote TTS fallback. Select another language or install an appropriate local voice through your OS/browser separately. Ordinary typed replies do not automatically play.

**Interrupt and listen** stops the current turn/playback before opening a new single-utterance capture. Recording and playback do not run together. This is push-to-talk interruption with echo avoidance, not full-duplex acoustic echo cancellation or a wake-word listener. Capture ends on a final transcript, service end/error, Stop, or the 20-second maximum. Permission denial, no final speech, unsupported recognition and synthesis errors have text fallbacks. Muting, changing session/language/consent, closing the voice panel or unmounting stops capture/playback. It never opens the microphone merely because a page loads or a command palette opens settings.

## Speech privacy

Speech recognition uses the browser's Web Speech implementation. It may send audio to a browser/vendor service, independently of TARS's local LLM setting. The opt-in checkbox applies only to the current page session. TARS itself does not receive or store raw microphone audio. Sent transcripts are chat messages and follow the existing conversation retention rules; unsent drafts/partial transcripts remain in page state. Closing the page does not retroactively remove data already handled by a vendor.

Playback requires voices reporting `localService=true` and a matching primary language. Browser recognition availability, service access, installed voices and microphone permissions vary. See [SpeechRecognition documentation](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) and [localService documentation](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService). This phase does not claim fully offline STT, a cloned TARS voice, a hosted speech subscription, continuous background listening, or telephony.

## Audience policy

`src/personality/policy.py` contains `tars-persona-1`, strict per-turn style settings and reviewed examples. Owner style permits restrained dry humor; parent style is warm/respectful; professional/unknown style is neutral; friend humor needs explicit playful consent. Urgent/distress/code/citation detection suppresses humor, with a model instruction to handle sensitive cases the conservative classifier misses. Truthfulness is invariant; the legacy `honesty` API/settings key means directness. The UI Restraint slider is expression, not a privacy grant.

Audience selection starts a separate preview conversation. Previews cannot retrieve personal memory or the RAG corpus, invoke tools, or reuse owner/other-audience history. Their own preview history is retained. This is an owner-operated style preview, not a contact identity system or a real call. Contact authentication, overrides and real calls remain later work. A preview cannot authorize a tool by asking for it in its text. Owner messages still have their normal explicit command/tool behavior.

Persona instructions are composed per turn and travel through existing model adapters without changing shared system settings for another session. Model output is no longer randomly decorated with sarcastic prefixes, invented confidence or narrated cue lights. Markdown rendering also preserves emphasis/multiplication signs instead of treating arbitrary asterisk text as robot gestures. Provider-independent memory/personality does not guarantee identical wording or quality across models.

## Cancellation and transport

The browser now uses authenticated streaming SSE for chat, with client-chosen UUID turn IDs, abort signals, ID-bound message updates and late-event rejection. It does not require a WebSocket fallback to expose early cancellation. The legacy WebSocket endpoint remains available for existing clients. Device cookies and existing access/origin checks remain in effect.

The server acknowledges cancellation while a synchronous provider `next()` is blocked. It keeps that turn's capacity slot and conversation lock until the call returns, then safely closes the generator and saves partial output where applicable. It never closes a generator executing on another thread. A bounded pre-start cancellation tombstone handles Stop before server registration; reused turn IDs cannot replay generation.

This is cooperative provider cancellation: local display/audio stop immediately, while an already-running SDK/model call may continue until the next read or configured finite timeout. It is not a guaranteed GPU inference kill. Capacity is intentionally retained during drain to prevent abandoned calls accumulating. A queued turn in the same conversation waits for that drain. Personality settings save when the UI is idle and only when changed.

## Evidence and remaining acceptance gates

Deterministic backend tests cover held-out audience policy cases, strict schemas, private-preview/tool/history isolation, output preservation, pre-start cancellation and cancellation during a deliberately blocked provider call. Frontend tests exercise Send-to-Stop, Tamil transcript review, local playback, late-event rejection, split UTF-8 SSE, microphone consent/errors/timeouts, sentence/code-fence handling and bounded measured statistics. These tests mock browser speech; they are not microphone or acoustic evidence.

Three synthetic previews were exercised against the installed local Qwen model in an isolated evaluation database. The first pass exposed an invented log-access aside and a bracketed Tamil placeholder. Added explicit restrictions/reviewed examples and repeated all three: parent greeting was polite, friend reply concise with one aside, Tamil professional greeting natural. This is a small smoke test, not a comprehensive held-out generation evaluation. Final first-text times were 14,993 / 7,755 / 7,974 ms: median 7,974 ms, p95 14,993 ms, **n=3**. Results are private operator artifacts under `.runtime/phase5-evaluation/`; no owner memory was used.

The voice settings panel reports actual page-session timing samples (up to 50 per metric), sample count, median and p95 for request-to-first-text, request-to-first-utterance-start, available speech-end-to-final-transcript intervals and local stop API dispatch. No sample means no result. Dispatch timing is not acoustic silence or server shutdown. No end-to-end microphone/noise/code-switching or acoustic latency target has been measured or agreed yet. Evaluate those on the owner's actual browser/hardware before claiming Phase 5 operational acceptance.

Run `python -m pytest tests -q` and frontend `npm run test`, `npm run typecheck`, `npm run lint`, `npm run build`. Preserve the existing lint/build advisory baseline. No schema migration is required for persona: audience is recorded in existing user-message metadata. Back up canonical memory/foundation SQLite files before restarting the backend. Rollback stops the updated backend and reverts source; preserve conversations/backups and runtime artifacts.

Final verification: 80 backend tests, 19 frontend tests, TypeScript/lint/build passed (seven existing lint warnings). A live authenticated Stop probe before first token acknowledged in 32 ms (one sample), then drained the provider safely. Its synthetic turn was removed afterward; original conversation JSON hashes were unchanged. The backend and frontend are running locally.
