# LINKEDIN DRAFT REALIGNMENT WORKFLOW — v1.0
# Theresa Erhumwunse | One-time continuity fix for existing approved drafts
# Run once manually via linkedin_realign.py — do not schedule

---

## CONTEXT

Three posts from the current batch have already been published to LinkedIn.
The remaining 11 drafts are APPROVED but were generated before the series
continuity rules were introduced. They need the following added to each draft:
- Series label (Line 1)
- Opening callback referencing the previous post (Line 2, except where Post 1)
- Closing teaser hinting at the next post (second-to-last element, except last post)

The body content of every draft must remain completely unchanged word for word.
Only the three continuity elements are added. Nothing else is touched.

---

## FILE PATHS

- DRAFTS:    `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
- SCHEDULE:  `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
- AUDIT LOG: `C:\Users\pc\Documents\LinkedIn Project\audit-log.md`

---

## INSTRUCTIONS

You are performing a one-time continuity realignment on existing approved LinkedIn drafts.
Use the `local-files` MCP for all file operations.
Do NOT post anything. Do NOT change any post body content. Do NOT change any status fields.
Your only job is to add series label, opening callback, and closing teaser to each draft.

---

## STEP 1 — READ ALL FILES

Read `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
Extract every draft in order. For each draft note:
- Draft number
- Status (only process APPROVED drafts)
- Post type
- Content angle
- Full post body text exactly as written

Read `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
Extract the full posting schedule. Note:
- Total posts in the series
- Which post numbers have already been posted (status = POSTED)
- The sequential order of all posts

Read `C:\Users\pc\Documents\LinkedIn Project\audit-log.md`
Find the 3 already-published posts. For each note:
- Post number
- Post type
- The specific topic covered (summarise in 5 words or less)

---

## STEP 2 — BUILD THE FULL SERIES MAP

Using the schedule and audit log, build a complete map of the series:

| Post # | Draft # | Status  | Topic (5 words max)         |
|--------|---------|---------|----------------------------|
| 1      | —       | POSTED  | [topic from audit log]      |
| 2      | —       | POSTED  | [topic from audit log]      |
| 3      | —       | POSTED  | [topic from audit log]      |
| 4      | 1       | APPROVED| [topic from draft angle]    |
| 5      | 2       | APPROVED| [topic from draft angle]    |
...and so on for all 14 posts.

This map is the source of truth for every callback and teaser written in Step 3.
Every opening callback must reference the PREVIOUS post's topic from this map.
Every closing teaser must hint at the NEXT post's topic from this map.

---

## STEP 3 — REALIGN EACH APPROVED DRAFT

Process every APPROVED draft in order from lowest to highest draft number.

For each draft:

**3a — Determine series position**
From the series map: what is this post's number in the full series?
What was the previous post's topic? What is the next post's topic?

**3b — Write the series label**
Format: [Project Name] | Part [N] of [TOTAL]
Example: Catalyst CS Automation | Part 4 of 15

Extract the project name from the draft's Source Project field.
Use the correct post number and total from the series map.

**3c — Write the opening callback**
One sentence. Under 20 words. Moderate and conversational.
Reference the previous post's SPECIFIC topic — not a generic summary.
Do not start with "I". Do not use em dashes or en dashes.

Good examples:
- "Last post covered why manual CS across two storefronts couldn't scale. Today: the stack."
- "I walked through the full architecture last time. Now for what broke first."
- "The shared config decision came up last post. Here is why it mattered more than expected."

**3d — Write the closing teaser**
One sentence. Under 15 words. Specific enough to create genuine curiosity.
Do not use em dashes or en dashes. Do not say "Stay tuned" or "coming soon".

Good examples:
- "Next: the bug that made every email look like a rerun."
- "Next post: what 4,823 emails do to a system with no date filter."
- "Next: one line of Python that stopped the UTF-8 crashes entirely."

**3e — Assemble the realigned draft**
Build the new post text in this EXACT order with blank lines between every element:

  LINE 1:   Series label
            (blank line)
  LINE 2:   Opening callback
            (blank line)
  BODY:     Original post body — copied exactly, word for word, no changes whatsoever
            (blank line)
  CLOSING:  Original closing question or takeaway — copied exactly
            (blank line)
  TEASER:   "Next: [specific hint]" — always AFTER closing question, BEFORE hashtags
            (blank line)
  HASHTAGS: Original hashtags — copied exactly

CRITICAL RULES for realignment:
- If the original draft contains a context block (CONTEXT: / What it is: / Why it matters:)
  anywhere in the post body, REMOVE IT ENTIRELY. It is an internal note that was accidentally
  included and must never appear in published post text.
- "Next:" always sits AFTER the closing question and BEFORE the hashtags.
  Never inside the body paragraphs. Never before the closing question.
- Do not add blank lines inside the body content itself.
- The closing question or takeaway always comes BEFORE "Next:". Next: always comes before hashtags.

**3f — Overwrite the draft in drafts.md**
Replace the full post text of this draft with the realigned version.
The draft header block (Draft number, Status, Post Type, Source Project,
Content Angle, Source Evidence) must remain completely unchanged.
Only the post text below the header block is updated.

Do not change Status from APPROVED. Do not change any metadata fields.

---

## STEP 4 — VERIFY ALL 11 DRAFTS

After processing all drafts, re-read drafts.md and confirm:
- Every APPROVED draft now has a series label on line 1
- Every APPROVED draft (except the first in the remaining batch) has an opening callback
- Every APPROVED draft (except the last in the full series) has a closing teaser
- No draft body content was altered
- All status fields remain APPROVED
- All metadata fields are unchanged

---

## STEP 5 — REALIGNMENT REPORT

========================================
LINKEDIN REALIGNMENT REPORT — v1.0
========================================
Run Date: [DATE AND TIME WAT]

Series map built:
[Print the full series map from Step 2]

Drafts realigned: [N]
[List each: Draft # | Post # | Callback written | Teaser written]

Verification:
- All APPROVED drafts have series label: [Y/N]
- All callbacks reference specific previous post topic: [Y/N]
- All teasers are specific and under 15 words: [Y/N]
- No body content altered: [Y/N]
- All status fields unchanged: [Y/N]

NEXT ACTION FOR THERESA:
- Open drafts.md and review the realigned continuity elements on each draft
- Confirm each opening callback correctly references the previous post
- Confirm each closing teaser creates genuine curiosity for the next post
- If any callback or teaser needs adjustment, edit directly in drafts.md
- The daily runner will post each APPROVED draft on its scheduled date as normal
========================================
