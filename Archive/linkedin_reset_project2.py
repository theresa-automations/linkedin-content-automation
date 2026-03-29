"""
LinkedIn Project 2 Reset Script - v1.0
Theresa Erhumwunse | One-time cleanup script

Clears all project 2 data to allow clean regeneration.
Project 1 data is completely untouched.

Run once manually:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_reset_project2.py"

What this script does:
  1. drafts.md       — removes project 2 drafts only (keeps project 1)
  2. schedule.md     — removes project 2 schedule rows only (keeps project 1)
  3. generation-log.md — removes project 2 entry so generator redetects it
  4. audit-report.md — clears the audit report entirely (project 2 only so far)
  5. audit-state.json — deletes if present (resets audit loop to attempt 1)

Does NOT touch:
  - image-plan.json  (project 1 images still needed)
  - images/ folder   (project 1 images still needed)
  - run-logs/        (kept for audit history)
  - Any project 1 draft, schedule entry, or posted content
"""

import os
import re
import sys
import datetime
import pathlib

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

BASE_DIR         = r"C:\Users\pc\Documents\LinkedIn Project"
DRAFTS_FILE      = os.path.join(BASE_DIR, "drafts.md")
SCHEDULE_FILE    = os.path.join(BASE_DIR, "schedule.md")
GENERATION_LOG   = os.path.join(BASE_DIR, "generation-log.md")
AUDIT_REPORT     = os.path.join(BASE_DIR, "audit-report.md")
AUDIT_STATE      = os.path.join(BASE_DIR, "audit-state.json")

PROJECT2_SOURCE  = "2 linkedin-automation-system.md"
PROJECT2_MARKER  = "2 linkedin"   # used for loose matching in schedule/log

# Backup directory — originals saved here before any changes
BACKUP_DIR       = os.path.join(BASE_DIR, "Archive", "reset-backup-" +
                   datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))


# ── HELPERS ────────────────────────────────────────────────────────────────────

def log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def backup_file(filepath):
    """Save a copy of the file before modifying it."""
    if not os.path.exists(filepath):
        return
    pathlib.Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    filename    = os.path.basename(filepath)
    backup_path = os.path.join(BACKUP_DIR, filename)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"  [BACKUP] {filename} → {backup_path}")

def write_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ── 1. CLEAN DRAFTS.MD ─────────────────────────────────────────────────────────

def clean_drafts():
    log("Cleaning drafts.md — removing project 2 drafts only...")

    if not os.path.exists(DRAFTS_FILE):
        log("  [SKIP] drafts.md not found.")
        return

    backup_file(DRAFTS_FILE)

    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into individual draft sections
    # Each draft starts with "## Draft #N"
    parts    = re.split(r'(?=^## Draft #\d+)', content, flags=re.MULTILINE)
    header   = parts[0] if parts else ""
    drafts   = parts[1:] if len(parts) > 1 else []

    kept     = []
    removed  = []

    for draft in drafts:
        # Check if this draft belongs to project 2
        if PROJECT2_SOURCE.lower() in draft.lower():
            # Extract draft number for reporting
            num_match = re.match(r'## Draft #(\d+)', draft)
            num = num_match.group(1) if num_match else "?"
            removed.append(num)
        else:
            kept.append(draft)

    if not removed:
        log("  [INFO] No project 2 drafts found in drafts.md.")
        return

    new_content = header + "".join(kept)
    write_file(DRAFTS_FILE, new_content)

    log(f"  [OK] Removed {len(removed)} project 2 draft(s): {removed}")
    log(f"  [OK] Kept {len(kept)} project 1 draft(s) untouched.")


# ── 2. CLEAN SCHEDULE.MD ───────────────────────────────────────────────────────

def clean_schedule():
    log("Cleaning schedule.md — removing project 2 rows only...")

    if not os.path.exists(SCHEDULE_FILE):
        log("  [SKIP] schedule.md not found.")
        return

    backup_file(SCHEDULE_FILE)

    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    lines       = content.splitlines(keepends=True)
    kept        = []
    removed     = 0
    in_p2_notes = False

    for line in lines:
        # Detect project 2 schedule notes section
        if PROJECT2_MARKER.lower() in line.lower() and "schedule" in line.lower():
            in_p2_notes = True

        # Remove table rows referencing project 2
        if "|" in line and PROJECT2_MARKER.lower() in line.lower():
            removed += 1
            continue

        # Remove project 2 schedule notes block
        if in_p2_notes and line.strip() and not line.startswith("#"):
            if PROJECT2_MARKER.lower() in line.lower():
                removed += 1
                continue

        kept.append(line)

    # Also remove rows with POST PENDING or PENDING REVIEW that belong to p2
    # These are identified by post numbers that are project 2 posts (16+)
    # since project 1 has posts 1-15
    kept2   = []
    removed2 = 0
    for line in kept:
        if "|" in line:
            # Check if this is a data row (not header or separator)
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 3:
                try:
                    post_num = int(cells[1])
                    if post_num >= 16:  # Project 2 posts start at 16
                        removed2 += 1
                        continue
                except ValueError:
                    pass
        kept2.append(line)

    total_removed = removed + removed2
    write_file(SCHEDULE_FILE, "".join(kept2))

    if total_removed:
        log(f"  [OK] Removed {total_removed} project 2 schedule row(s).")
    else:
        log("  [INFO] No project 2 schedule rows found.")
    log("  [OK] Project 1 schedule entries untouched.")


# ── 3. CLEAN GENERATION-LOG.MD ─────────────────────────────────────────────────

def clean_generation_log():
    log("Cleaning generation-log.md — removing project 2 entry...")

    if not os.path.exists(GENERATION_LOG):
        log("  [SKIP] generation-log.md not found.")
        return

    backup_file(GENERATION_LOG)

    with open(GENERATION_LOG, "r", encoding="utf-8") as f:
        content = f.read()

    lines   = content.splitlines(keepends=True)
    kept    = []
    removed = 0

    for line in lines:
        if PROJECT2_SOURCE.lower() in line.lower():
            removed += 1
            continue
        kept.append(line)

    write_file(GENERATION_LOG, "".join(kept))

    if removed:
        log(f"  [OK] Removed project 2 entry from generation-log.md.")
        log(f"  [OK] Generator will redetect '2 linkedin-automation-system.md' on next run.")
    else:
        log("  [INFO] Project 2 entry not found in generation-log.md.")


# ── 4. CLEAR AUDIT-REPORT.MD ───────────────────────────────────────────────────

def clear_audit_report():
    log("Clearing audit-report.md...")

    if not os.path.exists(AUDIT_REPORT):
        log("  [SKIP] audit-report.md not found.")
        return

    backup_file(AUDIT_REPORT)

    # Write a fresh empty audit report with header only
    fresh = """# Audit Report
This file records all auditor agent runs.
Each run appends a new section with draft and image audit findings.

---
"""
    write_file(AUDIT_REPORT, fresh)
    log("  [OK] audit-report.md cleared and reset to empty state.")


# ── 5. DELETE AUDIT-STATE.JSON ─────────────────────────────────────────────────

def delete_audit_state():
    log("Checking audit-state.json...")

    if not os.path.exists(AUDIT_STATE):
        log("  [SKIP] audit-state.json not found — audit loop already at clean state.")
        return

    backup_file(AUDIT_STATE)
    os.remove(AUDIT_STATE)
    log("  [OK] audit-state.json deleted — audit loop reset to attempt 1.")


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("""
================================================================================
LINKEDIN PROJECT 2 RESET SCRIPT - v1.0
================================================================================
This script will clean project 2 data from 5 files.
Project 1 data will NOT be touched.
All files are backed up before modification.
================================================================================
""")

    # Confirm before proceeding
    response = input("Proceed with reset? (y/n): ").strip().lower()
    if response != "y":
        print("[STOPPED] No changes made.")
        sys.exit(0)

    print()
    log(f"Backup location: {BACKUP_DIR}")
    print()

    # Run all cleanup steps
    clean_drafts()
    print()
    clean_schedule()
    print()
    clean_generation_log()
    print()
    clear_audit_report()
    print()
    delete_audit_state()

    print(f"""
================================================================================
RESET COMPLETE
================================================================================
Files cleaned:
  drafts.md          — project 2 drafts removed, project 1 untouched
  schedule.md        — project 2 rows removed, project 1 untouched
  generation-log.md  — project 2 entry removed
  audit-report.md    — cleared and reset
  audit-state.json   — deleted (audit loop reset to attempt 1)

Backups saved to:
  {BACKUP_DIR}

NOT touched:
  image-plan.json    — project 1 images still valid
  images/ folder     — project 1 images still valid
  run-logs/          — kept for audit history

NEXT STEPS:
  1. Update 2 linkedin-automation-system.md with latest improvements
  2. Replace the file in Project Completed folder
  3. Run the generator:
     python "C:\\Users\\pc\\Documents\\LinkedIn Project\\linkedin_generator.py"
  4. Wait for generation to complete
  5. Auditor will run next Sunday at 6 PM WAT automatically
================================================================================
""")

if __name__ == "__main__":
    main()
