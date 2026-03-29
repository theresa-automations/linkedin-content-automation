# LinkedIn Content Automation System
**Owner:** Theresa Erhumwunse
**Type:** Automation Engineering | AI Systems | Content Publishing
**Timeline:** March 2026
**Status:** Live in Production

---

## GENERATOR INSTRUCTIONS — READ BEFORE PROCESSING THIS DOCUMENT

This document covers the LinkedIn Content Automation System, a project that is both a technical
engineering achievement and a direct solution to a real professional problem. When generating
posts from this document, every post must reflect both dimensions:

1. WHAT WAS BUILT — the specific technical decisions, tools, errors, and fixes
2. WHY IT MATTERS — the professional need it solves and the tangible benefit it delivers

The need: engineers and automation specialists complete real, complex projects but rarely have
the time or consistency to translate that work into a visible professional presence. Content
creation falls off. Visibility suffers. Opportunities are missed, not because the work is
absent, but because no one knows it exists.

The benefit: this system removes that bottleneck entirely. A completed project document becomes
a scheduled series of high-quality posts without any ongoing manual effort. The professional
presence runs itself.

Every post generated from this document should carry that thread. A debugging story is not just
about fixing an error. It is about the kind of systematic thinking that makes someone hireable.
An architecture post is not just about tools. It is about the judgment behind choosing them.
A results post is not just metrics. It is proof that the work shipped and ran in production.

Do not state this meta-context explicitly in the posts. Weave it into the angle, the framing,
and the takeaway of each post so the benefit is felt rather than announced.

---

## Project Overview

This project involved designing and building a fully autonomous LinkedIn content publishing
system from the ground up. The system converts completed engineering project documents into a
scheduled series of LinkedIn posts, generates the full batch in a single continuous session to
preserve narrative consistency, and publishes each approved post automatically via the LinkedIn
API on a Monday-to-Friday schedule, without any manual trigger required after initial approval.

The system was built to mirror the same architectural principles applied in production automation
work: modular components with clearly separated responsibilities, explicit error handling at every
layer, structured audit trails, and a human review step preserved before anything goes live.
Every component was built, tested, debugged, and confirmed working in a live environment before
the project was considered complete.

**The professional need this solves:** Engineers and builders consistently underinvest in their
visibility because translating project work into content takes time they do not have. This system
removes that constraint. Once a project document exists, the content pipeline runs itself.

---

## Objectives

The primary objective was to eliminate all manual effort from the LinkedIn content workflow after
a project is completed. Before this system, converting a completed project into published content
required writing each post individually, managing a posting schedule manually, and remembering
to publish consistently. The goal was to make the entire process automatic from the point a
project document is saved, with the only human touchpoint being a review and approval step.

Secondary objectives:
- Ensure content quality is grounded in specific, verifiable project details, not generic AI output
- Maintain narrative consistency across a full post batch by generating everything in one session
- Enforce a human-in-the-loop approval step so nothing goes live without review
- Build a system scalable to multiple projects without rebuilding any infrastructure

---

## System Architecture and Components

The system consists of two fully separate automated pipelines with distinct schedules and
responsibilities.

### LinkedIn Content Generator
- Script: linkedin_generator.py
- Schedule: Every Saturday at 9 AM, 12 PM, and 6 PM WAT via Windows Task Scheduler
- Responsibility: Scans the Project Completed folder for unprocessed project documents.
  If a new file is found, invokes Claude CLI to generate the full post batch in one session.
  If nothing new is found, exits cleanly with no action.
- Timeout: None. Runs until complete.
- Day guard: Hard-coded Saturday-only check. Will not run on any other day regardless of
  Task Scheduler configuration.

### LinkedIn Daily Poster
- Script: linkedin_runner.py
- Schedule: Monday to Friday at 9 AM WAT via Windows Task Scheduler
- Responsibility: Checks schedule.md for today's assigned post. If the draft is APPROVED,
  posts to LinkedIn via the custom MCP server, updates all tracking files, and logs the result.
  If not approved or not a posting day, exits cleanly.
- Timeout: 5 minutes. Posting should complete well within 2 minutes.
- Day guard: Monday to Friday only. Saturday is explicitly excluded.

### Workflow Files
Markdown workflow files serve as the instruction set passed to Claude CLI at runtime:
- LINKEDIN-GENERATOR-WORKFLOW.md: drives batch generation including content audit, schedule
  calculation, post writing with series continuity and 4-pass self-review, and file updates
- LINKEDIN-IMAGE-GEN-WORKFLOW.md: drives image progression planning — reads approved drafts,
  builds the progression map, and writes image-plan.json with complete Mermaid diagram code
  per post. Dynamic: adapts to any post count, not hardcoded to 15.
- LINKEDIN-POSTING-WORKFLOW.md: drives daily posting including schedule check, draft status
  verification, image attachment check, LinkedIn API call, and file updates
- LINKEDIN-REALIGN-WORKFLOW.md: one-time workflow used to add series continuity to existing
  approved drafts without changing body content (used March 2026, not scheduled)
- LINKEDIN-SCHEDULE-SYNC-WORKFLOW.md: one-time workflow used to sync schedule.md status
  fields to the correct POST PENDING state (used March 2026, not scheduled)

### Content Quality System
Rules enforced via content-guidelines.md, read at the start of every generation run:
- Golden Rule: every claim must trace to a specific verifiable detail in the source document
- Honest content count: the model audits the document and states exactly how many posts it
  can support without hallucination. That number is the generation target. No more.
- Posting frequency calculated from post count: 25-30 posts = daily, 18-24 = 4x/week,
  12-17 = 3x/week, 7-11 = 2x/week, 1-6 = weekly
- Context blocks: for every technical concept introduced, an internal 50-word context block
  is written first to ensure accuracy. CRITICAL: context blocks are never included in the
  published post text. They are internal reference only.
- Prohibited patterns: em dashes, en dashes, "What do you think?", "Here's the thing.",
  consecutive sentences starting with "This means/allows/ensures"
- Anti-redundancy: no word, phrase, or idea repeated within a post or across the series.
  Every post opens with a different sentence structure.
- 4-pass self-review: specificity, redundancy, human voice, and format checks applied to
  every post before it is written to the draft queue

### Series Continuity System
Every post in a batch is part of a serialised build story. A reader landing on any post
mid-series must immediately understand where they are, what came before, and what comes next.
Three structural elements are applied to every post:

Post structure (exact order):
  [Series label]      — [Project Name] | Part [N] of [TOTAL]
  [Opening callback]  — one sentence referencing the previous post's specific topic (skip Post 1)
  [Post body]         — 130-170 words of prose
  [Closing question]  — specific question or bold takeaway
  [Next: teaser]      — one line hinting at the next post topic (skip last post)
  [Hashtags]          — 4-6 hashtags, always last

Rules:
- Opening callback: moderate and conversational, under 20 words, references previous post topic
- Next: teaser: specific enough to create genuine curiosity, under 15 words
- Next: always appears AFTER the closing question and BEFORE the hashtags
- Post 1: series label + teaser only, no callback
- Last post: series label + callback only, no teaser

### Tracking Files
- drafts.md: all generated post drafts — status flow: PENDING REVIEW → APPROVED → POSTED
- schedule.md: posting calendar — status flow: POST PENDING → POSTED (two states only)
  POST PENDING = draft is queued and waiting for its scheduled date
  POSTED = successfully published to LinkedIn by the runner
- generation-log.md: records every processed project file to prevent reprocessing
- audit-log.md: master record of every published post with full metadata
- image-plan.json: machine-readable image specification — one Mermaid diagram per post,
  written by the planner, read by the image generator
- image-log.md: records every image generation run — draft number, type, stage, status
- images/post-N.png: rendered diagram per draft — attached by runner at posting time.
  If missing, runner posts text only with no error.
- audit-state.json: tracks the auditor regeneration loop across Sunday runs —
  attempt number, failure patterns from previous audit, previously passed drafts,
  and escalation flag. Deleted automatically when pass rate threshold is met.
  Delete manually to reset the audit loop at any time.
- audit-report.md: records every auditor run — draft scores, image findings,
  regeneration decision, and failure patterns per attempt.
- run-logs/: timestamped log file per execution — prefixed by script type:
  generation-run-*.log, posting-run-*.log, image-plan-*.log, image-gen-*.log,
  auditor-run-attempt[N]-*.log, realign-run-*.log, schedule-sync-*.log

Note: drafts.md and schedule.md use intentionally different status labels.
drafts.md tracks content review state (Theresa's approval).
schedule.md tracks posting queue state (runner's posting progress).
The runner reads APPROVED from drafts.md to decide whether to post.
schedule.md is never used to gate a post.

---

## Technologies Used

- Claude AI (CLI): central orchestration engine, invoked non-interactively via --print and
  --dangerously-skip-permissions flags, reading workflow instructions from markdown files
  passed via stdin
- Model Context Protocol (MCP): open standard connecting Claude to external tools including
  the LinkedIn API, local filesystem, and Google Drive
- Custom LinkedIn MCP Server: built from scratch in Node.js, integrates with the LinkedIn
  UGC Posts API via OAuth 2.0, registered in the shared Claude Desktop and CLI config file
- local-files MCP: filesystem access for reading and writing all system files at runtime
- Google Drive MCP (Personal): reads content strategy and guidelines from personal Drive,
  currently read-only, write capability planned
- Python: seven automation scripts:
  linkedin_generator.py: Saturday checker and batch generation invoker
  linkedin_runner.py: daily poster, Mon-Fri, attaches images automatically
  linkedin_image_planner.py: reads approved drafts, writes image-plan.json via Claude CLI
  linkedin_image_gen.py: reads image-plan.json, calls Kroki API, renders PNG per post
  linkedin_image_post.py: direct LinkedIn image post helper — bypasses the MCP entirely,
    uses LinkedIn REST API (/rest/images + /rest/posts) to post text with image;
    called by LINKEDIN-POSTING-WORKFLOW.md via Bash when an image file is present;
    accepts --text-file for multiline post text (safe against shell quoting failures);
    replaces ' | ' with ' - ' before sending to avoid LinkedIn commentary truncation;
    reads credentials from linkedin_mcp_config.json; stdlib only, no dependencies
  linkedin_realign.py: one-time series continuity retrofitter (run March 2026)
  linkedin_schedule_sync.py: one-time schedule status corrector (run March 2026)
  linkedin_reset_project2.py: one-time project 2 data reset for clean regeneration
- Kroki API: free hosted diagram rendering service. Accepts Mermaid diagram source via
  HTTP POST, returns PNG. Supports flowcharts, sequence diagrams, timelines, and more.
  No API key required. User-Agent header required to pass Cloudflare validation.
- Pillow (Python): post-processes each PNG after Kroki renders it — adds white canvas
  with padding, series label bottom-left, and subtle watermark bottom-right.
  Watermark: "Theresa AI Automations" at opacity 35, no shadow, Arial 15px.
- Windows Task Scheduler: triggers both scripts on their respective schedules
- LinkedIn UGC Posts API: REST API for publishing posts, authenticated via OAuth 2.0
- OAuth 2.0: authorization code grant flow for LinkedIn API access, token lifespan ~60 days
- Node.js and npm: runtime and package manager for the custom MCP server
- Markdown workflow files: structured instruction sets passed to Claude CLI at runtime

---

## Challenges Faced and Resolutions

### Single Orchestrator Replaced by Two Separate Workflow Files
The original design used a single markdown workflow file — LINKEDIN-ORCHESTRATOR.md — that
contained both the content generation logic and the daily posting logic in one document.
Claude CLI read this file on every run and attempted to execute all sections sequentially.

This created two problems. First, the file grew large and complex as features were added,
making it harder to reason about and debug. Second, the daily posting run was loading and
processing the full generation logic even when no new project existed, adding unnecessary
overhead to a task that should complete in under two minutes.

Resolution: the orchestrator was retired and replaced by two purpose-built workflow files.
LINKEDIN-GENERATOR-WORKFLOW.md handles all batch generation logic exclusively.
LINKEDIN-POSTING-WORKFLOW.md handles all daily posting logic exclusively.
Each script invokes only its own workflow file. The two files have no overlap.
LINKEDIN-ORCHESTRATOR.md was archived in the Archive\ subfolder for historical reference.

Verification confirmed neither linkedin_generator.py nor linkedin_runner.py contained any
reference to the old orchestrator file before it was archived, confirming Task Scheduler
tasks were unaffected by the change.

Why this matters professionally: a system that grows by accumulating logic into a single
file becomes fragile and difficult to maintain. Separating concerns into purpose-built
components — even when the original single-file approach was working — is the discipline
that keeps a system maintainable as it scales.

### Architecture Split: Generator vs Runner
The original single-script design hit the Claude API usage limit mid-session during batch
generation because producing a full post batch in one heavy call exceeded the per-session limit.

Resolution: split into two completely separate Python scripts with separate Task Scheduler
tasks. The generator runs every Saturday with no timeout and handles only batch generation.
The runner runs Mon-Fri with a 5-minute timeout and handles only posting. Each script has
a hard day guard making cross-schedule interference impossible regardless of Task Scheduler
configuration. This split also eliminated the timeout issue entirely — the daily runner now
consistently completes in under two minutes.

Why this matters professionally: recognising when a single-responsibility violation is causing
a system failure, and redesigning the architecture rather than patching around it, is the
difference between a system that works once and one that runs in production indefinitely.

### Custom LinkedIn MCP Server
No off-the-shelf LinkedIn MCP server existed that met requirements. The standard available
packages either lacked the UGC Posts API integration or had authentication limitations.

Resolution: built a custom Node.js MCP server from scratch. Registered it in the shared
Claude Desktop and CLI configuration. Tested with a live post before any automation was
wired up. The server has been running live since March 2026.

### Unicode SyntaxError on Windows
Windows file paths containing backslashes inside Python docstrings caused a SyntaxError on
startup because Python interpreted the backslash sequences as Unicode escape characters.

Resolution: removed special characters from docstring headers and used raw string notation
for all path constants throughout the configuration block. A small fix with a clear root cause,
resolved without workarounds.

### AI-Sounding Content Quality
Initial draft output was recognisably AI-written: em dashes throughout, repeated phrasing
across posts, generic observations with no grounding in specific project details, and closing
lines that restated the opening rather than adding something new.

Resolution: built a multi-layer quality system into the content guidelines file. The system
now requires every claim to trace to a specific verifiable detail in the source document,
prohibits em dashes and en dashes entirely, enforces anti-redundancy rules both within
individual posts and across the full series, requires an internal context block before writing
any post that introduces a technical concept, and runs a four-pass self-review on every post
before it is written to the draft queue. Output quality improved significantly on the
following generation run.

Why this matters professionally: most AI-generated content is recognisable as such, which
actively damages professional credibility rather than building it. Solving this required
understanding the specific failure modes and designing systematic guardrails for each one.

### Honest Content Counting
Early generation runs inflated post counts by padding thin material across too many posts,
producing generic filler toward the end of a batch.

Resolution: added an explicit honest content audit step to the generator workflow. The model
lists every distinct angle the document genuinely supports with a specific source citation for
each, states how many posts can be written without hallucination, and that number becomes the
generation target. No more can be written.

### Series Continuity Retrofitting
The first batch of 14 posts was generated before series continuity rules were introduced.
Rather than regenerating the full batch (which would have discarded 3 already-posted posts
and 11 approved drafts), a one-time realignment script was built to add series labels,
opening callbacks, and closing teasers to the 11 remaining approved drafts without touching
any body content. The realigner also removed context blocks that had incorrectly appeared
inside 4 post bodies. All 11 drafts were updated in a single run.

### Schedule Status Inconsistency
After the realignment run, the system flagged that schedule.md showed PENDING REVIEW for
Posts 5-15 while drafts.md showed APPROVED. This revealed that the two files needed
intentionally different status labels rather than mirrored ones. The fix introduced a clear
two-file status model: drafts.md tracks content review state using PENDING REVIEW, APPROVED,
and POSTED. schedule.md tracks posting queue state using only POST PENDING and POSTED.
A one-time sync script corrected the current batch. The generator and posting workflows
were updated to maintain this separation automatically going forward.

### Auditor First Run — Hallucination Pattern Identified
The first auditor run on 18 project 2 drafts achieved a 27% pass rate (5 of 18).
The dominant failure pattern was the generator adding plausible-sounding specifics
not present in the source manuscript — Python version numbers, post counts,
timeframes, and pricing claims. Every hallucination was this same pattern.

Resolution: the auditor captures these failure patterns in audit-state.json and
passes them as explicit context to the generator on the next regeneration attempt.
The generator is instructed to avoid these exact patterns in the new batch.
Series continuity was clean across all 18 posts — only factual accuracy failed.

This finding validated the auditor's core value: catching subtle hallucinations
that are invisible to casual review but would damage professional credibility
if published. A reader who knows the project would immediately notice fabricated
specifics. The auditor catches them before they reach Theresa's review.

### LinkedIn Image Posting — Five Failures Before a Working System
Image posting required resolving five distinct failures across the MCP layer, the LinkedIn
API surface, text rendering, API incompatibility, and shell argument handling. Each failure
was invisible until the previous one was fixed.

**Failure 1 — 401 Unauthorized on binary image upload**
The MCP's `create_post_image` tool returned 401 on the binary upload step. Root cause found
in the MCP source: `binaryUpload()` was called with `includeAuth = true` for legacy
`/v2/assets` upload URLs, which explicitly require no Authorization header on the binary PUT.
Fix applied: changed `includeAuth` from `true` to `false` in index.js.

**Failure 2 — SSL handshake timeout, endpoint deprecated**
After the auth fix, the image registration call itself timed out at the SSL level before
a connection was established. `/v2/assets?action=registerUpload` is deprecated at the
network level. The MCP hung indefinitely, causing the entire Claude CLI session to time
out after 5 minutes. The MCP could not be used for image posting regardless of any auth fix.

External tools evaluated at this point: n8n (workflow automation with LinkedIn node) and
Postiz (open-source social media scheduler). n8n ruled out — adds a permanent running
service. Postiz ruled out — replaces too much existing workflow architecture. Neither fixed
the root cause.

**Resolution — built `linkedin_image_post.py` bypassing the MCP**
Standalone Python script using LinkedIn's current REST API, stdlib only:
- Step 1: POST /rest/images?action=initializeUpload — new API, requires LinkedIn-Version header
- Step 2: binary PUT with Authorization header (new API requires it; legacy required no auth)
- Step 3: POST /rest/posts with urn:li:image: URN
Confirmed working with short test text ("Test post"). Image uploaded and posted correctly.

**Failure 3 — Full post text not displaying (shell quoting)**
First real-text test passed 1,482-character Draft #5 text via PowerShell here-string to
`--text`. Post went live with image but no text at all. Cause: PowerShell passed the
multiline string as an empty argument due to shell quoting failure on special characters.
Switched to writing the text to `post_text_temp.txt` first via Notepad — same result.
File then written programmatically in Python to rule out encoding or line-ending issues.
A debug line added to the script confirmed the correct text was reaching the API:
  [DEBUG] Text length: 1482 chars | First 60: 'Catalyst CS Automation | Part 5 of 15\n\nLast post covered two'

**Failure 4 — Commentary truncated at ` | ` by LinkedIn's /rest/posts API**
Despite confirmed text being sent, LinkedIn displayed only "Catalyst CS Automation" on
every test — the text before the first ` | ` in the series label. No "see more" above or
below the image. Clicking the post permalink produced the same result.
`content.media.title` changed to `altText`, then removed entirely — neither had any effect.

Attempted to verify stored content via GET /rest/posts/{post_id}: failed HTTP 400 (post
URN contains colons requiring URL encoding). After adding URL encoding: HTTP 403
ACCESS_DENIED — the OAuth token has write-only permissions, no read access to posts.
Stored content could not be verified via API.

Attempted to fix by switching post creation to `/v2/ugcPosts` (the endpoint used by
text-only posts, which display correctly): failed with 400 INVALID_CONTENT_OWNERSHIP.
`/v2/ugcPosts` only accepts `urn:li:digitalmediaAsset:` URNs from the deprecated
`/v2/assets` flow. The new `/rest/images` API returns `urn:li:image:` URNs. The two APIs
use incompatible URN formats and cannot be mixed. Reverted to `/rest/posts`.

Isolation test: ran the script with text containing no pipe character —
"Pipe test line one\n\nLine two is here\nLine three\n\n#Test" — full text displayed.
Confirmed: ` | ` in the series label is treated as a structural separator by `/rest/posts`,
truncating everything after it. Not documented anywhere in LinkedIn's API documentation.

Resolution: one-line preprocessing step in linkedin_image_post.py — `post_text.replace(' | ', ' - ')`.
Series label posts as "Catalyst CS Automation - Part 5 of 15". Approved drafts unchanged.
Replacement happens only at the API boundary on every image post.

**Failure 5 — Shell quoting breaks multiline text in workflow Bash commands**
When Claude CLI constructs a Bash command with post text embedded in `--text`, apostrophes
and special characters in the draft body cause silent failure regardless of quoting method.

Resolution: `--text-file` flag added to linkedin_image_post.py as a mutually exclusive
alternative to `--text`. The posting workflow uses the `local-files` MCP to write post text
to `post_text_temp.txt` before the Bash step — no shell quoting involved, encoding
guaranteed. The Bash command passes only a file path, never raw post text.

**Final confirmation**
Post #5 (originally published text-only on 2026-03-16) was deleted and reposted on
2026-03-17 with full text and image (urn:li:share:7439615154343927808). Full post body
visible on LinkedIn. All three files updated: drafts.md, schedule.md, audit-log.md.
LINKEDIN-POSTING-WORKFLOW.md updated: image posts route to linkedin_image_post.py via
Bash; text-only posts continue using the LinkedIn MCP create_post tool unchanged.

Why this matters professionally: five failure modes in sequence, each invisible until the
previous was resolved. The system that runs in production is not the one that was designed
on day one — it is the one that survived contact with the actual API. Systematic isolation,
one variable changed per test, is the only method that works when live API calls are the
test environment and every failed run produces a post that must be manually deleted.

### Generation Log Self-Healing
During a test run where the generation log had been cleared manually, the system detected
that a project file was missing from the log despite evidence of prior processing across other
files: an existing schedule, existing drafts, and a published post ID in the audit log.

Rather than reprocessing and overwriting live content, the system repaired the generation log
entry, removed a corrupted HTML comment block wrapping all 14 drafts that had made them
unreadable, and correctly identified the run as ALREADY_POSTED. This self-healing behaviour
was not explicitly programmed. It emerged from the structured reasoning the workflow enforces.

Why this matters professionally: production systems encounter unexpected states. A system that
detects inconsistency, reasons about the evidence, and takes the conservative corrective action
rather than blindly reprocessing is a system that can be trusted to run unsupervised.

---

## Results and Outcomes

### Operational Results
- 15 posts generated from one project document in a single generation session
- Posting schedule: Mon/Wed/Fri through April 2026, fully automated
- Generation checks: every Saturday at 9 AM, 12 PM, and 6 PM WAT
- Daily posting: Mon-Fri at 9 AM WAT, confirmed under 2 minutes per run
- Manual steps required after approval: zero
- Full audit trail: timestamped log per run, audit-log.md updated after every post
- Image generation: one progressive diagram per post, building from simple overview
  to complete system picture across the series. Dynamic — adapts to any post count.
- Posts attach images automatically at posting time. Text-only fallback if no image.

### Professional Impact
The system means that every project completed from this point forward automatically becomes
a visible body of published work on LinkedIn. The professional presence compounds over time
without additional effort. Engineers who ship real systems get the credit those systems deserve.

### Engineering Demonstration
The project demonstrates end-to-end ownership of an AI automation system from OAuth app
registration and custom MCP server development through workflow design and prompt engineering,
Python automation scripting with real-world Windows debugging, content quality system design,
and production deployment via Task Scheduler. Every component was tested against live conditions
and confirmed working before the project was considered complete.

---

## Run Order — What to Run and When

### When a new project is completed
1. Drop a numbered .md file into the Project Completed folder (e.g. 3 project-name.md)
2. Wait for the next Saturday — linkedin_generator.py fires automatically at 9 AM, 12 PM,
   or 6 PM WAT and detects the new file
3. Review drafts.md — change PENDING REVIEW to APPROVED for each post you are happy with
4. Run the image planner manually:
   python "C:\Users\pc\Documents\LinkedIn Project\linkedin_image_planner.py"
5. Run the image generator manually after the planner completes:
   python "C:\Users\pc\Documents\LinkedIn Project\linkedin_image_gen.py"
6. Review the images folder — replace any image by saving your own as post-N.png
7. The daily runner handles everything from here — posts fire Mon-Fri at 9 AM WAT

### Ongoing automated (no action needed)
- linkedin_generator.py: every Saturday 9 AM, 12 PM, 6 PM WAT — checks for new projects
- linkedin_runner.py: every weekday 9 AM WAT — posts next approved draft with image

### What to check occasionally
- run-logs/ folder — confirm posts are going live, spot any errors
- LinkedIn token expiry — regenerate around May 5, 2026 (see Section 6 of reference doc)

---

## How to Run the System — Execution Order

This section defines the exact order in which every script must be run and when.
Following this order is critical. Running scripts out of sequence will produce errors.

### For every new project — run in this order:

Step 1: ADD THE PROJECT FILE
Drop a new numbered .md file into:
  C:\Users\pc\Documents\LinkedIn Project\Project Completed\
Example: 2 next-project-name.md
No command needed. The Saturday generator detects it automatically.

Step 2: GENERATE DRAFTS (automatic — runs every Saturday at 9 AM, 12 PM, 6 PM WAT)
  linkedin_generator.py — triggered by Task Scheduler, no manual action needed.
  If you want to trigger it immediately:
  python "C:\Users\pc\Documents\LinkedIn Project\linkedin_generator.py"

Step 3: REVIEW AND APPROVE DRAFTS
  Open drafts.md. Change PENDING REVIEW to APPROVED for each post you are happy with.
  This is the only manual step in the entire pipeline.

Step 4: GENERATE IMAGE PLAN
  python "C:\Users\pc\Documents\LinkedIn Project\linkedin_image_planner.py"
  Claude reads all APPROVED drafts, builds the progression map, writes image-plan.json.
  Wait for this to complete before running Step 5.

Step 5: RENDER IMAGES
  python "C:\Users\pc\Documents\LinkedIn Project\linkedin_image_gen.py"
  Reads image-plan.json, calls Kroki API, renders PNG per post, saves to images/ folder.
  Check the images/ folder and replace any diagram by saving your own file as post-N.png.

Step 6: POSTING (automatic — runs Mon-Fri at 9 AM WAT via Task Scheduler)
  linkedin_runner.py — no manual action needed.
  Checks for APPROVED draft, attaches image if images/post-N.png exists, posts to LinkedIn.

---

## Current System Status (March 2026)

- 5 posts published: Posts 1-5
  Posts 1-4: text-only, published before image system was built
  Post 5: originally published text-only on 2026-03-16 (urn:li:share:7439213985284935680),
    deleted and reposted with image on 2026-03-17 after image system was confirmed working
    (urn:li:share:7439615154343927808)
- 10 approved drafts queued: Posts 6-15, scheduled Mon/Wed/Fri through April 9
- Images generated: post-5.png through post-15.png exist in images/ folder
- Image posting confirmed working end-to-end: upload, full text, image visible on LinkedIn
- Series label ' | ' replaced with ' - ' at API boundary for all image posts
- Multiline text handled via --text-file to post_text_temp.txt (no shell quoting issues)
- Task Scheduler: live for both daily poster (Mon-Fri 9 AM) and generator (Sat 9/12/6)
- Next scheduled post: 2026-03-18, Draft 6 — first fully automated image post via Task Scheduler

---

## Next Steps and Recommendations

---

### Why Image Generation Was Built Before the Auditor Agent

The Auditor Agent (quality review automation) was the originally planned Phase 5.
Image generation was built first for a deliberate reason: LinkedIn post engagement.

Posts with visuals consistently outperform text-only posts on LinkedIn, particularly
for technical content where a diagram makes abstract systems immediately scannable
to recruiters, founders, and technical leads. Building the image system first means
every post from this point forward ships with a professional diagram attached,
maximising reach and engagement from the current batch rather than waiting.

The Auditor Agent improves draft quality before posting. Image generation improves
engagement after posting. Engagement drives visibility. Visibility drives opportunity.
Getting the image system live first was the higher-leverage decision.

The Auditor Agent remains the next planned build — now as Phase 6.

---

### Phase 6: Auditor Agent — BUILT (March 2026)

The auditor agent is live and running every Sunday at 6 PM WAT. It audits all
PENDING REVIEW drafts against the source manuscript using a 5-check scoring system,
then automatically regenerates failed drafts using audit failure patterns as context.

**5-Check Scoring System (per draft):**
Each check returns PASS (1.0), PARTIAL (0.5), or FAIL (0.0).
Checks score = average of all five checks x 100.

1. Hallucination Detection — every factual claim traced to source manuscript
2. Inconsistency Detection — no contradictions between post and manuscript
3. Quality Rules — no em dashes, no context blocks, no redundancy, word count 130-170
4. Series Continuity — label, callback, closing question, Next: teaser, hashtags all correct
5. Coherence — new reader can follow, adds something new, reads like a human engineer

**Draft status after audit:**
- Checks score >= 80%: AUDITOR APPROVED
- Checks score 50-79%: AUDITOR FLAGGED
- Checks score < 50%: AUDITOR REJECTED

**Auto-Regeneration Loop:**
The auditor does not just flag issues — it triggers automatic regeneration when the
batch quality is below threshold, passing specific failure patterns to the generator
as context to avoid repeating the same mistakes.

Regeneration logic:
- Pass rate >= 80% AND failed checks score >= 70%: SELECTIVE REGEN (failed drafts only)
- Pass rate < 50% OR failed checks score < 70%: FULL BATCH REGEN (entire batch)
- Pass rate 50-79%: FULL BATCH REGEN (too many failures for selective)
- After 3 attempts: ESCALATE TO THERESA

Selective regen runs immediately on Sunday after audit — any day, not just Saturday.
Passed drafts are preserved as narrative anchors for continuity.
Failure patterns from each attempt are passed to the next regeneration as explicit
instructions, making each attempt materially better than the last.

**Audit block placement:**
Audit blocks are written AFTER the post text and hashtags, wrapped in HTML comment
markers. The daily runner reads post content up to the last hashtag line only —
audit notes are never included in live posts.

**Posting safeguard:**
AUDITOR APPROVED never triggers posting automatically. Theresa must manually change
to APPROVED in drafts.md. This safeguard remains until the auditor is validated
across 5 projects.

**State tracking:**
audit-state.json tracks attempt number, failure patterns, and previously passed
drafts across Sunday runs. Deleted automatically when threshold is met. Delete
manually to reset the audit loop at any time.

Build trigger: validated — first test run processed 18 drafts, caught 13 issues
including hallucinations (fabricated version numbers, post counts, timeframes),
word count overruns, and one factual inconsistency ("Fifteen drafts" vs actual
fourteen). Series continuity was clean across all 18 posts.

---

### Phase 7: Image Generation Refinements (Parallel with Phase 6)
- Add a confidence scoring step — flag diagrams where Mermaid rendering produces
  unexpected layouts, for manual replacement before posting
- Integrate Templated.io as an alternative renderer for branded card-style visuals
  on RESULT and REFLECTION posts where a metrics card is more appropriate than a diagram
- Build image review into the approval workflow so image status is tracked in drafts.md
  alongside post text status

---

### Phase 8: Full Cloud Migration (Recommended Next Major Phase)

This is the most significant architectural improvement available. The system currently
depends on a single local laptop being on, connected, and uninterrupted. If the laptop
sleeps, restarts, or loses connection, scheduled tasks miss their window silently.
A cloud deployment removes this dependency entirely.

Why cloud migration matters:
- The system runs whether or not any specific device is available
- Scheduled tasks never miss due to a sleeping laptop
- Recoverable after failures without manual intervention
- Accessible and manageable from anywhere
- The difference between a personal automation tool and production infrastructure

Recommended architecture:
- Hosting: Railway, Render, or a small DigitalOcean droplet (approximately 6 USD per month)
  Alternatively GitHub Actions with scheduled workflows (on: schedule with cron syntax)
- Scheduler: replace Windows Task Scheduler with cron jobs on the VPS
- File storage: migrate local .md files to a private GitHub repository — versioned,
  accessible from anywhere, and free
- MCP servers: Claude CLI and all MCP configs migrate to the VPS. The LinkedIn MCP
  server runs as a persistent Node.js process on the server
- Secrets management: environment variables on the VPS replace claude_desktop_config.json.
  LinkedIn token and OAuth credentials stored as encrypted env vars
- Drive sync: cloud hosting enables Google Drive MCP write capability via a non-interactive
  OAuth refresh token flow — automatic sync after every generation and posting run

Migration steps in order:
1. Set up VPS — confirm Python, Node.js, and Claude CLI install correctly
2. Copy all workflow files and scripts to the server
3. Migrate all secrets to environment variables
4. Test linkedin_runner.py on the server manually before enabling the cron job
5. Enable cron and run for one week in parallel with local Task Scheduler
6. Disable local Task Scheduler once cloud version is confirmed stable
7. Decommission local dependency entirely

---

### Short Term Infrastructure Improvements
- Resolve Google Drive MCP write capability to enable automatic sync after every run
- Implement proactive LinkedIn token refresh alert before the May 2026 expiry
- Add image status field to drafts.md so image review is tracked alongside post approval

---

## Skills Demonstrated

AI orchestration, MCP integration, Python automation scripting, API integration and debugging,
OAuth 2.0 implementation, custom MCP server development, workflow design and prompt engineering,
content quality system design, series continuity design, status lifecycle design,
programmatic diagram generation (Kroki API + Mermaid), image post-processing (Pillow),
progressive visual storytelling, Windows Task Scheduler configuration, system architecture,
production deployment, audit trail design, error handling and recovery design,
iterative system refinement, cloud migration planning
