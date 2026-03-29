#!/usr/bin/env python3
"""
LinkedIn Image Post Helper - v2.0
Theresa Erhumwunse | LinkedIn Content System

Posts text + image to LinkedIn via direct API call (no MCP).
Uses the current LinkedIn REST API (/rest/images + /rest/posts).
Reads credentials from linkedin_mcp_config.json.

Usage:
  python linkedin_image_post.py --text "post text here" --image "C:\\path\\to\\image.png"

Exit codes:
  0 - success (prints LinkedIn Post ID to stdout)
  1 - failure (prints error to stderr)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

API_VERSION = "202601"

# ── HELPERS ────────────────────────────────────────────────────────────────────

def load_credentials():
    token     = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_id = os.environ.get("LINKEDIN_PERSON_ID", "")
    if not token or not person_id:
        raise RuntimeError(
            "LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_ID must be set as "
            "Windows System Environment Variables."
        )
    return token, person_id


def api_post(url, token, payload, include_version=True):
    """POST to LinkedIn REST API. Returns (status_code, response_text, response_headers)."""
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization":             f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type":              "application/json",
        "Content-Length":            str(len(data)),
    }
    if include_version:
        headers["LinkedIn-Version"] = API_VERSION
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, res.read().decode("utf-8"), dict(res.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), {}


def binary_put(upload_url, image_path, token):
    """PUT image binary to upload URL. New /rest/images URLs require Authorization."""
    with open(image_path, "rb") as f:
        data = f.read()
    headers = {
        "Authorization":  f"Bearer {token}",
        "Content-Type":   "application/octet-stream",
        "Content-Length": str(len(data)),
    }
    req = urllib.request.Request(upload_url, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


# ── LINKEDIN STEPS ─────────────────────────────────────────────────────────────

def register_image(token, person_id):
    """Step 1 - Initialize image upload via /rest/images API."""
    print("[Step 1] Registering image upload...", file=sys.stderr)
    author_urn = f"urn:li:person:{person_id}"
    payload = {
        "initializeUploadRequest": {
            "owner": author_urn
        }
    }
    status, body, _ = api_post(
        "https://api.linkedin.com/rest/images?action=initializeUpload",
        token, payload, include_version=True
    )
    if status != 200:
        raise RuntimeError(f"Register failed: {status} {body}")

    data       = json.loads(body)
    image_urn  = data["value"]["image"]
    upload_url = data["value"]["uploadUrl"]
    print(f"[Step 1] OK - image URN: {image_urn}", file=sys.stderr)
    return image_urn, upload_url


def upload_image(upload_url, image_path, token):
    """Step 2 - Upload image binary to the registered upload URL."""
    size = os.path.getsize(image_path)
    print(f"[Step 2] Uploading image ({size} bytes)...", file=sys.stderr)
    status, body = binary_put(upload_url, image_path, token)
    if status not in (200, 201):
        raise RuntimeError(f"Upload failed: {status} {body}")
    print(f"[Step 2] OK - upload returned {status}", file=sys.stderr)


def create_image_post(token, person_id, text, image_urn):
    """Step 3 - Create the LinkedIn post using /rest/posts API."""
    print("[Step 3] Creating post with image...", file=sys.stderr)
    author_urn = f"urn:li:person:{person_id}"
    payload = {
        "author":      author_urn,
        "commentary":  text,
        "visibility":  "PUBLIC",
        "distribution": {
            "feedDistribution":               "MAIN_FEED",
            "targetEntities":                 [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "id": image_urn
            }
        },
        "lifecycleState":            "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    status, body, headers = api_post(
        "https://api.linkedin.com/rest/posts",
        token, payload, include_version=True
    )
    if status != 201:
        raise RuntimeError(f"Post creation failed: {status} {body}")

    post_id = (
        headers.get("x-restli-id")
        or headers.get("X-RestLi-Id")
        or headers.get("location", "").split("/")[-1]
        or "unknown"
    )
    print(f"[Step 3] OK - Post ID: {post_id}", file=sys.stderr)
    return post_id


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post text + image to LinkedIn")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text",      help="Post text (single-line use only)")
    group.add_argument("--text-file", help="Path to .txt file containing the post text (use for multiline text)")
    parser.add_argument("--image", required=True, help="Absolute path to image file (PNG or JPG)")
    args = parser.parse_args()

    if args.text_file:
        if not os.path.exists(args.text_file):
            print(f"ERROR: Text file not found: {args.text_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.text_file, "r", encoding="utf-8") as f:
            post_text = f.read().strip()
    else:
        post_text = args.text

    if not post_text:
        print("ERROR: Post text is empty.", file=sys.stderr)
        sys.exit(1)

    # LinkedIn's /rest/posts API truncates commentary at ' | '
    # Replace with ' - ' so the series label renders fully
    post_text = post_text.replace(' | ', ' - ')

    if not os.path.exists(args.image):
        print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    try:
        token, person_id      = load_credentials()
        image_urn, upload_url = register_image(token, person_id)
        upload_image(upload_url, args.image, token)
        post_id               = create_image_post(token, person_id, post_text, image_urn)
        print(post_id)  # stdout only — for easy parsing by the runner
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
