"""Renovate custom managers must actually match what they claim to track.

A regex manager that silently matches nothing produces zero PRs with zero
errors (this happened: depName-before-version patterns never matched the
version-first file layout). This test mirrors each manager's extraction
against the real files and requires full coverage.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _managers():
    return json.loads((ROOT / "renovate.json").read_text())["customManagers"]


def _compile(pattern):
    """Renovate (JS) named groups to Python syntax for local validation."""
    return re.compile(pattern.replace("(?<", "(?P<"))


def _by_description(fragment):
    for m in _managers():
        if fragment in m["description"]:
            return m
    raise AssertionError(f"manager missing: {fragment}")


def test_github_manager_covers_all_github_entries():
    m = _by_description("github-tags packages")
    raw = (ROOT / "pigeon" / "config" / "upstream-sources.json").read_text()
    got = {(dep, ver) for ver, dep in _compile(m["matchStrings"][0]).findall(raw)}
    want = set()
    data = json.loads(raw)["packages"]
    for entry in data.values():
        r = entry.get("renovate", {})
        if r.get("datasource") == "github-tags":
            want.add((r["depName"], entry["version"]))
    assert want, "no github-tags entries found (test bug?)"
    assert got == want, f"unmatched: {sorted(want - got)[:5]}"


def test_gitlab_manager_covers_all_gitlab_entries():
    m = _by_description("gitlab-tags packages")
    raw = (ROOT / "pigeon" / "config" / "upstream-sources.json").read_text()
    got = {(dep, ver) for ver, dep in _compile(m["matchStrings"][0]).findall(raw)}
    want = set()
    data = json.loads(raw)["packages"]
    for entry in data.values():
        r = entry.get("renovate", {})
        if r.get("datasource") == "gitlab-tags":
            want.add((r["depName"], entry["version"]))
    assert want, "no gitlab-tags entries found (test bug?)"
    assert got == want, f"unmatched: {sorted(want - got)[:5]}"


def test_uupd_manager_matches_flavors():
    m = _by_description("uupd version")
    raw = (ROOT / "config" / "flavors.json").read_text()
    assert m["depNameTemplate"] == "ublue-os/uupd"
    assert _compile(m["matchStrings"][0]).search(raw), "uupd version not extracted"


def test_base_image_manager_matches_pinned_digest():
    m = _by_description("BASE_IMAGE digest pin")
    for image in ("warbler/Containerfile", "woodpecker/Containerfile"):
        raw = (ROOT / image).read_text()
        match = _compile(m["matchStrings"][0]).search(raw)
        assert match, f"{image}: BASE_IMAGE digest not extracted"
        assert "TODO" not in raw.split("ARG BASE_IMAGE=")[1].split("\n")[0]
