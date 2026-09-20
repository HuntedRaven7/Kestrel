"""Tests for drift_check.py (all offline via a fake API fetcher)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_check as dc


def _fake(pins: dict):
    """Build a fetch() stub: {(owner, repo): (default_branch, head_sha)}."""
    def fetch(url: str):
        parts = url.split("/repos/")[1].split("/")
        owner, repo = parts[0], parts[1]
        default, head = pins[(owner, repo)]
        if url.endswith(f"/repos/{owner}/{repo}"):
            return {"default_branch": default}
        return {"sha": head}
    return fetch


PINNED = ("https://github.com/acme/lib/archive/"
          "d86f9903efb9c490c0e3b0316d7f2da5b5a5632c.tar.gz")


def test_current_pin():
    fetch = _fake({("acme", "lib"): ("master", "d86f9903efb9c490c0e3b0316d7f2da5b5a5632c")})
    r = dc.check_extra("pkg", {"filename": "x.tar.gz", "url_template": PINNED,
                               "track": "master"}, fetch)
    assert r["status"] == "current"
    assert r["head"] == r["pinned"]


def test_drifted_pin_reports_compare_link():
    fetch = _fake({("acme", "lib"): ("master", "f" * 40)})
    r = dc.check_extra("pkg", {"filename": "x.tar.gz", "url_template": PINNED,
                               "track": "master"}, fetch)
    assert r["status"] == "drifted"
    assert "compare" in r["compare"]
    assert r["pinned"] in r["compare"] and r["head"] in r["compare"]


def test_track_defaults_to_repo_default_branch():
    fetch = _fake({("acme", "lib"): ("main", "d86f9903efb9c490c0e3b0316d7f2da5b5a5632c")})
    r = dc.check_extra("pkg", {"filename": "x.tar.gz",
                               "url_template": PINNED}, fetch)
    assert r["status"] == "current"
    assert r["branch"] == "main"


def test_floating_url_is_informational():
    r = dc.check_extra("pkg", {"filename": "x.tar.gz",
                               "url_template": "https://github.com/acme/lib/archive/master.tar.gz"},
                       _fake({}))
    assert r["status"] == "floating"


def test_non_github_host_unsupported():
    r = dc.check_extra("pkg", {"filename": "x.tar.gz",
                               "url_template": "https://example.invalid/x.tar.gz"},
                       _fake({}))
    assert r["status"] == "unsupported-host"


def test_api_failure_is_error_not_current():
    def boom(url: str):
        raise RuntimeError("network down")
    r = dc.check_extra("pkg", {"filename": "x.tar.gz", "url_template": PINNED,
                               "track": "master"}, boom)
    assert r["status"] == "error"


def test_check_all_scopes_to_package():
    data = {"packages": {
        "a": {"extra_sources": [{"filename": "a.tar.gz", "url_template": PINNED}]},
        "b": {"extra_sources": [{"filename": "b.tar.gz", "url_template": PINNED}]},
    }}
    fetch = _fake({("acme", "lib"): ("master", "d86f9903efb9c490c0e3b0316d7f2da5b5a5632c")})
    assert {r["package"] for r in dc.check_all(data, "a", fetch)} == {"a"}
    assert len(dc.check_all(data, None, fetch)) == 2


def test_render_markdown_counts_drift():
    rows = [{"package": "p", "filename": "f", "status": "drifted",
             "pinned": "a" * 40, "head": "b" * 40,
             "compare": "http://x", "reason": "moved"}]
    md = dc.render_markdown(rows)
    assert "1 of 1 pins drifted" in md
