# LINKEDIN SCHEDULE SYNC — ONE-TIME FIX
# Theresa Erhumwunse | One-time schedule.md status correction
# Run once via linkedin_schedule_sync.py — do not schedule

---

## CONTEXT

drafts.md currently shows 11 drafts with status APPROVED (Posts 5-15).
schedule.md shows those same posts with status PENDING REVIEW (should be POST PENDING).
These must be brought into sync before the next posting run on 2026-03-16.

Rule: schedule.md status must always mirror drafts.md status exactly.
- PENDING REVIEW in drafts.md = POST PENDING in schedule.md
- APPROVED in drafts.md = POST PENDING in schedule.md (same — approval tracked in drafts.md)
- POSTED in drafts.md = POSTED in schedule.md

---

## FILE PATHS

- DRAFTS:   `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
- SCHEDULE: `C:\Users\pc\Documents\LinkedIn Project\schedule.md`

---

## INSTRUCTIONS

Use the `local-files` MCP for all file operations.
Do NOT post anything. Do NOT change any draft content.
Your only job is to sync schedule.md status fields to match drafts.md.

---

## STEP 1 — READ BOTH FILES

Read `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
For every draft, note: Draft number, Post number (from scheduled date mapping), Status.

Read `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
For every row in the Active Schedule table, note: Post number, Draft number, current Status.

---

## STEP 2 — BUILD SYNC MAP

Compare the two files and build a sync map:

| Post # | Draft # | drafts.md Status | schedule.md Status | Action needed |
|--------|---------|-----------------|-------------------|---------------|
| ...    | ...     | ...             | ...               | UPDATE / OK   |

Only rows where schedule.md status does NOT match drafts.md status need updating.

---

## STEP 3 — UPDATE schedule.md

For every row where drafts.md shows PENDING REVIEW or APPROVED, set schedule.md
status to POST PENDING. For rows where drafts.md shows POSTED, set schedule.md
status to POSTED. These are the only two valid states in schedule.md.

Do not change Posted Date or LinkedIn Post ID fields.
Do not change any row that is already in sync.
Do not change any POSTED rows.

---

## STEP 4 — VERIFY

Re-read schedule.md. Confirm every row status matches drafts.md exactly.

---

## SYNC REPORT

========================================
SCHEDULE SYNC REPORT
========================================
Run Date: [DATE AND TIME WAT]

Sync map:
[Print the full sync map from Step 2]

Rows updated: [N]
Rows already in sync: [N]

Verification:
- All schedule.md statuses match drafts.md: [Y/N]
- No POSTED rows changed: [Y/N]
- No draft content changed: [Y/N]

NEXT ACTION FOR THERESA:
- Open schedule.md and confirm Posts 5-15 now show POST PENDING
- The daily runner will post Draft #5 on 2026-03-16 as scheduled
========================================
