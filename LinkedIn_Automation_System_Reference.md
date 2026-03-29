# LinkedIn Content Automation System
## System Reference & Operations Manual
**Author:** Theresa Erhumwunse
**Version:** 2.0 — March 2026
**Next LinkedIn token refresh:** ~May 2026

---

## 1. System Overview

This system automatically generates and publishes LinkedIn content derived from real engineering projects. It reads completed project documents, produces a full batch of high-quality posts in one run, schedules them across working days, audits their quality, generates diagram images, and posts each one automatically at 9 AM WAT without manual intervention.

**Human review is the only required step before any post goes live.**

### How It Works

```
New project .md dropped in Project Completed\
        ↓  (Saturday — automatic)
linkedin_generator.py — generates full post batch → drafts.md (PENDING REVIEW)
        ↓  (Sunday — automatic)
linkedin_auditor.py — audits drafts, scores quality, auto-regenerates failures
        ↓  (manual — Theresa)
Review drafts.md — change AUDITOR APPROVED → APPROVED for each post you accept
        ↓  (manual — after approval)
linkedin_image_planner.py → image-plan.json
linkedin_image_gen.py     → images/post-N.png
        ↓  (Sunday — automatic, after images generated)
linkedin_auditor.py — IMAGE AUDIT mode — checks images, flags/regenerates bad ones
        ↓  (weekdays 9 AM WAT — automatic)
linkedin_runner.py — posts each APPROVED draft on its scheduled date
```

---

## 2. File Structure

All system files live in one folder:

```
C:\Users\pc\Documents\LinkedIn Project\
```

### Scripts

| File | Role | Runs |
|------|------|------|
| `linkedin_generator.py` | Generates post batches from project writeups | Saturdays (auto) |
| `linkedin_auditor.py` | Audits drafts + images, auto-regenerates failures | Sundays (auto) |
| `linkedin_image_planner.py` | Reads approved drafts, writes image-plan.json | Manual |
| `linkedin_image_gen.py` | Renders Mermaid diagram images via mmdc | Manual |
| `linkedin_image_post.py` | Posts text + image to LinkedIn | Called by runner |
| `linkedin_runner.py` | Daily poster — reads schedule, posts approved drafts | Mon–Fri 9 AM WAT |

### Workflow Docs (Claude reads these as prompts)

| File | Purpose |
|------|---------|
| `LINKEDIN-GENERATOR-WORKFLOW.md` | Generator instructions + banned words list |
| `LINKEDIN-AUDITOR-WORKFLOW.md` | Auditor scoring rules + regen logic |
| `LINKEDIN-IMAGE-GEN-WORKFLOW.md` | Image planning + generation instructions |
| `LINKEDIN-POSTING-WORKFLOW.md` | Daily posting instructions |

### Data Files

| File | Purpose |
|------|---------|
| `drafts.md` | All generated post drafts with statuses |
| `schedule.md` | Posting calendar with dates and statuses |
| `audit-log.md` | Record of all published posts |
| `audit-report.md` | Latest auditor run report |
| `generation-log.md` | Record of all generator runs |
| `image-log.md` | Record of image generation + image audit results |
| `image-plan.json` | Structured image specs for current batch |
| `audit-state.json` | Inter-run state for auditor (attempt number, failure patterns) |
| `drive-file-ids.json` | Maps local .md filenames to Google Drive file IDs |
| `content-strategy.md` | Persona, post types, tone, formatting rules |
| `content-guidelines.md` | Detailed writing guidelines (read by generator + auditor) |

### Config Files

| File | Purpose |
|------|---------|
| `linkedin_mcp_config.json` | MCP config for generator, runner, image planner, image post |
| `auditor_mcp_config.json` | MCP config for auditor only (local-files only — faster startup) |

### Folders

| Folder | Purpose |
|--------|---------|
| `Project Completed\` | Source .md project writeups for content generation |
| `images\` | Generated post images (`post-N.png`) |
| `run-logs\` | Timestamped logs from every script run |
| `Archive\` | Old/unused files |

---

## 3. MCP Servers

### linkedin_mcp_config.json
Used by: `linkedin_generator.py`, `linkedin_runner.py`, `linkedin_image_planner.py`, `linkedin_image_post.py`

Contains three MCP servers:
- **linkedin** — LinkedIn API via Node.js MCP server (`C:\Users\pc\linkedin-mcp\index.js`)
- **local-files** — filesystem access to project folder and Catalyst-Projects
- **gdrive-personal** — Google Drive read access via personal account MCP server

### auditor_mcp_config.json
Used by: `linkedin_auditor.py` only

Contains one MCP server:
- **local-files** — filesystem access only

> **Why separate?** The auditor does not need LinkedIn or Google Drive MCPs. Loading them added startup overhead that caused multi-hour hangs. The auditor uses local-files only and completes in 20–30 minutes.

---

## 4. LinkedIn Credentials

LinkedIn credentials are stored as **Windows System Environment Variables** — not in any config file.

| Variable | Value |
|----------|-------|
| `LINKEDIN_ACCESS_TOKEN` | Your current LinkedIn OAuth access token |
| `LINKEDIN_PERSON_ID` | Your LinkedIn member ID (`urn:li:person:...`) |

Scripts read these at runtime via `os.environ`. The LinkedIn MCP server inherits them automatically from the system environment. `linkedin_image_post.py` reads them directly.

> **Never put credentials back into JSON files.** If a script fails with a credentials error, check that the environment variables are set in Windows System Properties → Environment Variables (not user variables — system variables).

---

## 5. Automated Tasks (Windows Task Scheduler)

Three separate Task Scheduler entries. **Do not combine them.**

| Task | Script | Schedule | Day Guard |
|------|--------|----------|-----------|
| LinkedIn Generator | `linkedin_generator.py` | Saturday (any time) | Exits if not Saturday |
| LinkedIn Auditor | `linkedin_auditor.py` | Sunday (any time) | Exits if not Sunday |
| LinkedIn Daily Poster | `linkedin_runner.py` | Mon–Fri 9 AM WAT | Exits if weekend |

Each script has a hard day guard — if Task Scheduler fires on the wrong day, the script detects it and exits immediately without taking any action.

---

## 6. Status Lifecycle

### drafts.md statuses

```
PENDING REVIEW    → Generated, not yet audited
AUDITOR APPROVED  → Passed audit — Theresa must manually change to APPROVED
AUDITOR FLAGGED   → Failed audit, flagged for review
AUDITOR REJECTED  → Failed audit, rejected for regeneration
APPROVED          → Manually approved by Theresa — queued for posting
POSTED            → Published to LinkedIn
```

> **Critical safeguard:** `AUDITOR APPROVED` **never** triggers posting. Theresa must manually change it to `APPROVED`. The runner only posts drafts with status `APPROVED`. This safeguard remains until the auditor is validated across 5 projects.

### schedule.md statuses

```
POST PENDING  → Scheduled, not yet posted
POSTED        → Published
```

schedule.md uses only these two states. All approval tracking happens in drafts.md only.

### image-log.md audit statuses

```
GENERATED     → Image rendered successfully
REGENERATED   → Image re-rendered (supersedes prior entry)
SUPERSEDED    → Replaced by a newer generation run
IMAGE PASSED  → Passed image audit — auditor will skip on all future runs
IMAGE FLAGGED → Flagged by image audit — pending regeneration
```

---

## 7. LinkedIn Content Generator

**Script:** `linkedin_generator.py`
**Runs:** Every Saturday (any time) — Task Scheduler + on-demand

### What It Does

1. Confirms it is Saturday — exits immediately if not
2. Scans `Project Completed\` for any `.md` file not yet in `generation-log.md`
3. If a new project is found: invokes Claude CLI to generate the full post batch
4. If no new project is found: logs SKIP and exits cleanly
5. Writes all drafts to `drafts.md` as PENDING REVIEW
6. Updates `schedule.md` and `generation-log.md`
7. Syncs `drafts.md`, `schedule.md`, `generation-log.md` to Google Drive

Generation takes 10–20 minutes. Multiple Saturday time slots (9 AM, 12 PM, 6 PM) act as safety nets — if the first run already generated, later runs skip automatically.

---

## 8. LinkedIn Auditor

**Script:** `linkedin_auditor.py`
**Runs:** Every Sunday (any time) — Task Scheduler + on-demand

The auditor runs in **two mutually exclusive modes** selected automatically based on draft state.

### DRAFT AUDIT MODE
**Triggered when:** PENDING REVIEW drafts exist in drafts.md

1. Scores every PENDING REVIEW draft using a 5-check system (specificity, redundancy, voice, format, quality)
2. Marks each draft: AUDITOR APPROVED, AUDITOR FLAGGED, or AUDITOR REJECTED
3. Python calculates `pass_rate` and `avg_failed_checks_score` from audit output
4. Python applies threshold logic to decide regeneration mode:

| Condition | Mode |
|-----------|------|
| pass_rate = 100% | NONE — no regeneration |
| pass_rate ≥ 80% AND failed checks score ≥ 70% | SELECTIVE — regenerate only failed drafts |
| pass_rate < 50% OR failed checks score < 70% | FULL_BATCH — regenerate entire batch |
| pass_rate 50–79% | FULL_BATCH — too many failures |
| Attempt 3 of 3 with threshold not met | ESCALATE — notify Theresa |

5. Syncs `drafts.md` and `audit-report.md` to Google Drive

> **Regen logic is deterministic Python math — not Claude's judgement.** Claude writes scores only. Python applies thresholds.

### IMAGE AUDIT MODE
**Triggered when:** No PENDING REVIEW drafts exist

1. Gets all APPROVED (not POSTED) drafts
2. Checks `image-log.md` — skips any draft already marked `IMAGE PASSED`
3. Audits remaining images visually via Claude CLI
4. Writes results to `image-log.md` (IMAGE PASSED / IMAGE FLAGGED)
5. If any images flagged: auto-triggers `linkedin_image_gen.py --check` for regeneration
6. Re-audits regenerated images (Cycle 2)
7. If still failing after Cycle 2: logs for manual review
8. Syncs `audit-report.md` and `image-log.md` to Google Drive

> **Why separate modes?** Images are only generated after draft approval. Running image audit during draft audit would check images for drafts that may later be rewritten — wasted work.

### Timeout
Claude CLI calls have a 30-minute hard timeout (`TIMEOUT_SECONDS = 1800`). If hit, the run errors out with a clear message.

---

## 9. Image Generation System

**Scripts:** `linkedin_image_planner.py` → `linkedin_image_gen.py`
**Runs:** Manual (after you approve drafts)

### Renderer: mmdc (Mermaid CLI)

Images are rendered locally using `mmdc` (Mermaid CLI v11.12.0). **Kroki API is no longer used.**

Why mmdc:
- Renders at 2400px wide then scales down to 1200px — sharp output (no upscaling blur)
- Runs offline — diagram code never sent to an external server
- Full control over output dimensions

Prerequisite: `npm install -g @mermaid-js/mermaid-cli` (already installed)

### Image Dimensions

| Setting | Value |
|---------|-------|
| `TARGET_WIDTH` | 1200px (LinkedIn optimal) |
| `TARGET_HEIGHT` | 644px (LinkedIn max height) |
| `RENDER_WIDTH` | 2400px (2× for sharp downscale) |
| `CANVAS_PADDING` | 48px each side |
| Output | `images/post-N.png` at 300 DPI |

### Flagging Bad Images

Rename `post-N.png` → `post-N.review.png`, then run:
```
python linkedin_image_gen.py --check
```
- 0 or 1 flagged: regenerates flagged images only
- 2 or more flagged: regenerates entire batch for visual consistency

---

## 10. Google Drive Sync

**Script:** `linkedin_drive_sync.py` (utility module)

Automatically syncs key project files to Google Drive after each automated run.

| Script | Files Synced |
|--------|-------------|
| Generator | drafts.md, schedule.md, generation-log.md |
| Auditor (draft mode) | drafts.md, audit-report.md |
| Auditor (image mode) | audit-report.md, image-log.md |
| Runner | drafts.md, schedule.md, audit-log.md |

Files are mapped in `drive-file-ids.json` (filename → Google Drive file ID). First upload creates the file; subsequent runs update in place.

> **Note:** The gdrive MCP server (read-only) and Drive sync (write) are separate systems that coexist. The MCP server provides read access in Claude Desktop. The sync module provides write access from Python scripts.

**OAuth token location:** `C:\Users\pc\gdrive-personal-mcp\credentials\.gdrive-write-token.json`

---

## 11. Adding a New Project

### Step 1 — Create the project document

Create a new `.md` file in `Project Completed\`. Name it with the next number:
```
C:\Users\pc\Documents\LinkedIn Project\Project Completed\2 project-name.md
```

Include: what was built, tools used, specific errors encountered, fixes applied, real metrics, architecture decisions, lessons learned, and next steps. The more specific detail you include, the better the generated posts will be.

### Step 2 — Wait for Saturday

No manual command needed. The generator detects the new file automatically on the next Saturday run. It will:
- Audit how many posts the project can honestly support
- Calculate posting schedule (continuing from where the last project ended)
- Generate all posts in one continuous session for narrative consistency
- Write all drafts to `drafts.md` as PENDING REVIEW
- Update `schedule.md` and `generation-log.md`

### Step 3 — Wait for Sunday

The auditor runs Sunday. After it completes, open `drafts.md` and for each post you accept, change:
```
**Status:** AUDITOR APPROVED
```
to:
```
**Status:** APPROVED
```

### Step 4 — Generate images (manual)

After approving drafts, run in order:
```
python linkedin_image_planner.py
python linkedin_image_gen.py
```

Then wait for the next Sunday auditor run — it will auto-detect the new images and audit them (IMAGE AUDIT MODE).

### Step 5 — Posts go live automatically

The runner posts each APPROVED draft on its scheduled weekday at 9 AM WAT. No further action needed.

---

## 12. LinkedIn Token Refresh

Your LinkedIn access token expires approximately every 60 days.
**Next refresh due:** ~May 2026

### Step 1 — Get a new authorisation code

Open this URL in your browser:
```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=77f0dzmek6ht55&redirect_uri=http://localhost:8080/callback&scope=w_member_social%20openid%20profile%20email
```
Click Allow. Copy the full redirect URL. Extract the `code=` value.

### Step 2 — Exchange code for new token (run in Command Prompt)

```
curl -X POST "https://www.linkedin.com/oauth/v2/accessToken" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "grant_type=authorization_code&code=[YOUR_CODE]&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback&client_id=77f0dzmek6ht55&client_secret=WPL_AP1.u74vD7tQ045OdKUo.DyGjpw%3D%3D"
```

### Step 3 — Update Windows System Environment Variables

Go to: **Windows Search → "Edit the system environment variables" → Environment Variables → System variables**

Update `LINKEDIN_ACCESS_TOKEN` with the new `access_token` value from the response.

> Do **not** put the token in any JSON file. The MCP server and all scripts read it from the system environment automatically.

---

## 13. Content Quality Rules

### Banned Words and Phrases

The generator is prohibited from using these in any post body:

**AI Giveaway Words:** delve, unlock, unleash, harness, foster, elevate, revolutionize, transform, empower, underscore, interplay, synergy

**Navigational Phrases:** "In conclusion,", "Furthermore,", "Moreover,", "Additionally,", "In summary,", "To summarise,", "In essence,", "Firstly,", "Secondly,", "Thirdly,", "Finally,", "In closing,"

**Adjective Overload:** comprehensive, robust, dynamic, crucial, essential, innovative, cutting-edge, state-of-the-art, game-changing, next-level, world-class, best-in-class

**Helpful Assistant Vibe:** "Dive in", holistic, endeavor, demystify, "Let's explore", "It's worth noting", "It's important to", "I'm excited to", "I'm thrilled to", "Feel free to", "Don't hesitate to", "I hope this helps", "As an AI"

**Generic Closer Words:** realm, journey, navigate, beacon, catalyst (as descriptive word — allowed only as proper noun: Catalyst Case / Catalyst Lifestyle), empower, landscape, paradigm

### Series Continuity

Every post in a batch is part of a serialised build story. Three structural elements apply to every post:
- **Series label** — "Part N of X: [Series Title]"
- **Opening callback** — references the previous post (except Post 1)
- **Closing teaser** — hints at the next post (except the last post)

Context blocks written during generation are **never** included in the post text — internal reference only.

---

## 14. Current Posting Schedule (as of 2026-03-22)

### Project 1 — catalyst-cs-automation.md
- **Posts 1–15** (drafts 1–15)
- Posts 1–7: POSTED
- Posts 8–15: APPROVED — scheduled from next available weekday
- Images: posts 8–15 have `IMAGE PASSED` in image-log.md (bootstrap — approved before image audit system)

### Project 2 — linkedin-automation-system.md
- **Posts 16–33** (drafts 16–33)
- All 18 drafts: AUDITOR APPROVED — awaiting Theresa's manual approval
- Scheduled: 2026-04-10 to 2026-05-11
- Images: not yet generated — run image planner after approving drafts

---

## 15. Troubleshooting

### Auditor hangs / takes more than 30 minutes
- Check `run-logs\auditor-run-*.log` for the last output line
- If stuck mid-audit: Ctrl+C to kill, re-run — it will retry
- The 30-minute timeout (`TIMEOUT_SECONDS = 1800`) will kill stuck Claude CLI calls automatically
- Ensure `auditor_mcp_config.json` is being used (not the full linkedin_mcp_config.json)

### Generator finds no new project
- Confirm the `.md` file is in `Project Completed\` (not the root project folder)
- Confirm the filename is not already in `generation-log.md`
- Run manually on any day — the Saturday guard only applies to Task Scheduler runs

### Runner skips a post
- Check `run-logs\posting-run-*.log` for SKIP reason
- Most common: draft status is AUDITOR APPROVED not APPROVED — change it manually
- Check `schedule.md` confirms today is a posting day for that draft

### LinkedIn token expired
- Runner will log an authentication error
- Follow Section 12 token refresh steps
- Update `LINKEDIN_ACCESS_TOKEN` in Windows System Environment Variables

### Drive sync fails
- Check that `drive-file-ids.json` exists in the project folder
- Check that `.gdrive-write-token.json` exists at `C:\Users\pc\gdrive-personal-mcp\credentials\`
- If token expired: re-run OAuth flow — `python linkedin_drive_sync.py` (standalone)

---

## 16. Roadmap

### Live (as of March 2026)
- ✅ Post generation (Saturday auto)
- ✅ Draft audit + auto-regeneration (Sunday auto)
- ✅ Image generation via mmdc (manual)
- ✅ Image audit with IMAGE PASSED tracking (Sunday auto, after images generated)
- ✅ Daily posting Mon–Fri 9 AM WAT (auto)
- ✅ Google Drive sync (auto, after each run)

### Planned
- [ ] **Audit batching** — split large drafts into groups of 5–6 per Claude CLI call. Fixes slow audit runs.
- [ ] **Status dashboard** — read-only script showing full pipeline state + recommendations at a glance
- [ ] **Project 2 image generation** — run image planner for posts 16–33 after approving drafts
- [ ] **Approval notification** — Windows toast or email when auditor marks drafts AUDITOR APPROVED
- [ ] **LinkedIn engagement pull** — pull likes/comments/views per post, log to performance file, feed back into generator priorities
- [ ] **Cloud migration** — remove dependency on local laptop being on; host on a cloud VM or serverless scheduler

---

*LinkedIn Content Automation System | Theresa Erhumwunse | Version 2.0 — March 2026*
*Source of truth for this document: `LinkedIn_Automation_System_Reference.md` in the project folder*
*The `.docx` version is a formatted copy — update the `.md` file first, then reformat to .docx when needed*
