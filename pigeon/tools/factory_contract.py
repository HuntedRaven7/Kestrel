"""Factory contract checks run by `just check` (stub; grows with skills)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"


def main() -> int:
    missing = []
    if not (ROOT / "AGENTS.md").exists():
        missing.append("AGENTS.md")
    if not list(SKILLS.glob("*/SKILL.md")):
        missing.append(".agents/skills/*/SKILL.md")
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    n = len(list(SKILLS.glob("*/SKILL.md")))
    print(f"factory contract OK ({n} skills indexed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
