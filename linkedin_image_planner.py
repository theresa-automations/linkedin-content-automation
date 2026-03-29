"""
LinkedIn Image Planner - v1.0
Theresa Erhumwunse | LinkedIn Content System

Step 1 of 2 in image generation.
Reads all approved drafts and produces image-plan.json — a structured
specification of every diagram to generate, including full Mermaid code.

Run after approving drafts in drafts.md:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_image_planner.py"

Then run linkedin_image_gen.py to render the actual images from the plan.
"""

import subprocess
import sys
import os
import datetime
import pathlib
from datetime import timezone, timedelta

PLANNER_WORKFLOW = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-IMAGE-GEN-WORKFLOW.md"
LOG_DIR          = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"
CLAUDE_CLI       = r"C:\Users\pc\.local\bin\claude.exe"
MCP_CONFIG       = r"C:\Users\pc\Documents\LinkedIn Project\linkedin_mcp_config.json"
TIMEOUT_SECONDS  = None  # No timeout — plan generation runs until complete

def setup_log_dir():
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"image-plan-{date_str}.log")

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
LINKEDIN IMAGE PLANNER - v1.0
================================================================================
Run started:  {now}
Purpose:      Read approved drafts, write image-plan.json with Mermaid diagrams
Workflow:     {PLANNER_WORKFLOW}
MCP Config:   {MCP_CONFIG}
Log file:     {log_path}
Timeout:      None (runs until complete)
================================================================================
"""
    print(header)
    write_log(log_path, header)

    if not os.path.exists(PLANNER_WORKFLOW):
        log(log_path, f"[ERROR] Workflow not found: {PLANNER_WORKFLOW}")
        sys.exit(1)

    with open(PLANNER_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = f.read()

    log(log_path, f"[OK] Workflow loaded — {len(workflow)} chars")
    log(log_path, "[INFO] Invoking Claude CLI to plan image progression...")
    log(log_path, "[INFO] This may take 10-15 minutes. Do not close this window.\n")

    prompt = (
        "Read and execute every step of the following workflow exactly as instructed.\n"
        "Your output is image-plan.json — a complete machine-readable image specification.\n"
        "Write valid JSON only in that file. Every mermaid_diagram field must contain\n"
        "complete, renderable Mermaid diagram code using actual line breaks in node labels.\n"
        "Output the full image plan report at the end.\n\n"
        f"{workflow}"
    )

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"]       = "1"

        result = subprocess.run(
            [CLAUDE_CLI, "--print", "--dangerously-skip-permissions", "--mcp-config", MCP_CONFIG],
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

        footer = (
            f"\n[SUCCESS] Planning completed at {datetime.datetime.now().strftime('%H:%M:%S')}\n"
            "[NEXT]    Review image-plan.json in your LinkedIn Project folder\n"
            "[NEXT]    Run linkedin_image_gen.py to render all images"
        ) if result.returncode == 0 else f"\n[WARNING] Exit code: {result.returncode}"

        print(footer)
        write_log(log_path, footer)

    except FileNotFoundError:
        log(log_path, f"[ERROR] Claude CLI not found: {CLAUDE_CLI}")
        sys.exit(1)
    except Exception as e:
        log(log_path, f"[ERROR] {e}")
        sys.exit(1)

    log(log_path, f"[INFO] Log saved: {log_path}")

if __name__ == "__main__":
    main()
