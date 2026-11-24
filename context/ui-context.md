# UI context

**Product direction · 23 November 2026.** The [companion robot master roadmap](../docs/COMPANION_MASTER_ROADMAP.md) governs upcoming work. Start with R0 and the isolated public demo (R1), alongside the USB tabletop prototype (R2). Earlier phase records below describe the desktop baseline.

## Theme

Retain the existing dark terminal/HUD aesthetic: amber accents, restrained silver surfaces and a TARS monolith companion. Increase clarity and accessibility as real tools/memory/phone controls arrive. The UI should communicate actual operational state; cosmetic animation must not imply real microphone capture or successful model/database connectivity.

## Colors

Current source of truth: `frontend/src/index.css` and `frontend/tailwind.config.ts`. CSS variables contain HSL components and are used through `hsl(var(--token))` / Tailwind semantic classes.

| Role | CSS token | Existing value |
| --- | --- | --- |
| Background | `--background` | `0 0% 4%` |
| Surface | `--card`, `--tars-dark` | `0 0% 8%` |
| Raised surface | `--secondary` | `0 0% 16%` |
| Primary text | `--foreground` | `0 0% 94%` |
| Muted text | `--muted-foreground` | `0 0% 55%` |
| Primary accent | `--primary`, `--tars-amber` | `37 100% 50%` |
| Information | `--tars-blue` | `200 80% 55%` |
| Success | `--tars-green` | `145 70% 45%` |
| Error | `--destructive`, `--tars-red` | `0 72% 51%` |
| Border | `--border` | `0 0% 18%` |

## Typography and shape

Inter for general UI; JetBrains Mono for terminal, code and short status labels. Existing `--radius` is `0.25rem`; use established `rounded`/semantic radius classes. Keep long reports and evidence readable; do not extend tiny HUD text to primary workflows. Avoid new hard-coded colors.

## Component library and layout

Reuse Radix/shadcn primitives in `frontend/src/components/ui/`, Lucide React icons and existing Tailwind utilities. Preserve the left monolith sidebar and central chat shell. Use accessible sheets/dialogs for secondary controls. Add keyboard labels, focus states, sufficient contrast and reduced-motion support. Voice/call actions need explicit text and keyboard access, not color alone.

## Planned surfaces

| Surface | Required information/actions |
| --- | --- |
| Conversation | Actual model/provider, source references, tool progress, cancel/retry, error states |
| Memory | Search/list and optional graph view; fact provenance, certainty status, correct/forget/export |
| Contacts | Relationship, language, tone override, disclosure permissions and identity confidence |
| Projects/jobs | Goal, state, allowed repository, artifacts/diff, test evidence, approval/cancel |
| Calls | Caller uncertainty, selected tone, live status, take over/end, transcript policy |
| Routines | Trigger/timezone, destination, quiet hours, next run, snooze/disable |
| Settings | Model/privacy eligibility, tested capabilities, cost limits, persona/directness |

## Truthful states

Replace fixed RAG “SYNCED”, LLM “ACTIVE”, simulated CPU, hard-coded confidence and “DATA ARCHIVES” labels with measured data or unavailable states. Offer microphone capture only through supported speech APIs, explicit disclosure/permission and a user start action. Settings without backend semantics must be disabled or clearly labeled unavailable. A source label means traceable evidence; it is not decoration.

Approval UI shows the concrete action, target, relevant content/diff and scope. A broad “trust” slider cannot grant permission. Disclose cloud routing and missing/degraded capabilities in user language. Preserve useful personality without sarcastic errors that obscure recovery steps.

## Implemented memory surface

Personal memory opens a dialog for facts/search, source inspection, cloud opt-in, correction, confirmed forget, export and rebuild. Relationship inspection uses a directed edge table with node count; a graph canvas is not implemented. Memory status shows backend/model/local projection lag. Retention notes separate facts from transcripts/backups. Imported server sessions appear in chat history.


## Implemented tools surface

Tools & projects opens a dialog with Projects, Research, Calendar, Permissions and Activity tabs. Local writes require a review of tool name and exact arguments followed by Approve and run. Retry preserves the request key; failures are shown, never labeled completed. Source URLs, retrieval times, source type and bounded evidence are inspectable. Calendar uses an explicit file picker, timezone, import review and snapshot freshness note. Archives/completions are recoverable through Show archived/Show completed. Source/model Markdown images are disabled; links remain explicit user actions.


## Implemented coding review surface

Coding jobs opens a dialog for repository alias, objective, selected paths, verification profiles, deadline and observed token budget. Prepare creates a local snapshot; file previews and cloud disclosure consent precede the separate Approve and queue action. Job history, cancellation, truthful failure/check states, patch download and agent/sandbox evidence are available. Readiness displays actual probe output; on this host sandbox provisioning currently blocks execution. No automatic source application or cloud success badge exists.


## Implemented Phase 5 surfaces

The send rectangle becomes a labeled amber STOP during thinking/streaming, capture or playback. It stops local audio/display and requests server cancellation. Voice settings includes Tamil/English language, local voice, non-persistent speech-provider consent, default transcript review, optional automatic final send, partial/error/status output, interrupt-and-listen and bounded measured timing statistics. No automatic recording or remote TTS fallback. The command palette opens settings, not the microphone. Audience selector creates separate owner/parent/friend/professional/unknown previews; friend playful consent is explicit. Preview label discloses no owner context/tools. Directness and Restraint sliders do not change truthfulness/access rules.

## Desktop voice update · 24 November 2026

The speech language menu is the microphone input locale. Typed and reviewed voice turns use automatic reply language. A request for Tamil or English applies to the current answer. Local playback follows the generated sentence and reports missing voices in the UI.
