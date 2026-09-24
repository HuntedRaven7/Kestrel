#!/usr/bin/env python3
"""Detect stale commit pins in upstream-sources.json extra_sources.

Primary sources are version-pinned (Renovate owns bumps), but secondary
inputs can be commit-pinned (immutable URLs, stable staged filenames).
A pin never fails a build when upstream moves — it just silently builds
old code. This tool compares each pinned SHA against the tracked branch
HEAD and reports drift.

Usage:
  drift_check.py [--package PKG] [--json] [--report DIR]

  --package PKG  scope to one package (default: all entries with extras)
  --json         print the machine-readable report instead of human text
  --report DIR   also write drift-report.json + drift-report.md into DIR

Exit codes: 0 = all pins current (floating/unsupported entries are
informational, not drift), 1 = at least one pin drifted, 2 = tool error.

Lock schema (per extra_sources entry):
  filename      staged name (what the spec references)
  url_template  download URL; a 40-hex SHA inside means "pinned"
  sha512        recorded digest (verified by source_pipeline fetch)
  track         branch the pin follows (optional; defaults to the repo's
                default branch via the GitHub API)

Only github.com archive URLs are supported for HEAD comparison; anything
else reports "unsupported-host". Network failures report "error" (never
"current" — absence of evidence is not evidence of freshness). Uses
GITHUB_TOKEN from the environment when present (higher API rate limit).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "rpm-factory" / "config" / "upstream-sources.json"
GITHUB_API = "https://api.github.com"
SHA_RE = re.compile(r"/archive/([0-9a-f]{40})\.(?:tar\.gz|zip)\s*$")
REPO_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/archive/")


def api_fetch(url: str) -> dict:
    """GET a GitHub API URL, returning parsed JSON. Raises on failure."""
    headers = {"User-Agent": "kestrel-drift-check/1",
               "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 403 and "rate limit" in (exc.read().decode(errors="replace") or "").lower():
            raise RuntimeError("GitHub API rate limit exceeded "
                               "(set GITHUB_TOKEN to raise it)") from exc
        raise RuntimeError(f"GitHub API {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error for {url}: {exc}") from exc


def parse_pin(url: str) -> tuple[str, str, str] | None:
    """Split a commit-pinned github archive URL into (owner, repo, sha).
    Returns None when the URL is not a pinned github archive URL."""
    repo = REPO_RE.search(url or "")
    sha = SHA_RE.search(url or "")
    if not repo or not sha:
        return None
    return repo.group(1), repo.group(2), sha.group(1)


def repo_default_branch(owner: str, repo: str, fetch=api_fetch) -> str:
    return fetch(f"{GITHUB_API}/repos/{owner}/{repo}")["default_branch"]


def branch_head(owner: str, repo: str, branch: str, fetch=api_fetch) -> str:
    return fetch(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}")["sha"]


def check_extra(pkg: str, extra: dict, fetch=api_fetch) -> dict:
    """Compare one extra's pin against its tracked branch HEAD."""
    filename = extra.get("filename", "")
    url = (extra.get("url_template") or "")
    base = {"package": pkg, "filename": filename, "url": url,
            "pinned": None, "branch": None, "head": None,
            "compare": None, "status": "unsupported-host", "reason": None}
    parsed = parse_pin(url)
    if parsed is None:
        if "github.com/" in url:
            base["status"] = "floating"
            base["reason"] = "no commit SHA in URL; tracks live upstream"
        else:
            base["reason"] = "only github.com archive URLs are supported"
        return base
    owner, repo, pinned = parsed
    base["pinned"] = pinned
    try:
        branch = extra.get("track") or repo_default_branch(owner, repo, fetch)
        head = branch_head(owner, repo, branch, fetch)
    except (RuntimeError, KeyError) as exc:
        base["status"] = "error"
        base["reason"] = str(exc)
        return base
    base["branch"] = branch
    base["head"] = head
    base["compare"] = f"https://github.com/{owner}/{repo}/compare/{pinned}...{head}"
    if head == pinned:
        base["status"] = "current"
    else:
        base["status"] = "drifted"
        base["reason"] = f"tracked branch {branch!r} moved to {head[:12]}"
    return base


def check_all(data: dict, package: str | None = None, fetch=api_fetch) -> list[dict]:
    """Check every extra_sources entry (optionally scoped to one package)."""
    results = []
    for name in sorted(data.get("packages", {})):
        if package and name != package:
            continue
        for extra in data["packages"][name].get("extra_sources", []) or []:
            results.append(check_extra(name, extra, fetch))
    return results


def render_markdown(results: list[dict]) -> str:
    lines = ["# Upstream pin drift report", ""]
    drifted = [r for r in results if r["status"] == "drifted"]
    if not results:
        return "\n".join(lines + ["No commit-pinned extra_sources found."])
    lines.append("| Package | File | Status | Detail |")
    lines.append("|---|---|---|---|")
    for r in results:
        detail = ""
        if r["status"] == "drifted":
            detail = f"{r['pinned'][:12]} → {r['head'][:12]} ([compare]({r['compare']}))"
        elif r["reason"]:
            detail = r["reason"]
        elif r["status"] == "current":
            detail = f"pinned to {r['branch']}@{r['pinned'][:12]}"
        lines.append(f"| {r['package']} | {r['filename']} | {r['status']} | {detail} |")
    lines += ["", f"{len(drifted)} of {len(results)} pins drifted."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Detect stale upstream pins")
    ap.add_argument("--package", "-p", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", default=None,
                    help="write drift-report.json + drift-report.md into DIR")
    args = ap.parse_args(argv)
    try:
        data = json.loads(SOURCES.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {SOURCES}: {exc}", file=sys.stderr)
        return 2
    if args.package and args.package not in data.get("packages", {}):
        print(f"ERROR: no upstream-sources.json entry for {args.package}",
              file=sys.stderr)
        return 2
    results = check_all(data, args.package)
    if args.report:
        outdir = Path(args.report)
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "drift-report.json").write_text(
            json.dumps(results, indent=2) + "\n")
        (outdir / "drift-report.md").write_text(render_markdown(results))
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            extra = f" ({r['reason']})" if r.get("reason") else ""
            print(f"{r['package']}/{r['filename']}: {r['status']}{extra}")
        if not results:
            print("no commit-pinned extra_sources found")
    if any(r["status"] == "error" for r in results):
        return 2
    return 1 if any(r["status"] == "drifted" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
