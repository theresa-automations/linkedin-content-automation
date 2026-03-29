"""
LinkedIn Draft Realignment - v1.0
Theresa Erhumwunse | LinkedIn Content System

One-time script. Adds series continuity elements to the 11 remaining
approved drafts without changing any body content.

Run once manually:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_realign.py"

After running, review drafts.md to confirm callbacks and teasers look right.
This script is not scheduled and does not need to be run again.
"""

import subprocess
import sys
import os
import datetime
import pathlib
from datetime import timezone, timedelta

# CONFIGURATION

REALIGN_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-REALIGN-WORKFLOW.md"
LOG_DIR          = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI       = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG       = r"C:\Users\pc\AppData\Roaming\Claude\claude_desktop_config.json"

TIMEOUT_SECONDS  = None  # No timeout — runs until complete

# HELPERS

def setup_log_dir():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"realign-run-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

# MAIN

def main():
    setup_log_dir()
    log_path = get_log_path()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""
================================================================================
LINKEDIN DRAFT REALIGNMENT - v1.0
================================================================================
Run started:  {now}
Purpose:      Add series continuity to 11 existing approved drafts
              Body content will NOT be changed
Workflow:     {REALIGN_WORKFLOW}
MCP Config:   {MCP_CONFIG}
Log file:     {log_path}
Timeout:      None (runs until complete)
================================================================================
"""
    print(header)
    write_log(log_path, header)

    # Verify workflow file exists
    if not os.path.exists(REALIGN_WORKFLOW):
        log(log_path, f"[ERROR] Realignment workflow not found at: {REALIGN_WORKFLOW}")
        log(log_path, f"[INFO]  Download LINKEDIN-REALIGN-WORKFLOW.md and place it in the LinkedIn Project folder.")
        sys.exit(1)

    with open(REALIGN_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    log(log_path, f"[OK] Workflow loaded — {len(workflow)} chars")
    log(log_path, "[INFO] Invoking Claude CLI to realign drafts...")
    log(log_path, "[INFO] This should take 5-10 minutes. Do not close this window.\n")

    prompt = (
        "Read and execute every step of the following workflow exactly as instructed.\n"
        "Your only job is to add series label, opening callback, and closing teaser "
        "to each APPROVED draft.\n"
        "Do NOT change any post body content. Do NOT change any status fields.\n"
        "Do NOT post anything to LinkedIn.\n"
        "Output the full realignment report at the end.\n\n"
        f"{workflow}"
    )

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
            write_log(log_path, "\n--- CLAUDE OUTPUT ----------------------------------------------------------\n")
            write_log(log_path, result.stdout)
            print(result.stdout)

        if result.stderr:
            write_log(log_path, "\n--- STDERR -----------------------------------------------------------------\n")
            write_log(log_path, result.stderr)
            print("[STDERR]", result.stderr, file=sys.stderr)

        if result.returncode == 0:
            footer = f"\n[SUCCESS] Realignment completed at {datetime.datetime.now().strftime('%H:%M:%S')}"
            footer += "\n[NEXT]    Open drafts.md and review the series label, callbacks, and teasers on each draft."
            footer += "\n[NEXT]    Edit any callback or teaser directly in drafts.md if adjustments are needed."
            footer += "\n[DONE]    This script does not need to be run again."
        else:
            footer = f"\n[WARNING] Completed with exit code: {result.returncode}"

        print(footer)
        write_log(log_path, footer)

    except FileNotFoundError:
        log(log_path, f"[ERROR] Claude CLI not found at: {CLAUDE_CLI}")
        sys.exit(1)

    except Exception as e:
        log(log_path, f"[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)

    log(log_path, f"[INFO] Log saved to: {log_path}")

if __name__ == "__main__":
    main()
