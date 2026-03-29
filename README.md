# LinkedIn Content Automation System

An end-to-end AI-powered pipeline that generates, audits, and publishes LinkedIn content automatically — with human review as the only required manual step.

Built to turn engineering project writeups into a consistent, high-quality LinkedIn presence without manual content work.

---

## What It Does

```
New project writeup dropped in folder
        ↓  Saturday (automatic)
AI generates full post batch → drafts.md
        ↓  Sunday (automatic)
Auditor scores quality, auto-regenerates failures
        ↓  Manual — owner reviews and approves
Image planner + renderer → post-N.png
        ↓  Sunday (automatic)
Image auditor checks visuals, flags/regenerates bad images
        ↓  Mon–Fri 9 AM WAT (automatic)
Runner posts each approved draft on its scheduled date
```

---

## Key Features

- **AI post generation** — Claude AI reads a project writeup and generates a full serialised post series in one run, maintaining narrative consistency across all posts
- **Dual-mode auditor** — automatically switches between draft quality audit (scores on 5 checks, applies threshold logic for regeneration) and image audit (tracks IMAGE PASSED state to avoid re-auditing)
- **Deterministic regeneration logic** — Python applies thresholds to decide no regen / selective regen / full batch regen / escalate. Claude writes scores only; it never decides what to regenerate
- **Local diagram rendering** — Mermaid diagrams rendered via `mmdc` at 2400px then downscaled to 1200×644px for sharp LinkedIn images (no upscaling blur)
- **Google Drive sync** — key files synced to Drive automatically after every run for remote access
- **Hard safeguard** — `AUDITOR APPROVED` never triggers posting. Owner must manually change status to `APPROVED`. Runner only posts `APPROVED` drafts

---

## Stack

| Component | Technology |
|-----------|-----------|
| AI Engine | Claude Sonnet (via Claude CLI) |
| Scripting | Python 3 |
| LinkedIn API | LinkedIn MCP server (Node.js) |
| Image Rendering | mmdc (Mermaid CLI v11.12.0) + Pillow |
| Google Drive | gdrive MCP + custom sync module |
| Scheduling | Windows Task Scheduler |
| Credentials | Windows System Environment Variables |

---

## File Structure

```
├── linkedin_generator.py        # Generates post batches from project writeups
├── linkedin_auditor.py          # Audits drafts + images, auto-regenerates
├── linkedin_image_planner.py    # Reads approved drafts, writes image-plan.json
├── linkedin_image_gen.py        # Renders Mermaid diagram images via mmdc
├── linkedin_image_post.py       # Posts text + image to LinkedIn
├── linkedin_runner.py           # Daily poster — reads schedule, posts approved drafts
├── linkedin_drive_sync.py       # Google Drive sync utility
│
├── LINKEDIN-GENERATOR-WORKFLOW.md   # Claude prompt: generation rules
├── LINKEDIN-AUDITOR-WORKFLOW.md     # Claude prompt: audit scoring rules
├── LINKEDIN-IMAGE-GEN-WORKFLOW.md   # Claude prompt: image planning + generation
├── LINKEDIN-POSTING-WORKFLOW.md     # Claude prompt: daily posting instructions
│
├── linkedin_mcp_config.json     # MCP config: LinkedIn + filesystem + Drive
├── auditor_mcp_config.json      # MCP config: filesystem only (faster auditor startup)
│
├── content-strategy.md          # Persona, post types, tone, formatting rules
├── content-guidelines.md        # Detailed writing rules (read by generator + auditor)
├── LinkedIn_Automation_System_Reference.md  # Full system reference doc
└── state_of_things_log.txt      # Change log + planned improvements
```

---

## Automated Schedule

| Task | Script | Schedule |
|------|--------|----------|
| Post generation | `linkedin_generator.py` | Every Saturday |
| Draft + image audit | `linkedin_auditor.py` | Every Sunday |
| Daily posting | `linkedin_runner.py` | Mon–Fri 9 AM WAT |

Each script has a hard day guard — if Task Scheduler fires on the wrong day, the script exits immediately without taking any action.

---

## Status Lifecycle

```
PENDING REVIEW → AUDITOR APPROVED → (manual) APPROVED → POSTED
```

Images tracked separately in `image-log.md`:
```
GENERATED → IMAGE PASSED / IMAGE FLAGGED
```

---

## Setup Requirements

- Python 3.x with `Pillow` installed
- Node.js + `mmdc` installed globally (`npm install -g @mermaid-js/mermaid-cli`)
- Claude CLI installed and authenticated
- LinkedIn MCP server configured
- Google Drive MCP server configured (optional — for Drive sync)
- `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_ID` set as Windows System Environment Variables
- Windows Task Scheduler entries for the three automated tasks

See [LinkedIn_Automation_System_Reference.md](LinkedIn_Automation_System_Reference.md) for full setup and operations documentation.

---

## Roadmap

- [ ] Audit batching — split large draft sets into groups of 5–6 per Claude CLI call
- [ ] Status dashboard — read-only pipeline state viewer with recommendations
- [ ] Approval notifications — Windows toast when auditor marks drafts ready
- [ ] LinkedIn engagement pull — log likes/comments/views per post, feed back into generator
- [ ] Cloud migration — remove dependency on local machine being online

---

*Built by Theresa Erhumwunse — March 2026*
