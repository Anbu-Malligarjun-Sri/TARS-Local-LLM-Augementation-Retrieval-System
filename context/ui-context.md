# UI context

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

Replace fixed RAG “SYNCED”, LLM “ACTIVE”, simulated CPU, hard-coded confidence and “DATA ARCHIVES” labels with measured data or unavailable states. Disable mic until a real audio capability exists. Settings without backend semantics must be disabled or clearly labeled unavailable. A source label means traceable evidence; it is not decoration.

Approval UI shows the concrete action, target, relevant content/diff and scope. A broad “trust” slider cannot grant permission. Disclose cloud routing and missing/degraded capabilities in user language. Preserve useful personality without sarcastic errors that obscure recovery steps.

## Implemented memory surface

Personal memory opens a dialog for facts/search, source inspection, cloud opt-in, correction, confirmed forget, export and rebuild. Relationship inspection uses a directed edge table with node count; a graph canvas is not implemented. Memory status shows backend/model/local projection lag. Retention notes separate facts from transcripts/backups. Imported server sessions appear in chat history.
