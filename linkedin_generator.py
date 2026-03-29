"""
LinkedIn Content Generator - v2.0
Theresa Erhumwunse | LinkedIn Content System

Runs automatically every Saturday at 9 AM, 12 PM, and 6 PM WAT via Task Scheduler.
Checks for new project files in the Project Completed folder.
If a new project is found, generates the full post batch automatically.
If no new project is found, exits cleanly with no action.

No manual intervention required. Add a new numbered .md file to the
Project Completed folder and the next Saturday check will pick it up.
"""

import subprocess
import sys
import os
import datetime
import pathlib
from datetime import timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linkedin_drive_sync import sync_to_drive

# CONFIGURATION

GENERATOR_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-GENERATOR-WORKFLOW.md"
GENERATION_LOG     = r"C:\Users\pc\Documents\LinkedIn Project\generation-log.md"
PROJECT_FOLDER     = r"C:\Users\pc\Documents\LinkedIn Project\Project Completed"
LOG_DIR            = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI         = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG         = r"C:\Users\pc\Documents\LinkedIn Project\linkedin_mcp_config.json"

WAT_OFFSET         = 1
TIMEOUT_SECONDS    = None  # No timeout - generation runs until complete

# HELPERS

def get_wat_now():
    return datetime.datetime.now(timezone.utc) + timedelta(hours=WAT_OFFSET)

def setup_log_dir():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"generation-run-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

def get_processed_projects():
    """Read generation-log.md and return set of already-processed filenames."""
    if not os.path.exists(GENERATION_LOG):
        return set()
    with open(GENERATION_LOG, "r", encoding="utf-8") as f:
        content = f.read()
    processed = set()
    for line in content.splitlines():
        # Table rows start with | and contain the filename in column 2
        if line.startswith("|") and ".md" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                filename = parts[2].strip()
                if filename and filename != "File Name" and ".md" in filename:
                    processed.add(filename)
    return processed

def get_project_files():
    """List all .md files in Project Completed folder, sorted numerically."""
    if not os.path.exists(PROJECT_FOLDER):
        return []
    files = [f for f in os.listdir(PROJECT_FOLDER) if f.endswith(".md")]
    # Sort by leading number: "1 name.md" < "2 name.md" < "10 name.md"
    def sort_key(filename):
        try:
            return int(filename.split(" ")[0])
        except ValueError:
            return 9999
    return sorted(files, key=sort_key)

def find_new_project():
    """Return the lowest-numbered project file not yet in the generation log."""
    all_files = get_project_files()
    processed = get_processed_projects()
    for filename in all_files:
        if filename not in processed:
            return filename
    return None

# MAIN

def main():
    setup_log_dir()
    log_path = get_log_path()
    wat_now  = get_wat_now()

    header = f"""
================================================================================
LINKEDIN CONTENT GENERATOR - v2.0
================================================================================
Run started (WAT): {wat_now.strftime("%Y-%m-%d %H:%M:%S")} | {wat_now.strftime("%A")}
Schedule:          Every Saturday at 9 AM, 12 PM, and 6 PM WAT
Workflow:          {GENERATOR_WORKFLOW}
MCP Config:        {MCP_CONFIG}
Log file:          {log_path}
Timeout:           None (runs until complete)
================================================================================
"""
    print(header)
    write_log(log_path, header)

    # Day guard - only run on Saturdays (weekday 5)
    if wat_now.weekday() != 5:
        msg = (
            f"[SKIP] Today is {wat_now.strftime('%A')} — generator only runs on Saturdays. "
            f"Task Scheduler misconfiguration suspected. Exiting."
        )
        log(log_path, msg)
        sys.exit(0)

    log(log_path, f"[OK] Saturday confirmed — proceeding with project check.")

    # Check for new project files
    log(log_path, f"[INFO] Scanning: {PROJECT_FOLDER}")
    new_project = find_new_project()

    if not new_project:
        log(log_path, "[SKIP] No new projects found. All files in Project Completed are already processed.")
        log(log_path, "[INFO] To add a new project: drop a numbered .md file into the Project Completed folder.")
        log(log_path, f"[INFO] Next check: next Saturday at 9 AM, 12 PM, or 6 PM WAT.")
        write_log(log_path, "\n[DONE] No action taken.")
        sys.exit(0)

    log(log_path, f"[NEW PROJECT FOUND] {new_project}")
    log(log_path, f"[INFO] Invoking Claude CLI to generate full post batch...")
    log(log_path, f"[INFO] This may take 10-20 minutes. Do not close this window.\n")

    # Verify workflow file
    if not os.path.exists(GENERATOR_WORKFLOW):
        log(log_path, f"[ERROR] Generator workflow not found at: {GENERATOR_WORKFLOW}")
        sys.exit(1)

    with open(GENERATOR_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    log(log_path, f"[OK] Workflow loaded - {len(workflow)} chars")

    prompt = (
        "Read and execute every step of the following workflow exactly as instructed.\n"
        "Take as long as needed. Generate all posts completely. Do not rush or truncate.\n"
        "Apply all 4 self-review passes to every post before writing it to the queue.\n"
        "Output the full generation report at the end.\n\n"
        f"{workflow}"
    )

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"]            = "utf-8"
        env["PYTHONUTF8"]                  = "1"
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "65536"

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
            footer = f"\n[SUCCESS] Generation completed at {datetime.datetime.now().strftime('%H:%M:%S')}"
        else:
            footer = f"\n[WARNING] Completed with exit code: {result.returncode}"

        print(footer)
        write_log(log_path, footer)

        sync_ok, sync_msg = sync_to_drive(["drafts.md", "schedule.md", "generation-log.md"])
        sync_line = f"\n[DRIVE SYNC] {sync_msg}"
        print(sync_line)
        write_log(log_path, sync_line)

    except FileNotFoundError:
        log(log_path, f"[ERROR] Claude CLI not found at: {CLAUDE_CLI}")
        sys.exit(1)

    except Exception as e:
        log(log_path, f"[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)

    log(log_path, f"[INFO] Log saved to: {log_path}")

if __name__ == "__main__":
    main()
