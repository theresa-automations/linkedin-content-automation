"""
LinkedIn Image Generator - v2.1
Theresa Erhumwunse | LinkedIn Content System

Step 2 of 2 in image generation.
Reads image-plan.json, renders diagrams via mmdc (Mermaid CLI),
adds canvas and watermark, saves to images/post-N.png.

NORMAL MODE — generate all images from plan:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_image_gen.py"

CHECK MODE — count flagged images, regenerate if 2 or more:
    python "C:/Users/pc/Documents/LinkedIn Project/linkedin_image_gen.py" --check

HOW TO FLAG A BAD IMAGE:
    Rename images/post-N.png to images/post-N.review.png
    Then run with --check flag

REGENERATION RULES:
    - 0 or 1 flagged: regenerates flagged images only (individually)
    - 2 or more flagged: regenerates ENTIRE batch from image-plan.json
      (same session = consistent progression, no visual disjoints)
"""

import sys
import os
import io
import json
import datetime
import pathlib
import tempfile
import subprocess
import glob

# CONFIGURATION
IMAGE_PLAN  = r"C:\Users\pc\Documents\LinkedIn Project\image-plan.json"
IMAGE_DIR   = r"C:\Users\pc\Documents\LinkedIn Project\images"
IMAGE_LOG   = r"C:\Users\pc\Documents\LinkedIn Project\image-log.md"
LOG_DIR     = r"C:\Users\pc\Documents\LinkedIn Project\run-logs"

WATERMARK_TEXT    = "Theresa AI Automations"
WATERMARK_OPACITY = 35
WATERMARK_SIZE    = 15
CANVAS_PADDING    = 48
TARGET_WIDTH      = 1200   # LinkedIn optimal image width (px)
TARGET_HEIGHT     = 644    # LinkedIn max image height (px)
RENDER_WIDTH      = 2400   # mmdc render width (2x target — scale down = sharp output)
REGEN_THRESHOLD   = 2      # full batch regen if this many or more are flagged


# ── UTILITIES ────────────────────────────────────────────────────────────────

def setup_dirs():
    pathlib.Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_log_path(prefix="image-gen"):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"{prefix}-{date_str}.log")

def write_log(log_path, content):
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(content + "\n")

def log(log_path, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    write_log(log_path, line)

WORKFLOW_FILE = r"C:\Users\pc\Documents\LinkedIn Project\LINKEDIN-IMAGE-GEN-WORKFLOW.md"

def load_plan():
    if not os.path.exists(IMAGE_PLAN):
        print(f"[ERROR] image-plan.json not found: {IMAGE_PLAN}")
        print("[INFO]  Run linkedin_image_planner.py first.")
        sys.exit(1)

    # Warn if plan is older than the workflow file — stale plan risk
    if os.path.exists(WORKFLOW_FILE):
        plan_mtime     = os.path.getmtime(IMAGE_PLAN)
        workflow_mtime = os.path.getmtime(WORKFLOW_FILE)
        if workflow_mtime > plan_mtime:
            plan_age     = datetime.datetime.fromtimestamp(plan_mtime).strftime("%Y-%m-%d %H:%M")
            workflow_age = datetime.datetime.fromtimestamp(workflow_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"")
            print(f"  ╔══════════════════════════════════════════════════════════╗")
            print(f"  ║  WARNING — STALE IMAGE PLAN DETECTED                    ║")
            print(f"  ║                                                          ║")
            print(f"  ║  image-plan.json was generated: {plan_age}         ║")
            print(f"  ║  Workflow file was updated:     {workflow_age}         ║")
            print(f"  ║                                                          ║")
            print(f"  ║  The plan was built before the latest quality rules.    ║")
            print(f"  ║  Images generated from this plan may have artifacts.    ║")
            print(f"  ║                                                          ║")
            print(f"  ║  RECOMMENDED: Run linkedin_image_planner.py first       ║")
            print(f"  ║  to regenerate image-plan.json with updated rules.      ║")
            print(f"  ╚══════════════════════════════════════════════════════════╝")
            print(f"")
            response = input("  Continue anyway? (y/n): ").strip().lower()
            if response != "y":
                print("[STOPPED] Run linkedin_image_planner.py first, then retry.")
                sys.exit(0)

    with open(IMAGE_PLAN, "r", encoding="utf-8") as f:
        return json.load(f)

def get_flagged_images():
    """Return list of draft numbers flagged for review (post-N.review.png)."""
    pattern = os.path.join(IMAGE_DIR, "post-*.review.png")
    flagged = []
    for path in glob.glob(pattern):
        filename = os.path.basename(path)
        try:
            # Extract N from post-N.review.png
            draft_num = int(filename.replace("post-", "").replace(".review.png", ""))
            flagged.append(draft_num)
        except ValueError:
            continue
    return sorted(flagged)


# ── MMDC RENDER ──────────────────────────────────────────────────────────────

def render_with_mmdc(diagram_source, render_width=RENDER_WIDTH):
    """Render Mermaid diagram locally via mmdc. Returns PNG bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mmd_path = os.path.join(tmpdir, "diagram.mmd")
        png_path = os.path.join(tmpdir, "diagram.png")

        with open(mmd_path, "w", encoding="utf-8") as f:
            f.write(diagram_source)

        result = subprocess.run(
            ["mmdc", "-i", mmd_path, "-o", png_path,
             "-w", str(render_width), "-b", "white"],
            capture_output=True, text=True, shell=True
        )

        if result.returncode != 0:
            raise Exception(f"mmdc failed:\n{result.stderr}")

        if not os.path.exists(png_path):
            raise Exception("mmdc ran but produced no output file.")

        with open(png_path, "rb") as f:
            return f.read()


# ── IMAGE PROCESSING ─────────────────────────────────────────────────────────

def add_canvas_and_watermark(png_bytes, series_label, watermark_text,
                              opacity, font_size, padding, output_path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    w, h = img.size

    # Scale to TARGET_WIDTH (mmdc renders at RENDER_WIDTH so this is a downscale — sharp)
    if w != TARGET_WIDTH:
        scale = TARGET_WIDTH / w
        img   = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        w, h  = img.size

    bottom_strip = 32
    canvas_w = w + padding * 2
    canvas_h = h + padding * 2 + bottom_strip
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    canvas.paste(img, (padding, padding), img)
    draw = ImageDraw.Draw(canvas)

    try:
        font_label = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        font_wm    = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   font_size)
    except Exception:
        try:
            font_label = ImageFont.truetype("arial.ttf", font_size)
            font_wm    = font_label
        except Exception:
            font_label = ImageFont.load_default()
            font_wm    = font_label

    label_y = canvas_h - font_size - 10
    draw.text((20, label_y), series_label, font=font_label, fill=(80, 100, 130, 160))

    bbox = draw.textbbox((0, 0), watermark_text, font=font_wm)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((canvas_w - tw - 20, canvas_h - th - 10),
              watermark_text, font=font_wm, fill=(100, 120, 150, opacity))

    # Cap height at TARGET_HEIGHT — scale down and pad width if needed
    if canvas.size[1] > TARGET_HEIGHT:
        ratio  = TARGET_HEIGHT / canvas.size[1]
        new_w  = int(canvas.size[0] * ratio)
        canvas = canvas.resize((new_w, TARGET_HEIGHT), Image.LANCZOS)
        if canvas.size[0] < TARGET_WIDTH:
            final  = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255, 255))
            final.paste(canvas, ((TARGET_WIDTH - canvas.size[0]) // 2, 0))
            canvas = final

    canvas.convert("RGB").save(output_path, "PNG", dpi=(300, 300))


# ── GENERATION ───────────────────────────────────────────────────────────────

def generate_images(items, plan, log_path, mode_label):
    watermark = plan.get("watermark", WATERMARK_TEXT)
    total     = plan.get("total_posts", len(plan.get("images", [])))
    results   = []
    generated = 0
    failed    = 0

    log(log_path, f"[INFO] {mode_label} — generating {len(items)} image(s)")

    for i, item in enumerate(items, 1):
        draft_num    = item.get("draft_number")
        post_num     = item.get("post_number")
        post_type    = item.get("post_type", "")
        stage        = item.get("stage", "")
        series_label = item.get("series_label", f"Part {post_num} of {total}")
        diagram_code = item.get("mermaid_diagram", "")
        output_path  = os.path.join(IMAGE_DIR, f"post-{draft_num}.png")
        review_path  = os.path.join(IMAGE_DIR, f"post-{draft_num}.review.png")

        log(log_path, f"[{i}/{len(items)}] Draft #{draft_num} | {post_type} | {stage}")

        if not diagram_code:
            log(log_path, f"  [SKIP] No diagram code for draft #{draft_num}")
            results.append({"draft_number": draft_num, "post_number": post_num,
                           "post_type": post_type, "stage": stage,
                           "success": False, "error": "No diagram code"})
            failed += 1
            continue

        try:
            png_bytes = render_with_mmdc(diagram_code)
            log(log_path, f"  [OK]   mmdc returned {len(png_bytes):,} bytes")
        except Exception as e:
            log(log_path, f"  [ERROR] mmdc failed: {e}")
            results.append({"draft_number": draft_num, "post_number": post_num,
                           "post_type": post_type, "stage": stage,
                           "success": False, "error": str(e)})
            failed += 1
            continue

        try:
            add_canvas_and_watermark(
                png_bytes, series_label, watermark,
                WATERMARK_OPACITY, WATERMARK_SIZE, CANVAS_PADDING, output_path
            )
            # Remove review flag if it existed
            if os.path.exists(review_path):
                os.remove(review_path)
                log(log_path, f"  [OK]   Review flag cleared")
            log(log_path, f"  [SAVED] {output_path}")
            results.append({"draft_number": draft_num, "post_number": post_num,
                           "post_type": post_type, "stage": stage, "success": True})
            generated += 1
        except Exception as e:
            log(log_path, f"  [ERROR] Canvas/watermark failed: {e}")
            results.append({"draft_number": draft_num, "post_number": post_num,
                           "post_type": post_type, "stage": stage,
                           "success": False, "error": str(e)})
            failed += 1

    return results, generated, failed


def update_image_log(results, mode_label):
    """
    Appends new entries to image-log.md.
    On regeneration runs, marks previous entries for regenerated drafts as SUPERSEDED.
    Full history is preserved — current state is always clear.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    regenerated_drafts = {r["draft_number"] for r in results if r["success"]}

    # If this is a regeneration run, mark old entries as SUPERSEDED
    if regenerated_drafts and os.path.exists(IMAGE_LOG):
        with open(IMAGE_LOG, "r", encoding="utf-8") as f:
            log_content = f.read()

        updated = []
        for line in log_content.splitlines():
            should_supersede = False
            if line.startswith("|") and ".png" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    try:
                        draft_num = int(parts[1])
                        if draft_num in regenerated_drafts:
                            if "GENERATED" in line or "FAILED" in line:
                                should_supersede = True
                    except ValueError:
                        pass
            if should_supersede:
                line = line.replace("| GENERATED |", "| SUPERSEDED |")
                line = line.replace("| FAILED", "| SUPERSEDED (was FAILED)")
            updated.append(line)

        with open(IMAGE_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(updated) + "\n")

    # Append new entries
    lines = [
        f"\n## {mode_label} — {now}\n",
        "| Draft # | Post # | Type | Stage | Status | File |",
        "|---------|--------|------|-------|--------|------|",
    ]
    for r in results:
        if "Regenerat" in mode_label:
            status = "REGENERATED" if r["success"] else f"REGEN FAILED — {r.get('error','')}"
        else:
            status = "GENERATED" if r["success"] else f"FAILED — {r.get('error','')}"
        lines.append(
            f"| {r['draft_number']} | {r['post_number']} | {r['post_type']} "
            f"| {r['stage']} | {status} | post-{r['draft_number']}.png |"
        )
    with open(IMAGE_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def print_summary(results, generated, failed, log_path):
    summary = f"""
================================================================================
GENERATION COMPLETE
Generated: {generated}  |  Failed: {failed}
Output:    {IMAGE_DIR}
"""
    if generated > 0:
        summary += "\nGenerated:\n"
        for r in results:
            if r["success"]:
                summary += f"  post-{r['draft_number']}.png  ({r['post_type']} | {r['stage']})\n"
    if failed > 0:
        summary += "\nFailed:\n"
        for r in results:
            if not r["success"]:
                summary += f"  Draft #{r['draft_number']}: {r.get('error','unknown')}\n"
    summary += """
TO FLAG A BAD IMAGE FOR REGENERATION:
  Rename: post-N.png  →  post-N.review.png
  Then run: python linkedin_image_gen.py --check

IF 2+ IMAGES ARE FLAGGED:
  Full batch regeneration runs automatically in one session.

IF FEWER THAN 2 ARE FLAGGED:
  Only the flagged images are regenerated individually.
================================================================================"""
    print(summary)
    write_log(log_path, summary)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    setup_dirs()
    check_mode = "--check" in sys.argv
    log_path   = get_log_path("image-check" if check_mode else "image-gen")
    now        = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""
================================================================================
LINKEDIN IMAGE GENERATOR - v2.0  |  Mode: {"CHECK" if check_mode else "GENERATE"}
================================================================================
Run started:  {now}
Image plan:   {IMAGE_PLAN}
Output dir:   {IMAGE_DIR}
Log file:     {log_path}
Threshold:    Full batch regen if {REGEN_THRESHOLD}+ images flagged
================================================================================
"""
    print(header)
    write_log(log_path, header)

    plan   = load_plan()
    images = plan.get("images", [])

    if check_mode:
        flagged = get_flagged_images()
        log(log_path, f"[INFO] Flagged images found: {len(flagged)} — {flagged}")

        if len(flagged) == 0:
            log(log_path, "[OK]   No images flagged. Nothing to regenerate.")
            log(log_path, "[INFO] To flag an image: rename post-N.png to post-N.review.png")
            sys.exit(0)

        if len(flagged) >= REGEN_THRESHOLD:
            log(log_path, f"[INFO] {len(flagged)} images flagged — threshold met.")
            log(log_path, "[INFO] Regenerating FULL BATCH in one session for visual consistency.")
            items      = images
            mode_label = f"Full Batch Regeneration ({len(flagged)} flagged, threshold {REGEN_THRESHOLD})"
        else:
            log(log_path, f"[INFO] {len(flagged)} image(s) flagged — below threshold.")
            log(log_path, f"[INFO] Regenerating flagged image(s) only: {flagged}")
            items      = [img for img in images if img.get("draft_number") in flagged]
            mode_label = f"Selective Regeneration ({len(flagged)} image(s))"

    else:
        log(log_path, f"[OK]   Plan loaded — {len(images)} images to generate")
        items      = images
        mode_label = "Full Generation"

    results, generated, failed = generate_images(items, plan, log_path, mode_label)

    try:
        update_image_log(results, mode_label)
        log(log_path, "[OK]   image-log.md updated")
    except Exception as e:
        log(log_path, f"[WARNING] Could not update image-log.md: {e}")

    print_summary(results, generated, failed, log_path)
    log(log_path, f"[INFO] Log saved: {log_path}")


if __name__ == "__main__":
    main()
