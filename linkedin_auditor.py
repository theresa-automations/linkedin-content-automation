"""
LinkedIn Auditor Agent - v3.0
Theresa Erhumwunse | LinkedIn Content System

Runs every Sunday at 6 PM WAT via Windows Task Scheduler.
Audits PENDING REVIEW drafts, scores them, and auto-regenerates
failed drafts using audit failure patterns as generator context.

REGENERATION LOGIC:
  Pass rate >= 80% AND failed checks score >= 70%:
    SELECTIVE REGEN — only failed drafts regenerated immediately
  Pass rate < 50% OR failed checks score < 70%:
    FULL BATCH REGEN — entire batch regenerated immediately
  Pass rate 50-79%:
    FULL BATCH REGEN — too many failures for selective
  After 3 attempts: ESCALATE TO THERESA

SAFEGUARD: AUDITOR APPROVED never triggers posting.
Theresa must manually change to APPROVED in drafts.md.
This applies until auditor is validated across 5 projects.

Usage:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_auditor.py"
"""

import subprocess
import sys
import os
import json
import re
import glob
import datetime
import pathlib
from datetime import timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linkedin_drive_sync import sync_to_drive

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

AUDITOR_WORKFLOW   = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-AUDITOR-WORKFLOW.md"
GENERATOR_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-GENERATOR-WORKFLOW.md"
DRAFTS_FILE        = r"C:\Users\pc\Documents\LinkedIn Project\drafts.md"
SCHEDULE_FILE      = r"C:\Users\pc\Documents\LinkedIn Project\schedule.md"
IMAGES_DIR         = r"C:\Users\pc\Documents\LinkedIn Project\images"
AUDIT_REPORT       = r"C:\Users\pc\Documents\LinkedIn Project\audit-report.md"
IMAGE_LOG          = r"C:\Users\pc\Documents\LinkedIn Project\image-log.md"
AUDIT_STATE        = r"C:\Users\pc\Documents\LinkedIn Project\audit-state.json"
LOG_DIR            = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI         = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG         = r"C:\Users\pc\Documents\LinkedIn Project\auditor_mcp_config.json"
IMAGE_GEN_SCRIPT   = r"C:\Users\pc\Documents\LinkedIn Project\linkedin_image_gen.py"

WAT_OFFSET         = 1
RUN_DAY            = 6        # Sunday
RUN_HOUR           = 18       # 6 PM WAT
MAX_ATTEMPTS       = 3
TIMEOUT_SECONDS    = 1800  # 30 minutes max per Claude CLI call


# ── THRESHOLDS ─────────────────────────────────────────────────────────────────

SELECTIVE_PASS_RATE       = 80.0   # >= this + checks score >= 70 = selective regen
SELECTIVE_CHECKS_SCORE    = 70.0   # failed drafts must score above this for selective
FULL_BATCH_PASS_RATE      = 50.0   # < this = full batch regen regardless of checks score
FULL_BATCH_CHECKS_SCORE   = 70.0   # < this = full batch regen regardless of pass rate


# ── HELPERS ────────────────────────────────────────────────────────────────────

def get_wat_now():
    return datetime.datetime.now(timezone.utc) + timedelta(hours=WAT_OFFSET)

def setup_dirs():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path(attempt):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"auditor-run-attempt{attempt}-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

def is_run_time():
    wat = get_wat_now()
    return (wat.weekday() == RUN_DAY)

def load_audit_state():
    if not os.path.exists(AUDIT_STATE):
        return {
            "attempt_number": 1,
            "previously_passed_drafts": [],
            "failure_patterns": "",
            "escalate_to_theresa": False
        }
    with open(AUDIT_STATE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_audit_state(state):
    with open(AUDIT_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def clear_audit_state():
    if os.path.exists(AUDIT_STATE):
        os.remove(AUDIT_STATE)

def get_pending_draft_numbers():
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    pending = []
    sections = content.split("## Draft #")
    for section in sections[1:]:
        if "**Status:** PENDING REVIEW" in section:
            match = re.match(r"(\d+)", section)
            if match:
                pending.append(int(match.group(1)))
    return sorted(pending)

def get_approved_draft_numbers():
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    approved = []
    sections = content.split("## Draft #")
    for section in sections[1:]:
        if "**Status:** AUDITOR APPROVED" in section:
            match = re.match(r"(\d+)", section)
            if match:
                approved.append(int(match.group(1)))
    return sorted(approved)

def get_approved_not_posted_draft_numbers():
    """Returns draft numbers with status APPROVED (not AUDITOR APPROVED, not POSTED)."""
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    approved = []
    sections = content.split("## Draft #")
    for section in sections[1:]:
        if "**Status:** APPROVED" in section and "**Status:** AUDITOR APPROVED" not in section:
            match = re.match(r"(\d+)", section)
            if match:
                approved.append(int(match.group(1)))
    return sorted(approved)

def get_failed_draft_numbers():
    """Returns draft numbers with AUDITOR FLAGGED or AUDITOR REJECTED status."""
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    failed = []
    sections = content.split("## Draft #")
    for section in sections[1:]:
        if "**Status:** AUDITOR FLAGGED" in section or "**Status:** AUDITOR REJECTED" in section:
            match = re.match(r"(\d+)", section)
            if match:
                failed.append(int(match.group(1)))
    return sorted(failed)

def determine_regen_mode(pass_rate, avg_failed_checks_score, attempt, pending_drafts):
    """
    Pure Python threshold logic — determines regeneration mode from audit scores.
    This is intentionally NOT delegated to Claude. Deterministic math belongs in Python.

    Returns: (regen_mode, drafts_to_regen)
    """
    if pass_rate == 100.0:
        return "NONE", []

    if attempt >= MAX_ATTEMPTS:
        return "ESCALATE", []

    failed_drafts = get_failed_draft_numbers()

    if pass_rate >= SELECTIVE_PASS_RATE and avg_failed_checks_score >= SELECTIVE_CHECKS_SCORE:
        return "SELECTIVE", failed_drafts
    else:
        # Covers: pass_rate < 50, avg_failed < 70, and grey zone 50-79%
        return "FULL_BATCH", pending_drafts

def get_image_audited_draft_numbers():
    """Returns draft numbers that already have IMAGE PASSED in image-log.md.
    These are skipped in image audit mode — no need to re-audit passed images."""
    if not os.path.exists(IMAGE_LOG):
        return []
    with open(IMAGE_LOG, "r", encoding="utf-8") as f:
        content = f.read()
    passed = []
    for line in content.splitlines():
        if "IMAGE PASSED" in line and line.strip().startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                try:
                    passed.append(int(parts[1]))
                except ValueError:
                    continue
    return sorted(set(passed))

def write_image_audit_results(passed_drafts, flagged_drafts, cycle_num):
    """Appends IMAGE PASSED / IMAGE FLAGGED entries to image-log.md after an audit cycle."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"\n## Image Audit — {now} (Cycle #{cycle_num})\n",
        "| Draft # | Status | Notes |",
        "|---------|--------|-------|",
    ]
    for d in sorted(passed_drafts):
        lines.append(f"| {d} | IMAGE PASSED | Passed audit cycle #{cycle_num} |")
    for d in sorted(flagged_drafts):
        lines.append(f"| {d} | IMAGE FLAGGED | Flagged cycle #{cycle_num} — regeneration triggered |")
    with open(IMAGE_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def get_flagged_images():
    pattern = os.path.join(IMAGES_DIR, "post-*.review.png")
    flagged = []
    for path in glob.glob(pattern):
        filename = os.path.basename(path)
        try:
            draft_num = int(filename.replace("post-", "").replace(".review.png", ""))
            flagged.append(draft_num)
        except ValueError:
            continue
    return sorted(flagged)

def parse_audit_scores_from_output(output):
    """
    Parse pass rate and avg failed checks score from Claude's audit output.
    Returns (pass_rate, avg_failed_checks_score, regen_mode, drafts_to_regen)
    """
    pass_rate = None
    avg_failed = None
    regen_mode = None
    drafts_to_regen = []

    # Try to find pass rate
    pr_match = re.search(r'pass.?rate[:\s]+(\d+\.?\d*)%?', output, re.IGNORECASE)
    if pr_match:
        pass_rate = float(pr_match.group(1))

    # Try to find avg failed checks score
    afc_match = re.search(r'avg.{1,20}failed.{1,30}score[:\s]+(\d+\.?\d*)%?', output, re.IGNORECASE)
    if afc_match:
        avg_failed = float(afc_match.group(1))

    # Try to find regen mode
    if re.search(r'REGEN_MODE[:\s]+SELECTIVE|SELECTIVE REGEN', output, re.IGNORECASE):
        regen_mode = "SELECTIVE"
    elif re.search(r'REGEN_MODE[:\s]+FULL_BATCH|FULL BATCH REGEN|FULL_BATCH REGEN', output, re.IGNORECASE):
        regen_mode = "FULL_BATCH"
    elif re.search(r'REGEN_MODE[:\s]+NONE|pass_rate.*100|all.*passed', output, re.IGNORECASE):
        regen_mode = "NONE"
    elif re.search(r'ESCALATE', output, re.IGNORECASE):
        regen_mode = "ESCALATE"

    # Try to find drafts to regen
    dr_match = re.search(r'drafts_to_regen[:\s]+\[([^\]]+)\]', output, re.IGNORECASE)
    if dr_match:
        nums = re.findall(r'\d+', dr_match.group(1))
        drafts_to_regen = [int(n) for n in nums]

    return pass_rate, avg_failed, regen_mode, drafts_to_regen


# ── CLAUDE CLI RUNNER ──────────────────────────────────────────────────────────

def run_claude_cli(prompt, log_path, label="Claude CLI"):
    env = os.environ.copy()
    env["PYTHONIOENCODING"]              = "utf-8"
    env["PYTHONUTF8"]                    = "1"
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "65536"

    result = subprocess.run(
        [CLAUDE_CLI, "--print", "--dangerously-skip-permissions",
         "--mcp-config", MCP_CONFIG],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=TIMEOUT_SECONDS
    )

    if result.stdout:
        write_log(log_path, f"\n--- {label} OUTPUT ---\n")
        write_log(log_path, result.stdout)

    if result.stderr:
        write_log(log_path, "\n--- STDERR ---\n")
        write_log(log_path, result.stderr)

    return result


# ── DRAFT AUDIT ────────────────────────────────────────────────────────────────

def run_draft_audit(pending_drafts, attempt_number, failure_patterns, log_path):
    if not os.path.exists(AUDITOR_WORKFLOW):
        log(log_path, f"[ERROR] Auditor workflow not found: {AUDITOR_WORKFLOW}")
        return None

    with open(AUDITOR_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    prev_patterns = ""
    if failure_patterns:
        prev_patterns = (
            f"\n\nPREVIOUS ATTEMPT FAILURE PATTERNS — AVOID THESE IN THIS AUDIT:\n"
            f"{failure_patterns}\n"
        )

    prompt = (
        f"Execute STEPS 1, 2, 3, 4, and 5 of the auditor workflow. Attempt #{attempt_number} of {MAX_ATTEMPTS}.\n"
        f"Drafts to audit (PENDING REVIEW only): {pending_drafts}\n"
        f"Skip any draft with status APPROVED, AUDITOR APPROVED, or POSTED.\n"
        f"{prev_patterns}\n"
        "Score every draft using the 5-check scoring system.\n"
        "Calculate pass_rate and avg_failed_checks_score.\n"
        "Update each draft status and append audit blocks to drafts.md.\n"
        "Append to audit-report.md.\n"
        "Write audit-state.json with ONLY these fields:\n"
        "  run_date, total_drafts, passed_drafts, failed_drafts,\n"
        "  pass_rate, avg_failed_checks_score, failure_patterns.\n"
        "Do NOT include regen_mode, drafts_to_regen, or escalate_to_theresa — Python calculates these.\n"
        "Output the full auditor report with pass_rate and avg_failed_checks_score clearly stated.\n\n"
        f"{workflow}"
    )

    return run_claude_cli(prompt, log_path, f"DRAFT AUDIT — Attempt #{attempt_number}")


# ── IMAGE AUDIT ────────────────────────────────────────────────────────────────

def run_image_audit(pending_drafts, attempt_number, log_path):
    images_to_check = [
        d for d in pending_drafts
        if os.path.exists(os.path.join(IMAGES_DIR, f"post-{d}.png"))
    ]

    missing = [d for d in pending_drafts if d not in images_to_check]
    if missing:
        log(log_path, f"[INFO] No image for drafts {missing} — runner will post text only")

    if not images_to_check:
        log(log_path, "[SKIP] No images to audit.")
        return None

    if not os.path.exists(AUDITOR_WORKFLOW):
        return None

    with open(AUDITOR_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    image_list = "\n".join([
        f"  Draft #{n}: {os.path.join(IMAGES_DIR, f'post-{n}.png')}"
        for n in images_to_check
    ])

    prompt = (
        f"Execute STEP 6 of the auditor workflow — IMAGE AUDIT only. Attempt #{attempt_number}.\n"
        f"Images to audit:\n{image_list}\n\n"
        "Read each image file via local-files MCP.\n"
        "Use your vision capability to inspect each diagram.\n"
        "Check for: clipped titles, floating dark boxes, text overflow, content match, readability.\n"
        "For FLAG or REJECT images: list the exact path to rename to .review.png\n"
        "Append image audit results to audit-report.md.\n"
        "Output image audit findings clearly listing any images to rename.\n\n"
        f"{workflow}"
    )

    result = run_claude_cli(prompt, log_path, f"IMAGE AUDIT — Attempt #{attempt_number}")

    # Rename flagged images based on Claude's output
    if result and result.stdout:
        for match in re.finditer(r'post-(\d+)\.png.*?(?:rename|flag|review)', result.stdout, re.IGNORECASE):
            draft_num   = int(match.group(1))
            image_path  = os.path.join(IMAGES_DIR, f"post-{draft_num}.png")
            review_path = os.path.join(IMAGES_DIR, f"post-{draft_num}.review.png")
            if os.path.exists(image_path):
                try:
                    os.rename(image_path, review_path)
                    log(log_path, f"[FLAGGED] Renamed post-{draft_num}.png to post-{draft_num}.review.png")
                except Exception as e:
                    log(log_path, f"[WARNING] Could not rename: {e}")

    return result


# ── SELECTIVE REGENERATION ─────────────────────────────────────────────────────

def run_selective_regen(drafts_to_regen, passed_drafts, failure_patterns, attempt_number, log_path):
    """Regenerate only the failed drafts, keeping passed drafts as narrative anchors."""
    log(log_path, f"[INFO] SELECTIVE REGEN — regenerating {len(drafts_to_regen)} draft(s): {drafts_to_regen}")
    log(log_path, f"[INFO] Passing drafts preserved as narrative anchors: {passed_drafts}")

    if not os.path.exists(GENERATOR_WORKFLOW):
        log(log_path, f"[ERROR] Generator workflow not found: {GENERATOR_WORKFLOW}")
        return None

    with open(GENERATOR_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    # Read current drafts to get context of passing drafts
    passing_context = ""
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
            drafts_content = f.read()
        passing_context = (
            f"\nPASSING DRAFTS CONTEXT (do not regenerate these — use as narrative anchors):\n"
            f"These drafts passed the audit and must NOT be changed.\n"
            f"Read them from drafts.md to understand the established narrative flow.\n"
            f"Draft numbers that passed: {passed_drafts}\n"
        )

    prompt = (
        f"SELECTIVE REGENERATION — Attempt #{attempt_number} of {MAX_ATTEMPTS}\n\n"
        f"You are regenerating ONLY these specific draft(s): {drafts_to_regen}\n"
        f"These drafts FAILED the quality audit and need to be rewritten.\n\n"
        f"{passing_context}\n"
        f"FAILURE PATTERNS TO AVOID (from the audit):\n"
        f"{failure_patterns}\n\n"
        "INSTRUCTIONS:\n"
        "1. Read drafts.md to understand the full narrative context\n"
        "2. Read the source manuscript from the Project Completed folder\n"
        "3. Read content-guidelines.md for all quality rules\n"
        "4. For EACH draft in the regeneration list:\n"
        "   a. Understand its position in the series and what the surrounding posts cover\n"
        "   b. Write a new post body that avoids ALL failure patterns listed above\n"
        "   c. Ensure every claim is directly verifiable in the source manuscript\n"
        "   d. Maintain narrative continuity with the passing drafts\n"
        "   e. Apply all 4 self-review passes before finalising\n"
        "   f. Update the draft in drafts.md:\n"
        "      - Replace post body with the new version\n"
        "      - Reset status to PENDING REVIEW (for re-audit)\n"
        "      - Remove any previous audit blocks\n"
        "5. Do NOT change any passing drafts\n"
        "6. Report which drafts were regenerated and what was changed\n\n"
        f"{workflow}"
    )

    return run_claude_cli(prompt, log_path, f"SELECTIVE REGEN — Attempt #{attempt_number}")


# ── FULL BATCH REGENERATION ────────────────────────────────────────────────────

def run_full_batch_regen(failure_patterns, attempt_number, log_path):
    """Clear all pending drafts and regenerate the entire batch."""
    log(log_path, f"[INFO] FULL BATCH REGEN — clearing all pending drafts and regenerating")

    if not os.path.exists(GENERATOR_WORKFLOW):
        log(log_path, f"[ERROR] Generator workflow not found: {GENERATOR_WORKFLOW}")
        return None

    with open(GENERATOR_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    prompt = (
        f"FULL BATCH REGENERATION — Attempt #{attempt_number} of {MAX_ATTEMPTS}\n\n"
        "The entire draft batch failed the quality audit and must be regenerated from scratch.\n\n"
        f"CRITICAL FAILURE PATTERNS TO AVOID (these caused the previous batch to fail):\n"
        f"{failure_patterns}\n\n"
        "INSTRUCTIONS:\n"
        "1. Read the source manuscript from the Project Completed folder\n"
        "2. Read content-guidelines.md for ALL quality rules\n"
        "3. Read drafts.md — clear ALL PENDING REVIEW, AUDITOR FLAGGED, and AUDITOR REJECTED drafts\n"
        "   (keep any APPROVED or POSTED drafts exactly as they are)\n"
        "4. Read schedule.md to understand the full posting schedule and total post count\n"
        "5. Regenerate the complete batch:\n"
        "   - Apply honest content audit — only include verifiable claims\n"
        "   - Every number, version, count must be directly from the manuscript\n"
        "   - Apply all 4 self-review passes to every draft\n"
        "   - Maintain full series continuity across all posts\n"
        "   - Set all new drafts to PENDING REVIEW\n"
        "6. Update drafts.md with the new complete batch\n"
        "7. Report total drafts regenerated\n\n"
        f"{workflow}"
    )

    return run_claude_cli(prompt, log_path, f"FULL BATCH REGEN — Attempt #{attempt_number}")


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    setup_dirs()
    wat_now = get_wat_now()

    # Day/time guard
    if not is_run_time():
        log_path = get_log_path(0)
        msg = (f"[SKIP] Not Sunday. "
               f"WAT: {wat_now.strftime('%A %H:%M')} | "
               f"Scheduled: Any time Sunday WAT")
        log(log_path, msg)
        sys.exit(0)

    # Load audit state to get attempt number
    state        = load_audit_state()
    attempt      = state.get("attempt_number", 1)
    log_path     = get_log_path(attempt)

    header = f"""
================================================================================
LINKEDIN AUDITOR AGENT - v3.0
================================================================================
Run started (WAT): {wat_now.strftime("%Y-%m-%d %H:%M:%S")} | {wat_now.strftime("%A")}
Attempt:           {attempt} of {MAX_ATTEMPTS}
Schedule:          Sunday at 6 PM WAT
MCP Config:        {MCP_CONFIG}
Log file:          {log_path}
================================================================================
THRESHOLDS:
  Selective regen: pass rate >= {SELECTIVE_PASS_RATE}% AND failed checks >= {SELECTIVE_CHECKS_SCORE}%
  Full batch regen: pass rate < {FULL_BATCH_PASS_RATE}% OR failed checks < {FULL_BATCH_CHECKS_SCORE}%
  Grey zone (50-79% pass rate): Full batch regen
  After {MAX_ATTEMPTS} attempts: Escalate to Theresa

SAFEGUARD: AUDITOR APPROVED never triggers posting automatically.
================================================================================
"""
    print(header)
    write_log(log_path, header)

    # Check for escalation from previous attempts
    if state.get("escalate_to_theresa"):
        escalation_msg = f"""
================================================================================
!! ESCALATION — {MAX_ATTEMPTS} AUDIT ATTEMPTS EXHAUSTED !!
================================================================================
The auditor has attempted {MAX_ATTEMPTS} regeneration cycles without reaching
the pass rate threshold. Manual intervention required.

Open drafts.md and audit-report.md for full findings.
Manually fix remaining AUDITOR FLAGGED and AUDITOR REJECTED drafts.
Change fixed drafts to PENDING REVIEW, then delete audit-state.json to reset.
================================================================================"""
        print(escalation_msg)
        write_log(log_path, escalation_msg)
        sys.exit(0)

    # Get pending drafts
    pending_drafts     = get_pending_draft_numbers()
    failure_patterns   = state.get("failure_patterns", "")
    prev_passed        = state.get("previously_passed_drafts", [])

    log(log_path, f"[INFO] Pending drafts: {pending_drafts if pending_drafts else 'None'}")

    # ── MODE SELECT ────────────────────────────────────────────────────────────
    # DRAFT AUDIT MODE : PENDING REVIEW drafts exist → audit drafts, skip images
    # IMAGE AUDIT MODE : no PENDING REVIEW drafts   → audit images for APPROVED drafts

    if pending_drafts:

        # ── DRAFT AUDIT MODE ───────────────────────────────────────────────────
        log(log_path, "[INFO] Mode: DRAFT AUDIT")

        # ── PART 1: DRAFT AUDIT ────────────────────────────────────────────────
        log(log_path, "\n" + "="*60)
        log(log_path, f"PART 1 — DRAFT AUDIT (Attempt #{attempt})")
        log(log_path, "="*60)

        draft_result = run_draft_audit(pending_drafts, attempt, failure_patterns, log_path)

        if draft_result is None or draft_result.returncode != 0:
            log(log_path, "[ERROR] Draft audit failed. Check log for details.")
            if draft_result and "hit your limit" in (draft_result.stdout or "").lower():
                log(log_path, "[INFO] Usage limit hit. Re-run after reset.")
            sys.exit(1)

        log(log_path, "[OK]   Draft audit completed.")
        if draft_result.stdout:
            print(draft_result.stdout)

        # Load scores written by Claude — Python makes the regen decision
        state        = load_audit_state()
        pass_rate    = state.get("pass_rate", 0)
        avg_failed   = state.get("avg_failed_checks_score", 0)
        new_patterns = state.get("failure_patterns", failure_patterns)
        passed_now   = get_approved_draft_numbers()
        all_passed   = sorted(set(prev_passed + passed_now))

        # Python applies threshold math — not Claude
        regen_mode, drafts_regen = determine_regen_mode(pass_rate, avg_failed, attempt, pending_drafts)

        log(log_path, f"\n[RESULT] Pass rate: {pass_rate}% | Avg failed checks: {avg_failed}%")
        log(log_path, f"[RESULT] Regeneration mode: {regen_mode} (decided by Python thresholds)")

        # Write Python's decision back to state
        state["attempt_number"]           = attempt
        state["regen_mode"]               = regen_mode
        state["drafts_to_regen"]          = drafts_regen
        state["previously_passed_drafts"] = all_passed
        state["failure_patterns"]         = new_patterns
        state["escalate_to_theresa"]      = (regen_mode == "ESCALATE")

        # ── REGENERATION DECISION ──────────────────────────────────────────────
        log(log_path, "\n" + "="*60)
        log(log_path, "REGENERATION DECISION")
        log(log_path, "="*60)

        if regen_mode == "NONE":
            log(log_path, "[OK] Pass rate threshold met. No regeneration needed.")
            log(log_path, f"[OK] AUDITOR APPROVED drafts: {passed_now}")
            log(log_path, "[NEXT] Change AUDITOR APPROVED to APPROVED in drafts.md to queue for posting.")
            clear_audit_state()

        elif regen_mode == "ESCALATE" or attempt >= MAX_ATTEMPTS:
            log(log_path, f"[!!] Attempt {attempt} of {MAX_ATTEMPTS} — threshold not met.")
            state["attempt_number"]      = attempt
            state["escalate_to_theresa"] = True
            save_audit_state(state)
            log(log_path, "[!!] ESCALATING TO THERESA — max attempts reached.")
            log(log_path, "[!!] Open drafts.md and audit-report.md. Manually fix remaining issues.")
            log(log_path, "[!!] Delete audit-state.json to reset the audit loop when ready.")

        elif regen_mode == "SELECTIVE":
            log(log_path, f"[INFO] SELECTIVE REGEN — regenerating {len(drafts_regen)} draft(s)")
            log(log_path, f"[INFO] Failure patterns passed to generator as context")

            state["attempt_number"]           = attempt + 1
            state["previously_passed_drafts"] = all_passed
            state["failure_patterns"]         = new_patterns
            save_audit_state(state)

            regen_result = run_selective_regen(
                drafts_regen, all_passed, new_patterns, attempt, log_path
            )

            if regen_result and regen_result.returncode == 0:
                log(log_path, "[OK] Selective regeneration complete.")
                log(log_path, f"[INFO] Regenerated drafts reset to PENDING REVIEW.")
                log(log_path, f"[INFO] Next audit (Attempt #{attempt+1}) runs next Sunday.")
                if regen_result.stdout:
                    print(regen_result.stdout)
            else:
                log(log_path, "[ERROR] Selective regeneration failed. Check log.")

        elif regen_mode == "FULL_BATCH":
            log(log_path, "[INFO] FULL BATCH REGEN — clearing all pending drafts")
            log(log_path, f"[INFO] Failure patterns passed to generator as context")

            state["attempt_number"]           = attempt + 1
            state["previously_passed_drafts"] = all_passed
            state["failure_patterns"]         = new_patterns
            save_audit_state(state)

            regen_result = run_full_batch_regen(new_patterns, attempt, log_path)

            if regen_result and regen_result.returncode == 0:
                log(log_path, "[OK] Full batch regeneration complete.")
                log(log_path, "[INFO] All drafts reset to PENDING REVIEW.")
                log(log_path, f"[INFO] Next audit (Attempt #{attempt+1}) runs next Sunday.")
                if regen_result.stdout:
                    print(regen_result.stdout)
            else:
                log(log_path, "[ERROR] Full batch regeneration failed. Check log.")

        # ── FINAL SUMMARY ──────────────────────────────────────────────────────
        footer = f"""
================================================================================
AUDITOR RUN COMPLETE — Attempt #{attempt} of {MAX_ATTEMPTS}
Pass rate: {pass_rate}% | Avg failed checks: {avg_failed}% | Mode: {regen_mode}
================================================================================
SAFEGUARD: AUDITOR APPROVED will NOT be posted automatically.
           Theresa must manually change to APPROVED in drafts.md.
================================================================================"""
        print(footer)
        write_log(log_path, footer)

        sync_ok, sync_msg = sync_to_drive(["drafts.md", "audit-report.md"])
        sync_line = f"\n[DRIVE SYNC] {sync_msg}"
        print(sync_line)
        write_log(log_path, sync_line)

    else:

        # ── IMAGE AUDIT MODE ───────────────────────────────────────────────────
        log(log_path, "[INFO] Mode: IMAGE AUDIT (no PENDING REVIEW drafts found)")

        approved_drafts  = get_approved_not_posted_draft_numbers()
        already_audited  = get_image_audited_draft_numbers()
        to_audit         = [d for d in approved_drafts if d not in already_audited]

        log(log_path, f"[INFO] APPROVED (not yet posted) drafts : {approved_drafts if approved_drafts else 'None'}")
        log(log_path, f"[INFO] Already image-audited (skipping) : {already_audited if already_audited else 'None'}")
        log(log_path, f"[INFO] Drafts to image-audit             : {to_audit if to_audit else 'None'}")

        if not to_audit:
            log(log_path, "[SKIP] All approved images already audited. Nothing to do.")
            sys.exit(0)

        def _run_image_audit_cycle(cycle_num, drafts):
            """Run one image audit cycle on given drafts. Returns (passed, flagged) lists."""
            log(log_path, "\n" + "="*60)
            log(log_path, f"IMAGE AUDIT — Cycle #{cycle_num} | Drafts: {drafts}")
            log(log_path, "="*60)
            run_image_audit(drafts, cycle_num, log_path)
            flagged = get_flagged_images()
            passed  = [d for d in drafts if d not in flagged]
            if flagged:
                log(log_path, f"[INFO] {len(flagged)} image(s) flagged: {flagged}")
            else:
                log(log_path, "[OK] No images flagged.")
            return passed, flagged

        # Cycle 1 — initial image audit
        passed, flagged = _run_image_audit_cycle(1, to_audit)
        write_image_audit_results(passed, flagged, 1)

        if flagged:
            log(log_path, "[ACTION] Triggering linkedin_image_gen.py --check for regeneration...")
            gen_result = subprocess.run(
                [sys.executable, IMAGE_GEN_SCRIPT, "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if gen_result.stdout:
                print(gen_result.stdout)
                write_log(log_path, gen_result.stdout)
            if gen_result.returncode == 0:
                log(log_path, "[OK] Image regeneration complete. Running re-audit...")
            else:
                log(log_path, "[ERROR] Image regeneration failed. Check output above.")

            # Cycle 2 — re-audit only the previously flagged images
            passed2, flagged = _run_image_audit_cycle(2, flagged)
            write_image_audit_results(passed2, flagged, 2)

            if flagged:
                log(log_path, f"[!!] {len(flagged)} image(s) still flagged after regeneration.")
                log(log_path, "[!!] Manual review required. Inspect flagged images.")
            else:
                log(log_path, "[OK] All images passed re-audit.")

        footer = f"""
================================================================================
IMAGE AUDIT COMPLETE
Approved drafts checked : {len(to_audit)}
Already audited (skipped): {len(already_audited)}
Images flagged after final check: {len(flagged)}
================================================================================"""
        print(footer)
        write_log(log_path, footer)

        sync_ok, sync_msg = sync_to_drive(["audit-report.md", "image-log.md"])
        sync_line = f"\n[DRIVE SYNC] {sync_msg}"
        print(sync_line)
        write_log(log_path, sync_line)

    log(log_path, f"[INFO] Log saved: {log_path}")


if __name__ == "__main__":
    main()
