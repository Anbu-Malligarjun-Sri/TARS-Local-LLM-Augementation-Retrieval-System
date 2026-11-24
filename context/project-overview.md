# TARS personal intelligence

The companion targets US buyers at USD 49–125. The demo operating target is INR 2,000/month with a hard ceiling of INR 3,000/month. [R0 decisions and release gates](../docs/COMPANION_R0_RELEASE.md)

**Product direction · 23 November 2026.** The [companion robot master roadmap](../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

## Overview

Build a persistent personal assistant for the owner: JARVIS-like usefulness with TARS-inspired dry humor. It helps with routines, research and projects, delegates programming to coding agents, converses through text/voice, and eventually handles inbound and approved outbound phone calls. Identity, personal memory and permission policy belong to TARS's application layer, independent of the selected local or cloud model.

This is a migration of an existing Python/FastAPI + React/Vite chatbot, not a greenfield rewrite. As of 2026-11-21, Phase 1 private chat and the local Phase 2 memory path are implemented: durable history, source-linked owner facts, correction/forget, relationship inspection and shared retrieval. External graph-service integration and live memory-quality gates remain pending. Other target capabilities below remain planned.

## Goals

1. Preserve relevant personal facts and project context across sessions, restarts and model switches.
2. Make every remembered fact inspectable, correctable and removable, with provenance.
3. Maintain a recognizable character while using respectful parent, playful friend and professional contact policies.
4. Complete useful tasks through scoped tools, with real results and failure reporting.
5. Enable natural interruptible voice before deploying a phone assistant.
6. Interrupt the owner only under configured routine/urgency rules, with quiet hours and a stop switch.

## Core user flow

1. Owner connects an authenticated private device and configures allowed models/privacy.
2. Owner chats and adds preferences, contacts and projects; TARS proposes or records sourced memories according to policy.
3. TARS retrieves only relevant audience-authorized memories and chooses an eligible model.
4. TARS answers, researches or proposes/executes a permitted tool action.
5. Long coding tasks run as durable jobs; owner receives diffs and test evidence.
6. Owner inspects and corrects memory and grants through the control panel.
7. Later, a known/unknown caller reaches a test number; TARS introduces itself, adapts tone, takes a message or escalates.
8. Approved routines generate notifications or owner calls, with an explanation of the trigger.

## Features

| Category | Scope |
| --- | --- |
| Conversation | Provider-independent sessions, streaming/cancellation, consistent persona |
| Memory | Events, sourced claims, relationship graph, semantic documents, correction/forget/export |
| Assistance | Current web research, project/task tracking, scoped calendar integration |
| Coding | Codex/Claude worker adapters, isolated repository access, artifacts and test results |
| Voice | Streaming speech recognition/synthesis, interruption, contact language preferences |
| Phone | Inbound screening, respectful/playful/professional modes, transfer/message fallback; approved outbound |
| Routines | Durable schedules, quiet hours, deduplication, escalation and budgets |

## Scope

In scope: one owner's assistant with multiple devices and separate contact audiences; model portability; incremental reuse of existing code; graph-backed memory; explicit action permissions.

Outside the initial scope: humanoid hardware, multi-tenant SaaS, autonomous spending, unrestricted code execution, pretending to be the owner, universal device/SIM control, training a foundation model, or continuous unrequested surveillance. Fine-tuning is optional after evaluations, not the starting point.

## Success criteria

- A fact learned through one model is correctly retrieved through another after restart, with the original source.
- A corrected fact supersedes the old one; a forgotten fact is excluded from active retrieval and derived indexes.
- Parent/friend/professional scenarios produce appropriate tone without changing privacy permissions.
- A project task produces a reviewable code diff and truthful test result.
- A test call can be handled or safely diverted during model/worker failure.
- A scheduled reminder survives restart without duplicate notification or redial.

See [architecture plan](../docs/TARS_ARCHITECTURE_PLAN.md) for audit evidence, proposed thresholds and phase gates. See [progress tracker](progress-tracker.md) for actual implementation state.

## Current delivery

Phase 1 private chat and local Phase 2 memory are implemented. Durable history, sourced owner facts, correction/forget, relationship inspection and shared retrieval are available. External graph deployment and live semantic-quality gates remain pending; later assistant/phone phases remain planned.


## Phase 3 delivery

Governed public web research, projects/tasks and the selected local ICS read-only integration are implemented. Tools & projects exposes concrete action review, sources, read grants and activity. Chat supports explicit research/fetch/projects/tasks/calendar read intents; autonomous model planning and coding delegation remain future phases. The owner still needs to import their own `.ics` snapshot for personal calendar data.


## Phase 4 delivery and limitation

Approved durable coding jobs, filtered isolated source snapshots, first Codex cloud adapter and diff/check review UI are implemented. The owner chose Codex cloud with explicit job approval; personal chat/memory stay under their existing local policy. Actual coding execution is blocked by Windows Codex sandbox provisioning and fails before cloud source disclosure. Local tests are not proof of live Codex integration. See `docs/PHASE_4_CODING.md`; persona/voice/phone work remains future scope.


## Phase 5 delivery and limits

Audience persona previews, opt-in Tamil/English browser speech, local sentence playback and rectangular Stop are implemented. Sent speech uses the same owner chat/memory path; previews have no private owner context/tools. Browser recognition may use a vendor service with separate explicit consent. Real microphone/voice availability, mixed-language accuracy and acoustic latency remain unverified acceptance gates; no carrier/phone integration is claimed. See `docs/PHASE_5_VOICE.md`.
