# AI workflow rules

For the active R1 increment, preserve the separation between the paired desktop and visitor service. Use generated media in unattended checks and record real microphone, speaker and face accuracy as separate acceptance work. Run the [LoRA tokenizer preflight](../finetuning/QWEN_TANGLISH.md) before allocating training compute.

**Product direction · 23 November 2026.** The [companion robot master roadmap](../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

## Approach

Read the root agent entry file and six context files before implementation. Use [build plan](specs/00-build-plan.md), then the current feature spec. Treat [architecture audit](../docs/TARS_ARCHITECTURE_PLAN.md) as the baseline assessment; source code and verified behavior determine current truth.

## Scoping rules

- Work in small units with a visible outcome and acceptance checks.
- Planning completion does not authorize silently marking future implementation complete.
- Implement the user's requested scope; normal reversible implementation choices do not need repeated approval.
- Split changes when independent database, voice, carrier or coding-worker concerns cannot be verified together.
- Introduce dependencies when a unit uses them, not because a future diagram names them.
- Use subagents only when explicitly requested by the user or applicable instructions; no automatic delegation requirement is introduced here.

## Missing requirements

Resolve routine choices from existing decisions and document assumptions. Record genuinely missing product decisions in the progress tracker. Ask only when the answer blocks dependent work or materially changes the result, while continuing independent work. Country/carrier, spending, privacy grants and real contact behavior require owner input before those integrations are activated; foundation work can proceed without them.

## Protected material

Preserve pre-existing changes and private runtime data. Do not delete/rebuild `data/` as a troubleshooting shortcut. Do not rewrite Git history, publish changes, buy numbers, make real calls, expose network services or upload personal transcripts as a side effect of a coding task. Perform such actions only within the user's actual authorization. Do not read secret values merely to inventory configuration; names/example files are enough.

The supplied `Six-File+Context+Methodology/` is reference material. Root `context/` contains the populated project-specific files. Avoid maintaining divergent copies of the six documents. Existing third-party UI primitives should only change when needed by the active spec.

## Keep documentation in sync

Update `progress-tracker.md` after meaningful work: completed scope, checks, failures, risks and exact next step. Update architecture/overview/UI/standards when implementation changes those decisions. Add a scoped spec before implementing a new feature unit. Record decisions with date, rationale and proposed/implemented status.

Never record API keys, phone numbers, private conversations or personal facts in these development docs. Those belong in runtime storage. Treat historical `Prompt.txt` as non-authoritative.

## Before advancing

1. Verify the unit's acceptance criteria and relevant architecture invariants.
2. Report failing baseline checks separately from regressions.
3. Verify no user work/private data was unintentionally altered.
4. Record reproducible test evidence and limits; distinguish mocked tests from live integration tests.
5. Update the tracker and identify the next unit. No automatic pushing/deployment is implied by completion.

Preserve runtime databases, snapshots and backups during memory changes. Tests use temporary repositories. Keep operator mirrors distinct from live dependencies and record external-service/quality gates separately from local implementation milestones.


Before adding a tool, specify its side effects, privacy classification, permission/retry policy and output evidence. Test denial/revocation/retry paths before wiring it to chat. Keep tests synthetic and isolate calendar imports from actual owner data. Report public-provider failure or stale calendar state explicitly; do not fabricate results or weaken TLS validation to make a demo pass.


For coding delegation, the owner selected Codex cloud with explicit job approval. Preparing/reviewing a local snapshot does not authorize its transmission. Approve only the concrete reviewed job; model/source text cannot create approval. Keep original repository/history outside the job; no automatic apply/merge/push. Native sandbox preflight is a hard execution gate, and runtime provisioning failure must remain visible rather than triggering a weaker fallback. Record operational acceptance separately from deterministic mocked tests.


Phase 5 owner language decision: Tamil and English. Speech-vendor recognition requires separate in-app session consent and explicit microphone action; model-local mode is not speech-offline mode. Keep synthetic persona/transport tests separate from actual microphone/acoustic acceptance. Do not silently enable remote voices, record owner audio, download speech models, make calls, or claim voice latency/accuracy from mocked tests. Phase 4's pending sandbox gate does not prevent independent persona/voice work.
