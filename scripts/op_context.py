#!/usr/bin/env python3
"""
op_context.py — OpenProject context fetcher for Claude Code

Fetches a work package + its parent feature + all sibling tasks (children of same parent)
and prints a structured context block ready to paste into Claude Code.

Usage:
    python scripts/op_context.py 40
    python scripts/op_context.py 40 --copy      # also copies to clipboard (needs pyperclip)
    python scripts/op_context.py 40 --file       # saves to .claude_context (auto-read by Claude Code)
    python scripts/op_context.py 40 --no-siblings
    python scripts/op_context.py 40 --json       # raw JSON debug dump

Token resolution (per-developer):
    1. Env var OP_API_TOKEN (if set, used directly)
    2. GCP Secret Manager: op-api-token-{OP_DEVELOPER} in project opintegr
    3. Error with setup instructions

Setup (one time per developer):
    1. Generate personal API token in OpenProject:
       Avatar > My Account > Access Tokens > + API access token
    2. Store in GCP Secret Manager:
       gcloud secrets create op-api-token-yourname --replication-policy="automatic"
       echo -n "YOUR_TOKEN" | gcloud secrets versions add op-api-token-yourname --data-file=-
    3. Set env vars:
       export OP_DEVELOPER="yourname"
"""

import io
import os
import sys
import json
import argparse
import textwrap
import base64
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional

# Fix Windows console encoding for emoji/unicode output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# — Configuration ——————————————————————————————————————————————————————————————

DEFAULT_BASE_URL = "https://aidevs4seba2.openproject.com"
GCP_PROJECT = "opintegr"

STATUS_ICONS = {
    "New":              "\U0001f535",
    "In Specification": "\U0001f4dd",
    "Specified":        "\U0001f4dd",
    "Scheduled":        "\U0001f4c5",
    "In Progress":      "\U0001f528",
    "In Verification":  "\U0001f50d",
    "In Testing":       "\U0001f9ea",
    "In Review":        "\U0001f9ea",
    "UAT":              "\U0001f9ea",
    "Tested":           "\u2705",
    "Resolved":         "\u2705",
    "Closed":           "\u2714\ufe0f",
    "On Hold":          "\u23f8\ufe0f",
    "Rejected":         "\u274c",
}

DONE_STATUSES = {"Closed", "Resolved", "Tested", "Rejected"}
ACTIVE_STATUSES = {"In Progress", "In Verification", "In Testing", "In Review", "UAT"}


# — Token resolution ——————————————————————————————————————————————————————————

def get_token() -> str:
    """Resolve API token: env var first, then GCP Secret Manager (per-developer)."""
    token = os.environ.get("OP_API_TOKEN")
    if token:
        return token

    developer = os.environ.get("OP_DEVELOPER")
    if not developer:
        print(
            "ERROR: No OP_API_TOKEN env var and no OP_DEVELOPER set.\n\n"
            "Option 1 — set token directly:\n"
            "  export OP_API_TOKEN='your_token'\n\n"
            "Option 2 — use GCP Secret Manager (recommended):\n"
            "  export OP_DEVELOPER='yourfirstname'\n"
            "  # Token is read from: op-api-token-{OP_DEVELOPER} in GCP project opintegr\n\n"
            "Setup (one-time):\n"
            "  1. Generate token: OpenProject > My Account > Access Tokens\n"
            "  2. Store: gcloud secrets create op-api-token-yourname --replication-policy=automatic\n"
            "     echo -n 'TOKEN' | gcloud secrets versions add op-api-token-yourname --data-file=-\n"
            "  3. Auth: gcloud auth application-default login --project opintegr"
        )
        sys.exit(1)

    secret_name = f"op-api-token-{developer}"
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except ImportError:
        print(
            "ERROR: google-cloud-secret-manager not installed.\n"
            "Run: pip install google-cloud-secret-manager\n"
            "Or set OP_API_TOKEN env var directly."
        )
        sys.exit(1)
    except Exception as e:
        print(
            f"ERROR: Failed to read secret '{secret_name}' from GCP project '{GCP_PROJECT}'.\n"
            f"Details: {e}\n\n"
            "Check:\n"
            f"  1. Secret exists: gcloud secrets describe {secret_name} --project={GCP_PROJECT}\n"
            "  2. You're authenticated: gcloud auth application-default login\n"
            f"  3. You have access: gcloud secrets versions access latest --secret={secret_name}"
        )
        sys.exit(1)


def get_base_url() -> str:
    """Get OP base URL from env or default."""
    return os.environ.get("OP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


# — API helpers ————————————————————————————————————————————————————————————————

def api_get(path: str, token: str, base_url: str) -> dict:
    """Make authenticated GET request to OpenProject API v3."""
    url = f"{base_url}/api/v3{path}"
    credentials = base64.b64encode(f"apikey:{token}".encode()).decode()
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 401:
            print(
                f"HTTP 401 Unauthorized — your OP API token is invalid or expired.\n"
                "Generate a new one: OpenProject > My Account > Access Tokens\n"
                "Then update your GCP secret:\n"
                f"  echo -n 'NEW_TOKEN' | gcloud secrets versions add "
                f"op-api-token-{os.environ.get('OP_DEVELOPER', 'YOURNAME')} --data-file=-"
            )
        else:
            print(f"HTTP {e.code} from OpenProject API: {body[:300]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error to {url}: {e.reason}")
        sys.exit(1)


# — Data extraction ————————————————————————————————————————————————————————————

def get_wp(wp_id: int, token: str, base_url: str) -> dict:
    """Fetch a single work package by ID."""
    return api_get(f"/work_packages/{wp_id}", token, base_url)


def get_children(parent_id: int, token: str, base_url: str) -> list:
    """Fetch all child work packages of a parent."""
    import urllib.parse

    filters = json.dumps([{"parent": {"operator": "=", "values": [str(parent_id)]}}])
    path = (
        f"/work_packages?filters={urllib.parse.quote(filters)}"
        f"&pageSize=100&sortBy=%5B%5B%22id%22%2C%22asc%22%5D%5D"
    )
    data = api_get(path, token, base_url)
    return data.get("_embedded", {}).get("elements", [])


def extract_text(field: Optional[dict]) -> str:
    """Extract raw text from OP description/rich text field."""
    if not field:
        return ""
    return (field.get("raw") or "").strip()


def wp_status(wp: dict) -> str:
    return wp.get("_links", {}).get("status", {}).get("title", "Unknown")


def wp_assignee(wp: dict) -> str:
    return wp.get("_links", {}).get("assignee", {}).get("title", "Unassigned")


def wp_type(wp: dict) -> str:
    return wp.get("_links", {}).get("type", {}).get("title", "")


def wp_url(wp: dict, base_url: str) -> str:
    return f"{base_url}/work_packages/{wp.get('id', '')}"


# — Context formatting —————————————————————————————————————————————————————————

def format_context(
    target_wp: dict,
    parent_wp: Optional[dict],
    siblings: list,
    base_url: str,
) -> str:
    """Format full context block for Claude Code."""
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines += ["=" * 70, f"  OPENPROJECT CONTEXT — fetched {now}", "=" * 70, ""]

    # — Target task ————————————————————————————————————————————————————————
    t_id = target_wp.get("id")
    t_status = wp_status(target_wp)
    t_icon = STATUS_ICONS.get(t_status, "\u267b\ufe0f")
    t_desc = extract_text(target_wp.get("description"))
    t_work = target_wp.get("estimatedTime") or "not set"
    t_spent = target_wp.get("spentTime") or "0h"
    t_prio = target_wp.get("_links", {}).get("priority", {}).get("title", "")

    lines += [
        f"## YOUR TASK — OP-{t_id}",
        f"   {t_icon} [{t_status}]  {wp_type(target_wp)}: {target_wp.get('subject', '')}",
        f"   Assignee: {wp_assignee(target_wp)}  |  Priority: {t_prio}",
        f"   Work: {t_work}  |  Spent: {t_spent}  |  Due: {target_wp.get('dueDate') or 'no date'}",
        f"   URL: {wp_url(target_wp, base_url)}",
        "",
    ]

    if t_desc:
        lines += ["### Requirements / Description"]
        lines += [f"   {line}" for line in t_desc.split("\n")]
        lines += [""]

    # Custom fields (acceptance criteria often here)
    custom_fields = {
        k: v for k, v in target_wp.items() if k.startswith("customField") and v
    }
    if custom_fields:
        lines += ["### Custom Fields"]
        for k, v in custom_fields.items():
            val = extract_text(v) if isinstance(v, dict) else str(v)
            if val:
                lines.append(f"   {k}: {val}")
        lines += [""]

    # — Parent feature —————————————————————————————————————————————————————
    if parent_wp:
        p_id = parent_wp.get("id")
        p_status = wp_status(parent_wp)
        p_icon = STATUS_ICONS.get(p_status, "\u267b\ufe0f")
        p_desc = extract_text(parent_wp.get("description"))
        p_work = parent_wp.get("estimatedTime") or "not set"
        p_spent = parent_wp.get("spentTime") or "0h"

        lines += [
            f"## PARENT FEATURE — OP-{p_id}",
            f"   {p_icon} [{p_status}]  {wp_type(parent_wp)}: {parent_wp.get('subject', '')}",
            f"   Work budget: {p_work}  |  Spent so far (all tasks): {p_spent}",
            f"   URL: {wp_url(parent_wp, base_url)}",
            "",
        ]

        if p_desc:
            lines += ["### Feature Description / Business Context"]
            lines += [f"   {line}" for line in p_desc.split("\n")]
            lines += [""]

    # — Sibling tasks ——————————————————————————————————————————————————————
    other_siblings = [s for s in siblings if s.get("id") != t_id]
    if other_siblings:
        done_sibs = [s for s in other_siblings if wp_status(s) in DONE_STATUSES]
        active_sibs = [s for s in other_siblings if wp_status(s) in ACTIVE_STATUSES]
        pending_sibs = [
            s
            for s in other_siblings
            if wp_status(s) not in DONE_STATUSES
            and wp_status(s) not in ACTIVE_STATUSES
        ]

        parent_id_label = parent_wp.get("id") if parent_wp else "?"
        lines += [
            f"## SIBLING TASKS (all tasks under OP-{parent_id_label})",
            f"   Total: {len(other_siblings)}  |  Done: {len(done_sibs)}  |  "
            f"Active: {len(active_sibs)}  |  Pending: {len(pending_sibs)}",
            "",
        ]

        if active_sibs:
            lines += [
                "### IN PROGRESS right now (coordinate — may affect your work)"
            ]
            for s in active_sibs:
                lines.append(
                    f"   {STATUS_ICONS.get(wp_status(s), '\u267b\ufe0f')} OP-{s['id']} [{wp_status(s)}]  "
                    f"{s.get('subject', '')}  — {wp_assignee(s)}"
                )
            lines += [""]

        if done_sibs:
            lines += ["### COMPLETED (context: what exists)"]
            for s in done_sibs:
                lines.append(
                    f"   {STATUS_ICONS.get(wp_status(s), '\u267b\ufe0f')} OP-{s['id']} [{wp_status(s)}]  "
                    f"{s.get('subject', '')}"
                )
            lines += [""]

        if pending_sibs:
            lines += ["### PENDING (don't implement their scope yet)"]
            for s in pending_sibs:
                lines.append(
                    f"   {STATUS_ICONS.get(wp_status(s), '\u267b\ufe0f')} OP-{s['id']} [{wp_status(s)}]  "
                    f"{s.get('subject', '')}  — {wp_assignee(s)}"
                )
            lines += [""]

    # — Ready-to-paste prompt ——————————————————————————————————————————————
    lines += ["=" * 70, "  PASTE THIS INTO CLAUDE CODE:", "=" * 70, ""]

    prompt = _build_prompt(
        target_wp, parent_wp, [s for s in siblings if s.get("id") != t_id]
    )
    lines.append(prompt)
    lines += ["", "=" * 70]

    return "\n".join(lines)


def _build_prompt(
    target_wp: dict,
    parent_wp: Optional[dict],
    other_siblings: list,
) -> str:
    """Build ready-to-paste prompt for Claude Code."""
    t_id = target_wp.get("id")
    t_subject = target_wp.get("subject", "")
    t_desc = extract_text(target_wp.get("description"))

    done_sibs = [s for s in other_siblings if wp_status(s) in DONE_STATUSES]
    active_sibs = [s for s in other_siblings if wp_status(s) in ACTIVE_STATUSES]
    pending_sibs = [
        s
        for s in other_siblings
        if wp_status(s) not in DONE_STATUSES
        and wp_status(s) not in ACTIVE_STATUSES
    ]

    parts = [f'I\'m starting work on OP-{t_id}: "{t_subject}"', ""]

    if t_desc:
        parts += ["Requirements from OpenProject:", t_desc, ""]

    if parent_wp:
        p_desc = extract_text(parent_wp.get("description"))
        parts += [
            f"Parent feature — OP-{parent_wp.get('id')}: {parent_wp.get('subject', '')}",
        ]
        if p_desc:
            short = p_desc[:500] + ("..." if len(p_desc) > 500 else "")
            parts += [short]
        parts += [""]

    if done_sibs:
        parts += ["Already completed sibling tasks (what has already been built):"]
        for s in done_sibs:
            parts.append(
                f"  OP-{s['id']} [{wp_status(s)}]: {s.get('subject', '')}"
            )
        parts += [""]

    if active_sibs:
        parts += ["In-progress sibling tasks (coordinate to avoid conflicts):"]
        for s in active_sibs:
            parts.append(
                f"  OP-{s['id']} [{wp_status(s)}]: {s.get('subject', '')} — {wp_assignee(s)}"
            )
        parts += [""]

    if pending_sibs:
        parts += ["Pending sibling tasks (do NOT implement their scope in this task):"]
        for s in pending_sibs:
            parts.append(
                f"  OP-{s['id']} [{wp_status(s)}]: {s.get('subject', '')}"
            )
        parts += [""]

    parts += [
        "Please:",
        f"1. Confirm what specifically needs to be built for OP-{t_id}",
        "2. Identify which files need to be created or modified",
        "3. Flag any missing information to clarify with the PM before coding",
        "4. Check for scope overlap with in-progress sibling tasks",
        "5. Suggest the implementation plan — don't write code yet",
    ]

    return "\n".join(parts)


# — Main ——————————————————————————————————————————————————————————————————————

def main():
    parser = argparse.ArgumentParser(
        description="Fetch OpenProject context for Claude Code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python scripts/op_context.py 40
              python scripts/op_context.py 40 --copy
              python scripts/op_context.py 40 --file
              python scripts/op_context.py 40 --no-siblings
              python scripts/op_context.py 40 --json
        """),
    )
    parser.add_argument("wp_id", type=int, help="OpenProject Work Package ID")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy output to clipboard (pip install pyperclip)",
    )
    parser.add_argument(
        "--file",
        action="store_true",
        help="Save to .claude_context in repo root",
    )
    parser.add_argument(
        "--no-siblings",
        action="store_true",
        help="Skip fetching sibling tasks (faster)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump raw JSON of the work package (debug)",
    )
    args = parser.parse_args()

    token = get_token()
    base_url = get_base_url()

    target_wp = get_wp(args.wp_id, token, base_url)

    if args.json:
        print(json.dumps(target_wp, indent=2, ensure_ascii=False))
        return

    # Resolve parent
    parent_href = target_wp.get("_links", {}).get("parent", {}).get("href")
    parent_wp = None
    siblings: list = []

    if parent_href:
        parent_id = int(parent_href.rstrip("/").split("/")[-1])
        parent_wp = get_wp(parent_id, token, base_url)
        if not args.no_siblings:
            siblings = get_children(parent_id, token, base_url)
    elif not args.no_siblings:
        # WP has no parent — treat its own children as context
        siblings = get_children(args.wp_id, token, base_url)

    output = format_context(target_wp, parent_wp, siblings, base_url)
    print(output)

    if args.copy:
        try:
            import pyperclip

            pyperclip.copy(output)
            print("\nCopied to clipboard.")
        except ImportError:
            print("\npyperclip not installed: pip install pyperclip")

    if args.file:
        with open(".claude_context", "w", encoding="utf-8") as f:
            f.write(output)
        print("\nSaved to .claude_context — Claude Code reads this automatically.")


if __name__ == "__main__":
    main()
