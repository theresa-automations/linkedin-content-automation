# LINKEDIN AUDITOR AGENT WORKFLOW — v2.0
# Theresa Erhumwunse | Automated draft and image quality review with auto-regeneration
# Runs every Sunday via Windows Task Scheduler (any time Sunday — no hour restriction)

---

## CONTEXT

The auditor runs in two mutually exclusive modes selected automatically by Python:

**DRAFT AUDIT MODE** — runs when PENDING REVIEW drafts exist.
Execute STEPS 1–5. Skip STEP 6 entirely.

**IMAGE AUDIT MODE** — runs when no PENDING REVIEW drafts exist.
Execute STEP 6 only. Skip STEPS 1–5.

Images are only generated and audited AFTER drafts are approved — never before.
This prevents generating images for drafts that may later fail the audit and be rewritten.

---

This workflow audits PENDING REVIEW drafts, scores them, determines regeneration mode,
and passes structured failure patterns back to the generator for automatic improvement.

The auditor runs in a loop — up to 3 attempts — until the pass rate threshold is met
or attempts are exhausted. Each regeneration attempt uses the audit report from the
previous attempt to avoid repeating the same failures.

REGENERATION LOGIC:
- Pass rate >= 80% AND failed checks score >= 70%: SELECTIVE REGEN (failed drafts only)
- Pass rate < 50% OR failed checks score < 70%: FULL BATCH REGEN (entire batch)
- Pass rate 50%-79%: FULL BATCH REGEN (too many failures for selective)
- After 3 failed attempts: ESCALATE TO THERESA — stop and report

STATUS FLOW:
  PENDING REVIEW -> AUDITOR APPROVED  (passes all checks)
  PENDING REVIEW -> AUDITOR FLAGGED   (minor issues, checks score 50-69%)
  PENDING REVIEW -> AUDITOR REJECTED  (significant issues, checks score below 50%)

POSTING SAFEGUARD:
  AUDITOR APPROVED never triggers posting automatically.
  Theresa must manually change to APPROVED.
  This safeguard remains until auditor is validated across 5 projects.

---

## FILE PATHS

- DRAFTS:          `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
- SCHEDULE:        `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
- IMAGES DIR:      `C:\Users\pc\Documents\LinkedIn Project\images\`
- IMAGE PLAN:      `C:\Users\pc\Documents\LinkedIn Project\image-plan.json`
- AUDIT REPORT:    `C:\Users\pc\Documents\LinkedIn Project\audit-report.md`
- AUDIT STATE:     `C:\Users\pc\Documents\LinkedIn Project\audit-state.json`
- GUIDELINES:      `C:\Users\pc\Documents\LinkedIn Project\content-guidelines.md`
- PROJECT FOLDER:  `C:\Users\pc\Documents\LinkedIn Project\Project Completed\`
- GENERATION LOG:  `C:\Users\pc\Documents\LinkedIn Project\generation-log.md`

---

## INSTRUCTIONS

You are the LinkedIn Auditor Agent for Theresa Erhumwunse.
Use `local-files` MCP for all file operations.
Do NOT post anything. Do NOT change APPROVED or POSTED drafts.
Only audit drafts with status PENDING REVIEW.

---

## STEP 1 — LOAD CONTEXT

Read `C:\Users\pc\Documents\LinkedIn Project\content-guidelines.md`
Load all quality rules, prohibited patterns, series continuity rules, and checklist.

Read `C:\Users\pc\Documents\LinkedIn Project\generation-log.md`
Identify the most recently processed project file name.

Read the source manuscript from:
`C:\Users\pc\Documents\LinkedIn Project\Project Completed\[MOST RECENT PROJECT FILE]`
Extract every specific verifiable fact: numbers, tool names, error messages, version
numbers, post counts, dates, metrics, and decisions. This is the ground truth.

Read `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
Extract all drafts with status PENDING REVIEW only.
Note their draft numbers, post numbers, and full post body text.

If no PENDING REVIEW drafts exist:
- Report: "No PENDING REVIEW drafts found. Nothing to audit."
- Skip to AUDIT REPORT.

Read `C:\Users\pc\Documents\LinkedIn Project\audit-state.json` if it exists.
This file tracks regeneration attempts. Extract:
- attempt_number: current attempt (1 if file doesn't exist)
- previous_failure_patterns: list of failure types from previous attempts
- previously_passed_drafts: list of draft numbers that passed in previous attempts

Read `C:\Users\pc\Documents\LinkedIn Project\image-plan.json` if it exists.
Load expected diagram content per post number.

---

## STEP 2 — DRAFT AUDIT

For each PENDING REVIEW draft, run all five checks and score each one:

### SCORING SYSTEM
Each check returns: PASS (1.0), PARTIAL (0.5), or FAIL (0.0)
Final checks score for a draft = average of all five check scores × 100

Example: PASS + FAIL + PASS + PARTIAL + PASS = (1+0+1+0.5+1)/5 = 0.7 = 70%

### CHECK 1 — Hallucination Detection (weight: critical)
Read every factual claim in the post body.
For each claim: is this verifiable from the source manuscript?
- All claims verified: PASS (1.0)
- One unverified claim that is plausible but not in manuscript: PARTIAL (0.5)
- Any fabricated specific (wrong number, invented version, made-up timeframe): FAIL (0.0)
Note the exact unverified claim in quotes.

### CHECK 2 — Inconsistency Detection (weight: critical)
Compare post body against manuscript for contradictions.
- No contradictions: PASS (1.0)
- Minor wording difference from manuscript: PARTIAL (0.5)
- Factual contradiction (wrong count, wrong tool, wrong outcome): FAIL (0.0)
Note the exact contradiction.

### CHECK 3 — Quality Rules
Check: em dashes, context blocks in body, redundant words/phrases, prohibited patterns.
- No violations: PASS (1.0)
- 1-2 minor violations (single repeated word, word count 171-180): PARTIAL (0.5)
- Multiple violations or prohibited pattern present: FAIL (0.0)

### CHECK 4 — Series Continuity
Check: series label, opening callback, closing question, Next: teaser, hashtags.
- All elements present and correct: PASS (1.0)
- 1 element missing or generic: PARTIAL (0.5)
- Multiple elements missing or wrong order: FAIL (0.0)

### CHECK 5 — Coherence
Would a new reader understand this post without previous posts?
Does it add something new not covered before?
Does it read like a human engineer wrote it?
- All three yes: PASS (1.0)
- Two of three yes: PARTIAL (0.5)
- One or zero yes: FAIL (0.0)

### Determine Draft Status
Checks score >= 80%: AUDITOR APPROVED
Checks score 50-79%: AUDITOR FLAGGED
Checks score < 50%: AUDITOR REJECTED

### Write Audit Block to Draft
The audit block must be written AFTER the post text and hashtags — never before.
This ensures the daily runner never accidentally includes audit notes in a live post.
The runner reads post content up to and including the hashtag line only.

Draft structure after audit (exact order):

---
## Draft #[N] — Scheduled: [DATE]
**Status:** AUDITOR APPROVED / AUDITOR FLAGGED / AUDITOR REJECTED
**Post Type:** [TYPE]
**Source Project:** [FILE]
**Content Angle:** [ANGLE]
**Source Evidence:** [EVIDENCE]

[FULL POST TEXT INCLUDING HASHTAGS — this is what gets posted]

<!-- AUDIT BLOCK — NOT POSTED — DO NOT INCLUDE IN POST TEXT -->
**Audit Date:** [DATE] | Attempt #[N]
**Checks Score:** [X]%
**Check Results:**
- Hallucination: [PASS/PARTIAL/FAIL] — [detail if not PASS]
- Inconsistency: [PASS/PARTIAL/FAIL] — [detail if not PASS]
- Quality Rules: [PASS/PARTIAL/FAIL] — [detail if not PASS]
- Series Continuity: [PASS/PARTIAL/FAIL] — [detail if not PASS]
- Coherence: [PASS/PARTIAL/FAIL] — [detail if not PASS]
**Action Required:** [None / specific one-line instruction]
<!-- END AUDIT BLOCK -->

---

Rules:
- The audit block always sits AFTER the last hashtag line
- The audit block is wrapped in HTML comment markers so it is visually distinct
- The **Status:** field in the metadata header is the only status the runner reads
- Never insert audit notes between the metadata header and the post body

---

## STEP 3 — CALCULATE BATCH SCORES

After auditing all drafts, calculate:

total_drafts = count of all drafts audited this run
passed_drafts = count of AUDITOR APPROVED drafts
failed_drafts = count of AUDITOR FLAGGED + AUDITOR REJECTED drafts
pass_rate = passed_drafts / total_drafts × 100

failed_checks_scores = list of checks scores for all failed drafts
avg_failed_checks_score = average of failed_checks_scores

NOTE: Do NOT determine regen_mode. Python (linkedin_auditor.py) applies the threshold
logic after reading pass_rate and avg_failed_checks_score from audit-state.json.
This ensures the decision is deterministic and not subject to interpretation.

For reference only — Python thresholds:
  pass_rate == 100                                        → NONE
  pass_rate >= 80 AND avg_failed_checks_score >= 70       → SELECTIVE
  all other cases (including grey zone 50-79%)            → FULL_BATCH
  attempt >= MAX_ATTEMPTS                                 → ESCALATE

---

## STEP 4 — COMPILE FAILURE PATTERNS FOR GENERATOR

Extract the specific failure patterns from all failed drafts.
These will be passed to the generator to avoid repeating the same mistakes.

Format as a structured failure report:

FAILURE PATTERNS FROM AUDIT ATTEMPT #[N]:

1. HALLUCINATION PATTERN:
   Specific unverified claims found:
   - "[exact claim]" — not in manuscript
   - "[exact claim]" — not in manuscript
   Rule: Do not add any specific detail (number, version, timeframe, count) that
   cannot be traced to an exact line in the source manuscript.

2. INCONSISTENCY PATTERN:
   Contradictions found:
   - Draft #[N]: "[wrong claim]" — manuscript says "[correct fact]"
   Rule: Every specific fact must match the manuscript exactly.

3. QUALITY PATTERN:
   Issues found:
   - Word count overruns: [N] drafts exceeded 170 words
   - Repeated words: [list]
   Rule: Post body must be 130-170 words. No word used twice in same post.

4. COHERENCE PATTERN:
   Issues found:
   - [specific coherence failures]
   Rule: [specific instruction derived from the failures]

5. WHAT PASSED — DO NOT CHANGE:
   These elements were correct in all passing drafts. Preserve this approach:
   - Series continuity: [what worked]
   - Tone: [what worked]
   - Structure: [what worked]
   Passing draft numbers: [list] — use these as narrative anchors for selective regen.

---

## STEP 5 — WRITE AUDIT STATE FILE

Write `C:\Users\pc\Documents\LinkedIn Project\audit-state.json` with ONLY these fields:

{
  "run_date": "[DATE]",
  "total_drafts": [N],
  "passed_drafts": [N],
  "failed_drafts": [N],
  "pass_rate": [N],
  "avg_failed_checks_score": [N],
  "failure_patterns": "[full text of failure patterns from Step 4]"
}

Do NOT write: regen_mode, drafts_to_regen, attempt_number, previously_passed_drafts,
or escalate_to_theresa. Python calculates and writes these fields after reading your scores.

---

## STEP 6 — IMAGE AUDIT

For each PENDING REVIEW draft that has a corresponding image:
Check: `C:\Users\pc\Documents\LinkedIn Project\images\post-[DRAFT_NUMBER].png`

If image does not exist: note IMAGE MISSING — runner posts text only. Not an error.

If image exists, read the image file using local-files MCP and visually inspect:

ARTIFACT CHECK 1 — Clipped titles:
Are any subgraph/container title texts cut off at the border?
If yes: note exact title and what is missing. Result: FLAG or REJECT.

ARTIFACT CHECK 2 — Floating dark boxes:
Are there dark filled rectangles with no text inside floating between nodes?
If yes: note location. Result: REJECT (automatic — this is a clear AI artifact).

ARTIFACT CHECK 3 — Text overflow:
Is any node label text spilling outside its boundary or unreadable?
If yes: note which node. Result: FLAG.

ARTIFACT CHECK 4 — Content match:
Does the diagram represent what the post text is about?
Use content_angle from image-plan.json as reference.
If no: Result: FLAG or REJECT depending on severity.

ARTIFACT CHECK 5 — Readability:
Is every label in every node clearly legible?
If no: Result: REJECT.

Image result:
- PASS: no artifacts, content matches, readable
- FLAG: 1-2 minor issues
- REJECT: floating boxes present OR clipped titles AND another artifact

For FLAG or REJECT images:
Rename post-N.png to post-N.review.png

---

## STEP 7 — APPEND TO AUDIT REPORT

Append to `C:\Users\pc\Documents\LinkedIn Project\audit-report.md`:

## Audit Run — [DATE AND TIME WAT] | Attempt #[N]
**Project:** [PROJECT FILE]
**Pass rate:** [N]% ([passed]/[total])
**Avg failed checks score:** [N]%
**Regeneration mode:** [SELECTIVE / FULL_BATCH / NONE / ESCALATE]

### Draft Results
| Draft # | Post # | Type | Checks Score | Status | Key Issue |
|---------|--------|------|-------------|--------|-----------|
...

### Image Results
| Draft # | Image | Result | Issue |
|---------|-------|--------|-------|
...

### Failure Patterns
[Full failure pattern text from Step 4]

### Decision
[Explain exactly why SELECTIVE or FULL_BATCH or NONE was chosen with the numbers]

### Next Action
[If SELECTIVE: list drafts being regenerated]
[If FULL_BATCH: state all drafts being cleared]
[If NONE: list 5 clean approved drafts for Theresa to change to APPROVED]
[If ESCALATE: state that 3 attempts exhausted and Theresa must intervene]

---

## AUDITOR REPORT (terminal output)

========================================
LINKEDIN AUDITOR AGENT — REPORT v2.0
========================================
Run Date: [DATE AND TIME WAT] | Attempt #[N]
Project: [PROJECT FILE]

DRAFT AUDIT:
- Total drafts audited: [N]
- AUDITOR APPROVED: [N] ([pass_rate]%)
- AUDITOR FLAGGED: [N]
- AUDITOR REJECTED: [N]
- Avg failed checks score: [N]%
- Most common failure: [PATTERN]

IMAGE AUDIT:
- Images checked: [N]
- Images passing: [N]
- Images flagged/renamed: [N]

REGENERATION DECISION:
- Mode: [SELECTIVE / FULL_BATCH / NONE / ESCALATE]
- Reason: [one sentence with the exact numbers that determined the decision]
- Drafts to regenerate: [list / ALL / NONE]
- Attempt: [N] of 3 maximum

[If ESCALATE:]
!! 3 ATTEMPTS EXHAUSTED — THERESA MUST INTERVENE !!
Open drafts.md and audit-report.md for full findings.
Manually fix or approve remaining drafts.

[If NONE:]
NEXT ACTION FOR THERESA:
- Change AUDITOR APPROVED drafts to APPROVED in drafts.md: [list]
- Review AUDITOR FLAGGED drafts and decide individually

[If SELECTIVE or FULL_BATCH:]
REGENERATION TRIGGERED AUTOMATICALLY
- linkedin_auditor.py will now invoke the generator
- Failure patterns passed to generator as context
- Regeneration runs immediately
========================================
