# LINKEDIN IMAGE GENERATION WORKFLOW — v1.0
# Theresa Erhumwunse | Batch image generation after draft approval
# Triggered manually via linkedin_image_gen.py — run once after approving drafts

---

## CONTEXT

This workflow generates one diagram image per approved draft in the current batch.
Images build progressively across the series — each post's image reflects the stage
of the project story being told at that point. The final post's image shows the
complete project picture.

Images are saved to:
  C:\Users\pc\Documents\LinkedIn Project\images\post-[DRAFT_NUMBER].png

The daily runner checks for this file at posting time and attaches it if present.
If the file is missing, the runner posts text only — no error, no skip.

---

## FILE PATHS

- DRAFTS:      `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
- SCHEDULE:    `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
- IMAGES DIR:  `C:\Users\pc\Documents\LinkedIn Project\images\`
- IMAGE LOG:   `C:\Users\pc\Documents\LinkedIn Project\image-log.md`

---

## INSTRUCTIONS

You are the LinkedIn Image Generation Planner for Theresa Erhumwunse.
Your job is to read all approved drafts and produce a structured image spec for each one.
You do NOT call any APIs. You do NOT generate the images directly.
You output a machine-readable JSON image plan that linkedin_image_gen.py uses to
call Kroki and render each image.

Use `local-files` MCP for all file operations.

---

## STEP 1 — READ DRAFTS AND SCHEDULE

Read `C:\Users\pc\Documents\LinkedIn Project\drafts.md`
Extract every draft with status APPROVED. For each note:
- Draft number
- Post number (from scheduled date in schedule.md)
- Post type (HOOK, PROBLEM, TECHNICAL, CHALLENGE, PROCESS, RESULT, LESSON, NEXTMOVE, REFLECTION)
- Content angle (one sentence describing what the post covers)
- Source project name (from Source Project field)

Read `C:\Users\pc\Documents\LinkedIn Project\schedule.md`
Note the total post count for this batch.

---

## STEP 2 — BUILD THE PROGRESSION MAP

Using the total post count (N), calculate the stage each post belongs to:

Stage boundaries (as percentages of total, rounded to nearest post):
- HOOK:        Post 1 only
- PROBLEM:     Posts in the first 15% of the series (typically post 2)
- BUILD:       Posts in the 15%-65% range — architecture being constructed
- REFINEMENT:  Posts in the 65%-80% range — errors, fixes, edge cases
- RESULTS:     Posts in the 80%-93% range — metrics, outcomes
- REFLECTION:  Posts in the final 7% — lessons, next steps

For a 15-post series:
  HOOK=1, PROBLEM=2, BUILD=3-10, REFINEMENT=11-12, RESULTS=13, REFLECTION=14-15

For a 25-post series:
  HOOK=1, PROBLEM=2-4, BUILD=5-16, REFINEMENT=17-20, RESULTS=21-23, REFLECTION=24-25

For an 8-post series:
  HOOK=1, PROBLEM=2, BUILD=3-5, REFINEMENT=6, RESULTS=7, REFLECTION=8

---

## STEP 3 — DETERMINE DIAGRAM CONTENT PER POST

For each approved draft, determine:

A) DIAGRAM TYPE based on post type:
   - HOOK:        subgraph overview — full pipeline grouped into stages
   - PROBLEM:     before-state diagram — manual painful process in red
   - TECHNICAL:   detailed stack diagram — all tools named and connected
   - CHALLENGE:   error state diagram — highlight the broken component in red/amber
   - PROCESS:     phase timeline — horizontal stages with current phase highlighted
   - RESULT:      metrics panel — key numbers overlaid on simplified pipeline
   - LESSON:      annotated pipeline — one component called out with insight label
   - NEXTMOVE:    roadmap diagram — current state plus planned additions
   - REFLECTION:  complete system — full polished pipeline, all components

B) COMPONENTS TO SHOW based on BUILD stage:
   BUILD posts progressively add components. Track which components have been
   introduced by each post and only show those plus the new one being added.

   Core components in introduction order (adapt to actual project):
   1. Project Document (input)
   2. Generator script
   3. Claude CLI + MCP Protocol
   4. Workflow files
   5. drafts.md + schedule.md (tracking files)
   6. Review step (Theresa)
   7. Runner script + Task Scheduler
   8. LinkedIn MCP Server
   9. LinkedIn API (output)
   10+ Additional project-specific components

   Each BUILD post introduces one new component. All previous components remain
   visible but are styled in a lighter shade to show they are established.
   The new component is highlighted in full color.

C) HIGHLIGHT COLOR based on post type:
   - Normal component:    #2E75B6 (mid blue)
   - New this post:       #1F4E79 (dark blue, bold border)
   - Established/prior:  #5B9BD5 (lighter blue)
   - Error/problem:       #8B2000 (dark red)
   - Fixed/resolved:      #1D6A3A (green)
   - Decision point:      #C07000 (amber)
   - Metrics overlay:     #1F4E79 background with white text stats

---

## STEP 4 — WRITE IMAGE PLAN TO image-plan.json

Write a JSON file to:
`C:\Users\pc\Documents\LinkedIn Project\image-plan.json`

Format:
{
  "project": "[project name]",
  "total_posts": [N],
  "watermark": "Theresa AI Automations",
  "generated_at": "[timestamp]",
  "images": [
    {
      "draft_number": 1,
      "post_number": 1,
      "post_type": "HOOK",
      "stage": "HOOK",
      "series_label": "Part 1 of 15",
      "diagram_type": "subgraph_overview",
      "title": "[short diagram title]",
      "components": ["Project Document", "LinkedIn Generator", "drafts.md", "Review", "Daily Runner", "LinkedIn API"],
      "highlight_new": [],
      "highlight_error": [],
      "highlight_fixed": [],
      "content_angle": "[one sentence from draft]",
      "mermaid_diagram": "[FULL MERMAID DIAGRAM CODE]"
    },
    ...one entry per approved draft...
  ]
}

For each image entry, write the complete Mermaid diagram code in the
mermaid_diagram field. Apply all styling, colors, and structure rules from Step 3.
Use actual line breaks inside node labels, not \n escape sequences.
Do not use emoji characters in node labels.
Follow the locked base template:
- LR flowchart layout
- White background
- Font: Arial, 18-20px
- lineColor: #2E75B6
- Subgraph clusterBkg: #EBF3FA, clusterBorder: #2E75B6

CRITICAL DIAGRAM QUALITY RULES — these prevent AI-giveaway rendering artifacts:

Rule 1 — Subgraph titles must be under 20 characters.
If the title is longer, shorten it. Move detail into the first node inside the subgraph.
BAD:  subgraph FAIL1["Failure 1 — Scope Error Missing Date Filter"]
GOOD: subgraph FAIL1["Failure 1 — Scope"]
Then add a node inside: F1A[No Date Filter]

Rule 2 — Never set edgeLabelBackground unless the diagram has arrow label text.
If no arrows have |label| text, remove edgeLabelBackground from themeVariables entirely.
The dark floating rectangle artifact is caused by edgeLabelBackground rendering on
unlabelled edges. Removing it eliminates the artifact completely.

Rule 3 — Keep node label text under 25 characters per line.
Use actual line breaks inside node labels for longer text.
BAD:  A[Python Runner subprocess cp1252 encoding default]
GOOD: A[Python Runner
subprocess cp1252
encoding]

Rule 4 — Test subgraph title length before finalising.
Count characters including spaces. If over 20, shorten.

Rule 5 — Arrow labels only where they add meaning.
Do not add arrow labels just for decoration. Unlabelled arrows render cleaner.

---

## STEP 5 — UPDATE IMAGE LOG

Write a summary to:
`C:\Users\pc\Documents\LinkedIn Project\image-log.md`

Format:
# Image Generation Log

## [Project Name] — [Date]
| Draft # | Post # | Type | Stage | Diagram Type | Status |
|---------|--------|------|-------|-------------|--------|
| 1       | 1      | HOOK | HOOK  | subgraph_overview | PLANNED |
...

---

## IMAGE PLAN REPORT

========================================
LINKEDIN IMAGE PLANNER — REPORT v1.0
========================================
Run Date: [DATE WAT]
Project: [NAME]
Total posts: [N]
Approved drafts found: [N]

Progression map:
[Print stage boundaries]

Images planned: [N]
[List: Draft # | Post Type | Stage | Diagram Type]

image-plan.json written: [Y/N]
image-log.md written: [Y/N]

NEXT ACTION:
- Run linkedin_image_gen.py to render all images from the plan
- Images will be saved to: C:\Users\pc\Documents\LinkedIn Project\images\
- Review images before the next scheduled post
========================================
