"""
LinkedIn Schedule Sync - v1.0
Theresa Erhumwunse | LinkedIn Content System

One-time script. Syncs schedule.md status fields to match drafts.md.
Fixes the current batch where 11 APPROVED drafts show PENDING REVIEW in schedule.md.

Run once manually:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_schedule_sync.py"

This script does not need to be run again after this fix.
Going forward, the generator and posting workflows maintain sync automatically.
"""

import subprocess
import sys
import os
import datetime
import pathlib

SYNC_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-SCHEDULE-SYNC-WORKFLOW.md"
LOG_DIR       = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI    = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG    = r"C:\Users\pc\AppData\Roaming\Claude\claude_desktop_config.json"

TIMEOUT_SECONDS = None

def setup_log_dir():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"schedule-sync-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

def main():
    setup_log_dir()
    log_path = get_log_path()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""
================================================================================
LINKEDIN SCHEDULE SYNC - v1.0
================================================================================
Run started:  {now}
Purpose:      Sync schedule.md status to match drafts.md for Posts 5-15
              No draft content will be changed
Workflow:     {SYNC_WORKFLOW}
MCP Config:   {MCP_CONFIG}
Log file:     {log_path}
================================================================================
"""
    print(header)
    write_log(log_path, header)

    if not os.path.exists(SYNC_WORKFLOW):
        log(log_path, f"[ERROR] Sync workflow not found at: {SYNC_WORKFLOW}")
        sys.exit(1)

    with open(SYNC_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    log(log_path, f"[OK] Workflow loaded — {len(workflow)} chars")
    log(log_path, "[INFO] Invoking Claude CLI to sync schedule.md...")

    prompt = (
        "Read and execute every step of the following workflow exactly as instructed.\n"
        "Your only job is to sync schedule.md status fields to match drafts.md.\n"
        "Do NOT change any draft content. Do NOT post anything to LinkedIn.\n"
        "Output the full sync report at the end.\n\n"
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

        if result.returncode == 0:
            footer = (
                f"\n[SUCCESS] Sync completed at {datetime.datetime.now().strftime('%H:%M:%S')}\n"
                "[NEXT]    Open schedule.md and confirm Posts 5-15 now show APPROVED\n"
                "[DONE]    This script does not need to be run again"
            )
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
