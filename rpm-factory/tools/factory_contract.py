"""Validate the Kestrel RPM factory/Tine contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
CONTRACT = ROOT / "rpm-factory" / "config" / "factory-contract.json"


def main() -> int:
    missing = []
    if not (ROOT / "AGENTS.md").exists():
        missing.append("AGENTS.md")
    if not list(SKILLS.glob("*/SKILL.md")):
        missing.append(".agents/skills/*/SKILL.md")
    for relative in ("tine.toml", ".buckconfig", ".gitmodules", "rpm-factory/BUCK"):
        if not (ROOT / relative).is_file():
            missing.append(relative)
    if not CONTRACT.is_file():
        missing.append(str(CONTRACT.relative_to(ROOT)))
    else:
        contract = json.loads(CONTRACT.read_text())
        expected = {
            "contract": "kestrel-rpm-factory",
            "registry": "ghcr.io/huntedraven7/rpm-factory",
            "rpm_suffix": ".hum1.rpmfactory",
            "build_system": "tine",
            "tine_commit": "4c80c7bd771233002b36ec80568d3a252a468aa2",
        }
        for key, value in expected.items():
            if contract.get(key) != value:
                print(f"factory contract mismatch: {key}={contract.get(key)!r} (expected {value!r})")
                return 1
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    n = len(list(SKILLS.glob("*/SKILL.md")))
    print(f"factory contract OK ({n} skills indexed; Tine pinned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
