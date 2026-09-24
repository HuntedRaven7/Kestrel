#!/usr/bin/env python3
"""Audit recipe dirs for spec-referenced files (and optionally fetch them).

Fedora dist-git imports bring the spec + patches but often miss extra
Source1..N files (sysusers units, install scripts, .sig/keys, metainfo)
and lookaside archives. rpmbuild -bs then fails with 'Bad file'.

Usage:
  audit_sources.py                 # report MISSING files, exit 1 if any
  audit_sources.py --fix           # fetch missing dist-git/lookaside files
  audit_sources.py --fix -p foot    # same, scoped to one recipe (for CI matrix)

Rules:
  - The FIRST Source: line per spec is skipped: the staged verified
    archive satisfies Source0 positionally (source_pipeline fetch stages
    it under the lock filename).
  - Any reference resolving to our staged archive basename is skipped.
  - Plain filenames must exist in the recipe dir (macros like %{name} are
    expanded from the spec preamble best-effort).
  - Remote (http/ftp) values are warnings only, EXCEPT rpm URL#file
    fragments (e.g. openpgpkey keys), which are fetched into the recipe
    dir so hermetic builds don't need network.
- *-vendor.tar.bz2 (Go) is reported, not fetched: it must be GENERATED
  with go-vendor-tools (network + Go toolchain), a CI-lane job.
- Names declared in the lock's extra_sources are staged by
  source_pipeline.py fetch (build-time, hash-verified): skipped here so
  large binaries never need committing to git.
- --fix downloads from Fedora 46 dist-git (plain files) or the lookaside
  cache (archives + .sig files, via the dist-git `sources` hash file).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKGS = ROOT / "rpm-factory" / "packages"
DISTGIT = "https://src.fedoraproject.org/rpms/{pkg}/raw/f46/f/{file}"
LOOKASIDE = "https://src.fedoraproject.org/repo/pkgs/{pkg}/{file}/sha512/{hx}/{file}"
ARCHIVE_SUFFIX = (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz", ".zip", ".tar.zst")


def parse_spec(path: Path):
    """Return (macros, first_source_idx, checks) where checks is a list of
    (tag, raw_value) for every Source/Patch line except the first Source."""
    text = path.read_text()
    text = re.sub(r"\\\n", "", text)
    macros = {}
    for m in re.finditer(r"^%(?:global|define)\s+(\w+)\s+(.+?)\s*$", text, re.M):
        macros[m.group(1)] = m.group(2)
    name = version = ""
    m = re.search(r"^Name:\s*(\S+)", text, re.M)
    if m:
        name = m.group(1)
    m = re.search(r"^Version:\s*(\S+)", text, re.M)
    if m:
        version = m.group(1)
    macros.setdefault("name", name)
    macros.setdefault("version", version)
    # rpm defines lowercase %{url} from the URL: tag.
    m = re.search(r"^URL:\s*(\S+)", text, re.M)
    if m:
        macros.setdefault("url", m.group(1))
        macros.setdefault("URL", m.group(1))
    lines = []
    # Track inactive %if blocks. A Source/Patch is only "required" when rpm
    # would actually evaluate its branch. Two shapes matter:
    #   %if 0 ... %endif                        -> literal dead block
    #   %if 0%{?runcheck} ... %endif            -> dead unless runcheck is set
    #                                             (openjpeg's data.tar.xz)
    # Crucially `%if 0%{?gitrel}` / `%else` is NOT dead overall: rpm takes the
    # %else branch, which holds the real active Source lines (pulseaudio).
    # Treating that whole construct as dead hid a genuine Source1 from the
    # audit, so branch state is tracked explicitly instead of a single flag.
    def cond_state(cond: str) -> bool:
        """True when this %if condition evaluates true with our macro set."""
        cond = cond.strip()
        if re.fullmatch(r"0+", cond):
            return False
        m = re.fullmatch(r"0*%\{\?(\w+)\}", cond)
        if m:
            return m.group(1) in macros
        return True

    # stack of [this_branch_active, any_branch_taken, parent_active]
    stack: list[list[bool]] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("%if"):
            parent = stack[-1][0] if stack else True
            active = parent and cond_state(s[3:])
            stack.append([active, active, parent])
            continue
        if s.startswith("%else") and stack:
            frame = stack[-1]
            frame[0] = frame[2] and not frame[1]
            frame[1] = frame[1] or frame[0]
            continue
        if s.startswith("%endif") and stack:
            stack.pop()
            continue
        if stack and not stack[-1][0]:
            continue
        m = re.match(r"^(Source\d*|Patch\d*)\s*:\s*(\S+)", s)
        if m:
            lines.append((m.group(1), m.group(2)))
    checks = []
    skipped_first_source = False
    for tag, val in lines:
        if tag.startswith("Source") and not skipped_first_source:
            skipped_first_source = True
            continue
        checks.append((tag, val))
    # %autosetup/%setup -n expectation (only when fully expandable with
    # spec-defined macros; conditional -n values like %{?commitdate:...}
    # for snapshot builds are skipped).
    topdir = None
    m = re.search(r"^%(?:auto)?setup\b[^\n]*-n\s+(\S+)", text, re.M)
    if m:
        expanded = expand(m.group(1), macros)
        if "%{" not in expanded:
            topdir = expanded
    return macros, checks, topdir


def _match_paren(s: str, start: int) -> int:
    """Index just past the ')' matching the '(' at `start`, or -1.

    rpm's %(shell) macros can nest (git's %{rcpath} is
    `%(test "%{version}" = "%{real_version}" || echo testing/)`), so the old
    `[^)]+` match truncated them and produced garbage basenames like
    ')git-2.55.0.tar.sign'. Quote-aware so a ')' inside a string is safe.
    """
    depth = 0
    quote = ""
    i = start
    while i < len(s):
        c = s[i]
        if quote:
            if c == quote:
                quote = ""
            elif c == "\\" and quote == '"':
                i += 1
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def run_shell_macro(body: str, macros: dict) -> str:
    """Expand %macro references inside a %(...) body, then run it in bash."""
    cmd = expand(body, macros)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, timeout=10, executable="/bin/bash")
    except Exception:  # noqa: BLE001
        return f"%({body})"
    if result.returncode != 0 and not result.stdout.strip():
        # Unresolvable (e.g. a nested %( ) we could not expand): keep literal
        # so the caller's basename sanity check skips it rather than emitting
        # a half-expanded path.
        return f"%({body})"
    return result.stdout.strip()


# rpm conditional macro forms: %{?name:alternate}, %{?name},
# %{!?name:alternate}. The audit needs these resolved or basenames come out
# full of '%{' and get skipped (which once hid a real pulseaudio Source1:
# its version is written as %{pa_major}%{?pa_minor:.%{pa_minor}}).
_COND_MACRO = re.compile(r"%\{\??!?\?(\w+)(?::((?:[^{}]|\{[^{}]*\})*))?\}")


def resolve_conditionals(val: str, macros: dict, _depth: int = 0) -> str:
    """Resolve %{?macro:alt} / %{?macro} / %{!?macro:alt} against `macros`.

    Unknown macros are assumed DEFINED, because in a dist-git spec the
    undefined case is the rare one and treating it as defined keeps the
    literal basename available for checking (a wrong guess only ever yields
    a 'missing' we can see, never a silent skip).
    """
    if _depth > 10:
        return val

    def rep(m: "re.Match[str]") -> str:
        name, alt = m.group(1), m.group(2)
        negated = m.group(0).startswith("%{!?")
        defined = name in macros
        if negated:
            return "" if defined else resolve_conditionals(alt or "", macros, _depth + 1)
        if not defined:
            # `%{?name:alt}` with name undefined expands to nothing in rpm.
            # When there is no alternate (`%{?name}`) we may be looking at a
            # macro the spec sets conditionally further down, so keeping a
            # placeholder is safer than silently dropping path text.
            return "%{" + name + "}" if alt is None else ""
        return resolve_conditionals(alt, macros, _depth + 1) if alt is not None else ""

    prev = None
    while prev != val:
        prev = val
        val = _COND_MACRO.sub(rep, val)
    return val


def expand(val: str, macros: dict, _depth: int = 0) -> str:
    if _depth > 10:
        return val

    val = resolve_conditionals(val, macros, _depth)

    def sub(m):
        raw = macros.get(m.group(1))
        if raw is None:
            return m.group(0)
        # A macro's own value may itself contain %(...) (git's %{rcpath} is
        # defined in terms of a nested shell command), so resolve it before
        # splicing it into the caller's text.
        if "%(" in raw and "%(" not in m.group(0):
            return expand(raw, macros, _depth + 1)
        return raw

    # Resolve %(...) innermost-first so nested shell macros expand correctly.
    out = []
    i = 0
    while i < len(val):
        if val.startswith("%(", i):
            end = _match_paren(val, i + 1)
            if end != -1:
                body = val[i + 2:end - 1]
                out.append(run_shell_macro(body, macros))
                i = end
                continue
        out.append(val[i])
        i += 1
    val = "".join(out)

    prev = None
    while prev != val:
        prev = val
        # `resolve_conditionals` inside the loop matters: substituting a macro
        # can INTRODUCE new conditionals (Version is %{pa_major}%{?pa_minor:...},
        # so expanding %{version} yields a fresh %{?pa_minor:.%{pa_minor}}).
        val = resolve_conditionals(val, macros, _depth)
        # Handle both %{macro} and %macro (word boundary after)
        val = re.sub(r"%\{(\w+)\}", sub, val)
        val = re.sub(r"%(\w+)(?![\w{])", lambda m: macros.get(m.group(1), m.group(0)), val)
    # NOTE: the old `for name in macros: val.replace(name, value)` used the
    # bare macro NAME (no % prefix) and corrupted unrelated text; the two
    # regexes above already cover the %name / %{name} forms.
    return val


def fetch(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "kestrel-audit-sources/1"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as f:
            while chunk := resp.read(1024 * 1024):
                f.write(chunk)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"    download failed: {url} ({exc})")
        return False


def distgit_sources(pkg: str) -> dict:
    """Parse the dist-git `sources` hash file: {filename: sha512}."""
    out = {}
    try:
        req = urllib.request.Request(
            DISTGIT.format(pkg=pkg, file="sources"),
            headers={"User-Agent": "kestrel-audit-sources/1"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp.read().decode().splitlines():
                m = re.match(r"SHA512 \((\S+)\) = (\S+)", line)
                if m:
                    out[m.group(1)] = m.group(2)
    except Exception as exc:  # noqa: BLE001
        print(f"    cannot read dist-git sources file for {pkg} ({exc})")
    return out


def try_fetch(pkgdir: Path, stored: str, fetch_name: str, missing: dict) -> None:
    """Attempt dist-git raw, then lookaside-by-basename. Removes `stored`."""
    name = pkgdir.name
    url = DISTGIT.format(pkg=name, file=fetch_name)
    print(f"  fetching {name}/{fetch_name} ...")
    if fetch(url, pkgdir / fetch_name):
        missing[name].remove(stored)
        return
    hashes = distgit_sources(name)
    if fetch_name in hashes:
        lurl = LOOKASIDE.format(pkg=name, file=fetch_name, hx=hashes[fetch_name])
        print(f"  fetching lookaside {name}/{fetch_name} ...")
        if fetch(lurl, pkgdir / fetch_name):
            missing[name].remove(stored)
            return
    print(f"    STILL MISSING: {name}/{stored}")


def staged_names() -> dict:
    """Basename of each entry's rendered URL (what fetch --stage-into stages)."""
    import json

    out = {}
    try:
        data = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())
        for pkg, e in data["packages"].items():
            if e.get("local") or not e.get("url_template"):
                continue
            url = e["url_template"].replace("{version}", str(e.get("version", "")))
            out[pkg] = url.rsplit("/", 1)[-1]
    except Exception:  # noqa: BLE001
        pass
    return out


def declared_extras() -> dict:
    """Declared secondary inputs per package (what fetch stages alongside
    the primary so large binaries never need committing to git)."""
    import json

    out: dict[str, set[str]] = {}
    try:
        data = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())
        for pkg, e in data["packages"].items():
            names = {x.get("filename", "") for x in e.get("extra_sources", []) or []}
            if names - {""}:
                out[pkg] = names - {""}
    except Exception:  # noqa: BLE001
        pass
    return out


def srpm_methods() -> dict:
    """SRPM approach per package: `standard` (default) or `rpmbuild`.

    The rpmbuild approach (plain `rpmbuild -bs` over committed Sources,
    for specs no SRPM parser can handle, e.g. grub2) has no download step
    for secondary sources, so its remote sources must be vendored into
    the recipe dir.
    """
    import json

    out = {}
    try:
        data = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())
        for pkg, e in data["packages"].items():
            if e.get("local") or e.get("srpm") == "rpmbuild":
                out[pkg] = "rpmbuild"
            else:
                out[pkg] = "standard"
    except Exception:  # noqa: BLE001
        pass
    return out


def audit(fix: bool = False, only: str | None = None) -> int:
    missing, warnings = {}, []
    staged = staged_names()
    extras = declared_extras()
    methods = srpm_methods()
    dirs = [PKGS / only] if only else sorted(PKGS.iterdir())
    for pkgdir in dirs:
        if not pkgdir.is_dir():
            print(f"no recipe dir: {pkgdir}")
            return 2
        specs = list(pkgdir.glob("*.spec"))
        if not specs:
            continue
        macros, checks, topdir = parse_spec(specs[0])
        for tag, raw in checks:
            val = expand(raw, macros)
            # Our staged verified archive satisfies any reference to it,
            # whatever SourceN position the spec uses (e.g. libinput's
            # snapshot-conditional double Source0). Declared secondary
            # inputs (extra_sources) are staged by the same fetch step.
            if val.rsplit("/", 1)[-1] == staged.get(pkgdir.name):
                continue
            if val.rsplit("/", 1)[-1] in extras.get(pkgdir.name, ()):
                continue
            if "vendor.tar" in val:
                if (pkgdir / val.rsplit("/", 1)[-1]).is_file():
                    continue
                if any(
                    name.endswith("vendor.tar.bz2")
                    and (pkgdir / name).is_file()
                    for name in extras.get(pkgdir.name, ())
                ):
                    continue
                warnings.append(
                    f"{pkgdir.name}: {tag} needs go-vendor-tools generation ({raw})"
                )
                continue
            if "://" in val:
                # A committed file satisfying a remote URL (e.g. .sig fetched
                # from lookaside) needs no network; rpmbuild uses the local copy.
                if (pkgdir / val.rsplit("/", 1)[-1]).is_file():
                    continue
                # rpmbuild-approach packages get no downloader for secondary
                # sources, so a remote source is a hard miss: fetch the URL itself.
                if methods.get(pkgdir.name) == "rpmbuild":
                    base = val.rsplit("/", 1)[-1].split("#", 1)[0]
                    missing.setdefault(pkgdir.name, []).append(f"{tag} -> {base}")
                    if fix:
                        print(f"  fetching {pkgdir.name}/{base} ...")
                        if fetch(val.split("#", 1)[0], pkgdir / base):
                            missing[pkgdir.name].remove(f"{tag} -> {base}")
                            continue
                        print(f"    STILL MISSING: {pkgdir.name}/{base}")
                    continue
                # For rpmbuild packages, also fetch signature/key files (.sig, .asc, .gpg)
                # since specs use %{gpgverify} which needs them present.
                if methods.get(pkgdir.name) == "rpmbuild":
                    base = val.rsplit("/", 1)[-1].split("#", 1)[0]
                    if base.endswith((".sig", ".asc", ".gpg")):
                        missing.setdefault(pkgdir.name, []).append(f"{tag} -> {base}")
                        if fix:
                            print(f"  fetching {pkgdir.name}/{base} ...")
                            if fetch(val.split("#", 1)[0], pkgdir / base):
                                missing[pkgdir.name].remove(f"{tag} -> {base}")
                                continue
                            print(f"    STILL MISSING: {pkgdir.name}/{base}")
                        continue
                # rpm URL#file fragments (openpgpkey keys): stage the file
                # so rpmbuild finds it without network.
                if "#/" in val:
                    base_url, frag = val.split("#", 1)
                    fname = frag.rsplit("/", 1)[-1]
                    if (pkgdir / fname).is_file():
                        continue
                    missing.setdefault(pkgdir.name, []).append(f"{tag} -> {fname}")
                    if fix:
                        print(f"  fetching {pkgdir.name}/{fname} ...")
                        if fetch(base_url, pkgdir / fname):
                            missing[pkgdir.name].remove(f"{tag} -> {fname}")
                            continue
                        print(f"    STILL MISSING: {pkgdir.name}/{fname}")
                    continue
                warnings.append(f"{pkgdir.name}: {tag} is remote ({val})")
                continue
            if "%{" in val:
                # Unresolvable macro (forge/git0/url, vendor names): try the
                # basename against dist-git raw + lookaside (.sig files live
                # in lookaside); generated trees (vendor tarballs) 404 both.
                base = val.rsplit("/", 1)[-1]
                if (pkgdir / base).is_file():
                    continue
                missing.setdefault(pkgdir.name, []).append(val)
                if fix:
                    try_fetch(pkgdir, val, base, missing)
                continue
            if (pkgdir / val).is_file():
                continue
            missing.setdefault(pkgdir.name, []).append(val)
            if fix:
                try_fetch(pkgdir, val, val, missing)
        # top-dir check against a staged archive, when present.
        # Declared secondary inputs (extra_sources) unpack elsewhere
        # (e.g. meson subprojects), so only the primary is compared.
        extra_names = extras.get(pkgdir.name, ())
        if topdir:
            for arc in pkgdir.glob("*.tar.*"):
                if arc.name.endswith((".sig", ".asc")):
                    continue
                if arc.name in extra_names:
                    continue
                try:
                    with tarfile.open(arc) as tf:
                        first = tf.getnames()[0].split("/")[0]
                    if first != topdir:
                        warnings.append(
                            f"{pkgdir.name}: {arc.name} extracts to {first!r}, "
                            f"spec expects {topdir!r}"
                        )
                except Exception:  # noqa: BLE001
                    pass
    for w in sorted(warnings):
        print(f"WARN: {w}")
    still = {k: v for k, v in missing.items() if v}
    if still:
        print("MISSING:")
        for k in sorted(still):
            for f in still[k]:
                print(f"  {k}: {f}")
        return 1
    print(f"source audit OK ({sum(1 for _ in PKGS.iterdir() if _.is_dir())} recipe dirs)")
    return 0


def committed_names(pkgdir: Path) -> set[str]:
    """Filenames in a recipe dir that are tracked by git.

    CI starts from a fresh checkout, so a gitignored artifact present on a
    developer's disk (pulseaudio-17.0.tar.xz.sha256sum matches
    `rpm-factory/packages/*/*.tar.*`) does NOT exist at build time. Only committed
    files may satisfy a SourceN reference.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "--", str(pkgdir)],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        return {Path(line).name for line in out.stdout.splitlines() if line.strip()}
    except Exception:  # noqa: BLE001
        # No git (e.g. an exported tarball): fall back to on-disk presence so
        # the gate still works outside a checkout.
        return {p.name for p in pkgdir.iterdir()}


def spec_sources(fix: bool = False, only: str | None = None) -> int:
    """Static pre-rpmbuild gate: every active SourceN/PatchN basename must be
    satisfiable from something we stage or commit.

    rpmbuild -bs hard-fails with `Bad file: .../SOURCES/<name>: No such file`
    for ANY declared Source/Patch whose basename is absent — even one the spec
    never references. Fedora dist-git makes this easy to hit: pulseaudio
    declares `Source1: .../pulseaudio-%{version}.tar.xz.sha256sum` but never
    uses %SOURCE1. Staging can never satisfy a file nothing downloads, so the
    fix is always to drop the dead declaration (or lock it as an extra_source).

    Satisfied when the basename is:
      - the staged verified primary archive (source_pipeline --stage-into), or
      - a declared extra_sources filename (staged by the same fetch), or
      - a file committed in the recipe dir (patches, .sig, sysusers units), or
      - a locally generated source (local: true).
    """
    import json

    data = json.loads((ROOT / "rpm-factory" / "config" / "upstream-sources.json").read_text())
    staged = staged_names()
    extras = declared_extras()
    dirs = [PKGS / only] if only else sorted(PKGS.iterdir())
    missing: dict[str, list[str]] = {}
    for pkgdir in dirs:
        if not pkgdir.is_dir():
            print(f"no recipe dir: {pkgdir}")
            return 2
        specs = list(pkgdir.glob("*.spec"))
        if not specs:
            continue
        entry = data["packages"].get(pkgdir.name, {})
        if entry.get("local"):
            continue
        macros, checks, _topdir = parse_spec(specs[0])
        ok_names = set(extras.get(pkgdir.name, ()))
        if staged.get(pkgdir.name):
            ok_names.add(staged[pkgdir.name])
        committed = committed_names(pkgdir)
        for tag, raw in checks:
            val = expand(raw, macros).strip()
            # rpm only honors '#' as a comment at the START of a line, so a
            # '#' inside a tag value is part of the filename (cdparanoia's
            # `Patch0: cdparanoia-10.2-#463009.patch` is a real file on disk).
            # The one exception is the explicit URL-fragment form `URL#/name`.
            if "#/" in val:
                base = val.split("#/")[-1]
            else:
                base = val.rsplit("/", 1)[-1]
            if not base or "%{" in base or base.startswith("%"):
                continue
            # NOTE: committed-only, not `is_file()` — a gitignored blob on a
            # dev machine (pulseaudio-17.0.tar.xz.sha256sum) is absent in CI
            # and was masking a real "Bad file" SRPM failure.
            if base in ok_names or base in committed:
                continue
            if (pkgdir / base).is_file() and base not in committed:
                missing.setdefault(pkgdir.name, []).append(
                    f"{tag} -> {base} (present but NOT committed — missing in CI)")
                continue
            missing.setdefault(pkgdir.name, []).append(f"{tag} -> {base}")
    if missing:
        print("UNSATISFIABLE SPEC SOURCES (rpmbuild -bs will fail with 'Bad file'):")
        for pkg in sorted(missing):
            for ref in missing[pkg]:
                print(f"  {pkg}: {ref}")
        print(
            "\nFix: drop the unused SourceN/PatchN line from the spec, or add the\n"
            "file to that package's extra_sources in upstream-sources.json."
        )
        return 1
    print(f"spec source audit OK ({len(dirs)} recipe dirs)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit (and fetch) spec-referenced files")
    ap.add_argument("--fix", action="store_true", help="fetch missing files into recipe dirs")
    ap.add_argument("--package", "-p", default=None, help="scope to one recipe dir (for CI matrix)")
    ap.add_argument("--spec-sources", action="store_true",
                    help="static pre-rpmbuild check: every SourceN/PatchN is satisfiable")
    args = ap.parse_args(argv)
    if args.spec_sources:
        return spec_sources(only=args.package)
    return audit(fix=args.fix, only=args.package)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
