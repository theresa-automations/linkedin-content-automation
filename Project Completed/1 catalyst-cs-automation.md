# Project: AI-Powered Customer Service Automation System
**Client:** Catalyst Products
**Period:** February – March 2026
**Status:** Live in production

## What Was Built
Fully automated AI customer service email processing system for a Shopify accessories brand
operating across two international storefronts.

## Core Problem Solved
All incoming customer emails required full manual review, classification, and response drafting.
High volume, wide variety, inconsistent quality. The system replaces drafting with reviewing.

## Technologies Used
Claude AI CLI · Model Context Protocol (MCP) · Gmail MCP · Shopify MCP (x2) ·
Google Drive MCP · Rube Automation · Python · Windows Task Scheduler · Node.js · npm

## Architecture
- Claude CLI as central orchestration engine
- Gmail MCP: reads, labels, threads, drafts responses
- Shopify MCP (x2): 22 tools across both storefronts — listOrders, getCustomer, order lookup
- Google Drive MCP: reads policy docs and FAQs at runtime
- Rube Automation: EMAIL TRIAGE v2 recipe — 16-tag classification with domain filtering
- Python + Task Scheduler: hourly execution 8am–6pm WAT, Monday–Friday
- Shared claude_desktop_config.json: enables both Desktop and CLI to use same MCPs

## Key Engineering Decisions
- Shared config between Claude Desktop and CLI — enabled full CLI automation
- Domain pre-filter enforced BEFORE LLM classification — blocks B2B spam without API cost
- PayPal exception rule — filtered as spam UNLESS chargeback keywords detected
- 7-day date cutoff — prevents processing 4,823-email historical backlog
- ID→name reverse map for Gmail labels — fixed v17/v18 rerun bug in v19
- UTF-8 encoding with errors='replace' — fixed Windows subprocess crash
- Human-in-the-loop preserved — all responses stay as Gmail drafts until approved

## Challenges & Resolutions
- npm package 404 (x2) → systematic registry search, found correct global package
- tar extraction failures → cleared npm cache, stable for 9+ days after
- Label ID mapping bug → built upfront reverse map from GMAIL_LIST_LABELS
- 4,823-email backlog → deployed 7-day date cutoff in Rube recipe v20
- UTF-8 crash in Python → explicit encoding params in subprocess call
- B2B misclassification → domain pre-filter now blocks LLM call entirely
- Windows Store app not scriptable → pivoted to Claude CLI (same MCP config)
- Docker MCP secret get fails → reverted to env-block, Credential Manager pending

## Results
- 16 operational classification labels deployed
- 4,823 historical emails classified in single automated pass
- 22 Shopify tools connected across 2 storefronts
- 20+ B2B/spam domains auto-filtered before LLM
- Triage recipe: v1 through v20
- 9+ days continuous stable production operation
- Hourly execution, 8am–6pm WAT, Mon–Fri
- 100% human oversight preserved on all outgoing responses

## Content Angles (for LinkedIn posts — check audit log before using)
- [x] Hook: The result headline — what the system does in one sentence
- [ ] Problem: Manual CS at scale doesn't work — the before picture
- [ ] Architecture: The full stack and why each tool was chosen
- [ ] Challenge: npm 404s and the systematic debugging process
- [ ] Challenge: The label ID mapping bug (v17→v19 fix)
- [ ] Challenge: UTF-8 encoding crash on Windows
- [ ] Challenge: 4,823-email backlog — an assumption that became a bug
- [ ] Solution: Domain pre-filter pattern — why rules beat LLM for known cases
- [ ] Solution: Shared config architecture decision
- [ ] Result: The numbers — what shipped and what it replaced
- [ ] Lesson: Human-in-the-loop is a feature, not a limitation
- [ ] Lesson: Version your recipes — v1 to v20 is the process, not failure
- [ ] Lesson: Test with production data constraints
- [ ] Reflection: AI doesn't replace judgment — it moves where judgment gets applied
- [ ] Next Steps: Security hardening, cloud migration, Amazon expansion
