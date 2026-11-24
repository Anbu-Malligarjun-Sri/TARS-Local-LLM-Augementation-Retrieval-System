# Companion R0 · US visitor demo

Decision record · 24 November 2026. This is the release scope for the first visitor experience. The working software today is the paired desktop assistant. The public demo needs its own build, session service and deployment. [Master roadmap](COMPANION_MASTER_ROADMAP.md)

## Release decisions

| Item | Decision | Evidence needed to change it |
| --- | --- | --- |
| Buyer | US market. Start with adults trying an English or Tamil conversation on a phone or laptop. English landing copy and equal access to Tamil conversation. | Observe actual device, language and accessibility needs in the pilot. |
| Price | Owner's target range is USD 49–125. Use USD 99 as an internal worksheet scenario. | Price the landed hardware, assembly, fulfilment, returns, warranty, payment fees and included inference per unit. Select a shipping price only after pilot measurements. |
| Spend | Plan for INR 2,000 per month across demo hosting and inference. Absolute monthly ceiling INR 3,000 inclusive of other demo costs. Local R0 uses the installed Qwen model. | Obtain provider quotes and measure traffic before enabling a paid route. |
| Visitor identity | Anonymous, short visit, no owner login. One random session credential per visitor. Proposed maximum 15 minutes and five turns per visit. | Two-browser isolation and expiry checks on the deployed hostname. |
| Retention | R1 design keeps text and visit facts in volatile session memory for at most 15 minutes. Clear on expiry or end visit. Exclude prompt bodies and raw audio from analytics, errors and standard access logs. | Verify cleanup even for idle visitors and verify provider retention before making a public privacy claim. |
| Purchase interest | Separate optional email consent and storage, independent of chat. Start with a waitlist after the demo passes staging. | Real hardware footage, shipping plan and priced BOM precede paid orders. |

## Public capability allowlist for R1

| Visitor action | Allowed data and effect | Verification before release |
| --- | --- | --- |
| Start or end a visit | Issue or revoke an opaque, short-lived visitor cookie. No visitor-supplied account ID. | Two visitors cannot read, stop, resume or extend each other's sessions. |
| Type, review a transcript, receive a reply | Only this visit's bounded messages enter the selected model. Show the simulated face in listening, thinking, speaking or idle state using real interaction events. | Switch languages mid-session, deny the microphone, disconnect during streaming, and continue using text. |
| Teach and recall a visit fact | Use a synthetic detail such as a fictional project nickname. Scope recall to the current visit. | A fresh visit cannot recall the nickname. Expiry clears context and derivatives. |
| Stop | Abort local playback and the visitor's turn, discard late chunks and reconcile its reserved budget. | Stop before first token, during audio and twice in succession. |
| Join waitlist | Submit only the address and specific opt-in in a separate flow. | Unsubscribe and delete the address without requiring a chat transcript. |

All other actions are outside the visitor API. In particular, the visitor service has no filesystem path, database credential, network route or tool grant to reach owner chat, personal memory, research, coding jobs, app accounts, robot control or payment operations. CI should check the demo build manifest as well as HTTP routes. Persona text alone cannot enforce isolation.

## Cost worksheet

Record actual invoice rates in INR including conversion, taxes and fees. Start metered comparison with measured text-only turns. Quote the speech route separately. An always-on GPU would also need a fixed hosting line even when there are no visitors.

| Monthly line | Calculation |
| --- | --- |
| Fixed | Hosting + domain allocation + monitoring + storage minimums |
| Text per turn | (Input tokens including history × input price per million + maximum output tokens × output price per million) / 1,000,000 |
| Speech per turn | Allowed audio minutes × recognition rate + allowed output characters × synthesis rate per character |
| Admissible paid turns | Floor of (monthly ceiling − fixed costs − contingency − committed spend − outstanding reservations) / worst-case per-turn cost. Clamp to zero. |
| Hardware margin at USD 99 | 99 − landed unit cost − fulfilment − warranty/returns allowance − fees − included service cost. Repeat at 49 and 125. |

**Illustrative planning case.** At ₹600 fixed, ₹400 contingency and ₹1 reserved per turn, the ₹2,000 target supports 1,000 turns, or 200 full five-turn visits. The ₹3,000 ceiling supports at most 2,000 turns under the same assumptions. These inputs are examples, not vendor quotes. Record fixed charges even if nobody visits. If rates are unknown, deny paid admission. Reserve atomically before provider dispatch, settle on measured use, and retain the worst-case reservation after an ambiguous failure. Include preview/staging traffic in the same monthly budget. Stop admitting paid turns at the operating target unless the owner enables headroom within the ceiling. Pair this with provider-side limits where available.

## Asset and privacy inventory

| Input | Local R0 use | Public release decision |
| --- | --- | --- |
| Existing TARS name, movie-derived dialogue, images, enclosure likeness and training files | Private desktop baseline | Exclude from public build. Commission original name, art, voice and examples with documented rights. |
| Qwen 3.5 9B and Nomic weights in LM Studio | Installed locally. The synthetic scripts use Qwen only. | No weights bundled. Record exact artifact, model card, upstream license, attribution and hosting provider terms before public use. |
| Browser/OS recognition and installed voices | Recognition needs separate consent. Playback selects an installed local voice by sentence language. | Confirm English and Tamil availability, disclosure, distribution rights for any packaged voice, accessibility and text fallback on supported devices. |
| Synthetic scripts in this repository | Original evaluation prompts, no account data, no raw audio. | Keep evaluation fixtures out of training. Write separate original prompts for visitor suggestions. |
| Owner SQL, Chroma, logs, credentials and source snapshots | Private operator data | Exclude from build context, public services, telemetry and support exports. Use a clean demo directory and service identity. |

## Run the baseline

From the repository root on Windows, use the existing launcher and pairing tab. The second command runs two interleaved-language conversations with fresh in-process memory, local inference, and retrieval disabled. It prints replies and returns a failure for a wrong dominant script or a detected malformed Tamil word mixed with Arabic or Bengali characters. Review factual quality, tone and quoted exceptions separately. The script performs no speech capture.

```powershell
.\scripts\start-local.ps1
..\.venv\Scripts\python.exe -m scripts.check_companion
```

In the desktop UI, type “Explain a solar panel in one sentence”, then “Explain that in Tamil”, then “What would happen on a cloudy day?” in the same conversation. For a voice check, select the microphone input language and review the recognized text. Ask for the other language and listen for the matching installed voice. Repeat with playback stopped mid-sentence. Record browser, OS, voice names, failures and time to first audible speech. [Phase 5 operator guide](PHASE_5_VOICE.md)

## Recorded baseline and release gate

On 24 November the local launcher loaded Qwen 3.5 9B and Nomic, the desktop UI and authenticated health endpoint responded with HTTP 200, and the running API schema advertised automatic reply language. All six Qwen turns had the expected dominant script. Full reply times were 30.3, 19.5, 9.1, 23.7, 8.7 and 10.3 seconds respectively, measured without retrieval or speech. The Tamil book-planning reply included a dry comparison in Tamil. The robot sleep-mode reply had a malformed mixed-script word, the identity reply invented an estimate, and the language-comparison reply invented a suffix example. These findings keep open-ended generated answers behind a quality gate for the sales demo. Compare another candidate on the same held-out scenarios, review factual answers and Tamil idiom with fluent reviewers, and measure actual browser speech on target devices before selecting a public model.

## Run the first R1 service unit

The separate visitor app currently implements only begin, inspect and end visit. It keeps a maximum of 64 active visits in one process and discards them after 15 minutes or restart. It accepts the dedicated host `visitor.localhost`. From the repository root, run one worker:

```powershell
..\.venv\Scripts\python.exe -m uvicorn demo.api:app --host 127.0.0.1 --port 8091
```

In a second terminal, use a disposable PowerShell web session. If the browser or OS does not resolve the development hostname, these commands connect to loopback and send the dedicated Host header:

```powershell
$visitHeaders = @{ Host = 'visitor.localhost:8091'; 'X-Demo-Client' = '1' }
$visitUrl = 'http://127.0.0.1:8091/demo/visit'
Invoke-RestMethod $visitUrl -Method Post -Headers $visitHeaders -SessionVariable demoVisit
Invoke-RestMethod $visitUrl -Headers $visitHeaders -WebSession $demoVisit
Invoke-RestMethod $visitUrl -Method Delete -Headers $visitHeaders -WebSession $demoVisit
```

**Next R1 unit.** Add visitor-bound create-turn streaming and Stop using a simulated provider first. Exercise cancellation before the first token, simultaneous requests at the quota ceiling and lost connections. Add spend reservations before enabling a paid provider. Attach the visitor UI after these checks pass. Hardware work starts with a USB display and physical stop button under R2.
