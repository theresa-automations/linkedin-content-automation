"""
LinkedIn Daily Poster - v3.0
Theresa Erhumwunse | LinkedIn Content System
Runs via Windows Task Scheduler at 9:00 AM WAT, Monday-Friday

This script ONLY posts. It does not generate content.
Expected runtime: under 2 minutes.
"""

import subprocess
import sys
import os
import datetime
import pathlib
from datetime import timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linkedin_drive_sync import sync_to_drive

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

POSTING_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-POSTING-WORKFLOW.md"
LOG_DIR          = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI       = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG       = r"C:\Users\pc\Documents\LinkedIn Project\linkedin_mcp_config.json"

# Business hours (WAT = UTC+1)
WAT_OFFSET          = 1
BUSINESS_HOUR_START = 8
BUSINESS_HOUR_END   = 18
BUSINESS_DAYS       = [0, 1, 2, 3, 4]  # Monday=0 to Friday=4

# Tight timeout — posting only should finish well within 5 minutes
TIMEOUT_SECONDS = 300

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_wat_now():
    return datetime.datetime.now(timezone.utc) + timedelta(hours=WAT_OFFSET)

def is_business_hours():
    wat = get_wat_now()
    return (
        wat.weekday() in BUSINESS_DAYS and
        BUSINESS_HOUR_START <= wat.hour < BUSINESS_HOUR_END
    )

def setup_log_dir():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"posting-run-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    setup_log_dir()
    log_path = get_log_path()
    wat_now  = get_wat_now()

    header = f"""
================================================================================
LINKEDIN DAILY POSTER — v3.0
================================================================================
Run started (WAT): {wat_now.strftime("%Y-%m-%d %H:%M:%S")} | {wat_now.strftime("%A")}
Workflow:          {POSTING_WORKFLOW}
MCP Config:        {MCP_CONFIG}
Log file:          {log_path}
Timeout:           {TIMEOUT_SECONDS}s ({TIMEOUT_SECONDS // 60} min)
================================================================================
"""
    print(header)
    write_log(log_path, header)

    # ── Business hours guard ──────────────────────────────────────────────────
    if not is_business_hours():
        msg = (
            f"[SKIP] Outside business hours. "
            f"WAT: {wat_now.strftime('%A %H:%M')} | "
            f"Allowed: Mon-Fri {BUSINESS_HOUR_START}:00-{BUSINESS_HOUR_END}:00 WAT"
        )
        log(log_path, msg)
        sys.exit(0)

    log(log_path, "[OK] Business hours confirmed.")

    # ── Verify workflow file ──────────────────────────────────────────────────
    if not os.path.exists(POSTING_WORKFLOW):
        log(log_path, f"[ERROR] Posting workflow not found at: {POSTING_WORKFLOW}")
        sys.exit(1)

    with open(POSTING_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    log(log_path, f"[OK] Posting workflow loaded — {len(workflow)} chars")

    prompt = (
        "Read and execute every step of the following workflow exactly as instructed.\n"
        "Do not generate new content. Only post, update files, and report.\n"
        "Output the full posting report at the end.\n\n"
        f"{workflow}"
    )

    log(log_path, "[INFO] Invoking Claude CLI...")

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"]       = "1"

        result = subprocess.run(
            [
                CLAUDE_CLI,
                "--print",
                "--dangerously-skip-permissions",
                "--mcp-config", MCP_CONFIG,
            ],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=TIMEOUT_SECONDS
        )

        if result.stdout:
            write_log(log_path, "\n─── CLAUDE OUTPUT ──────────────────────────────────────────────────────────\n")
            write_log(log_path, result.stdout)
            print(result.stdout)

        if result.stderr:
            write_log(log_path, "\n─── STDERR ─────────────────────────────────────────────────────────────────\n")
            write_log(log_path, result.stderr)
            print("[STDERR]", result.stderr, file=sys.stderr)

        if result.returncode == 0:
            footer = f"\n[SUCCESS] Run completed at {datetime.datetime.now().strftime('%H:%M:%S')} | Exit code: 0"
        else:
            footer = f"\n[WARNING] Completed with exit code: {result.returncode}"

        print(footer)
        write_log(log_path, footer)

        sync_ok, sync_msg = sync_to_drive(["drafts.md", "schedule.md", "audit-log.md"])
        sync_line = f"\n[DRIVE SYNC] {sync_msg}"
        print(sync_line)
        write_log(log_path, sync_line)

    except subprocess.TimeoutExpired:
        log(log_path, f"[ERROR] Timed out after {TIMEOUT_SECONDS // 60} minutes. Posting workflow should never take this long.")
        sys.exit(1)

    except FileNotFoundError:
        log(log_path, f"[ERROR] Claude CLI not found at: {CLAUDE_CLI}")
        sys.exit(1)

    except Exception as e:
        log(log_path, f"[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)

    log(log_path, f"[INFO] Log saved to: {log_path}")

if __name__ == "__main__":
    main()
