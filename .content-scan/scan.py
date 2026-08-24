#!/usr/bin/env python3
"""Repository content scan.

Implements content-scan-spec.md: a pull-request gate that keeps identifying
information out of the template library.

Findings print as `file:line:tier:rule:matched-text`, matched text truncated to
40 characters and emails, phones, and keys masked. Exit code 1 if any BLOCK
finding survives the allowlists; WARN findings never fail the build.

Usage:
    python3 .content-scan/scan.py [paths...]      # default: whole working tree
    python3 .content-scan/scan.py --warn-only     # never exit non-zero
    python3 .content-scan/scan.py --hash-denylist known-names.txt
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF_DIR = ROOT / ".content-scan"

BLOCK, WARN = "BLOCK", "WARN"


# --------------------------------------------------------------------------
# Minimal YAML reader
#
# The scan is a CI gate and must run on a bare python:3 image without a pip
# install step. config.yml only ever holds scalars, lists, and one level of
# nesting, so a full parser would be more dependency than the file deserves.
# --------------------------------------------------------------------------
def load_config(path: Path) -> dict:
    """Parse the subset of YAML config.yml uses: scalars, lists, and one level
    of nested mappings. Enough for a CI gate that must run without a pip step."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    # The owner of the most recent valueless key, in case it turns out to be a
    # list rather than a nested mapping.
    pending: tuple[dict, str] | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = raw.split("  #", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith("- "):
            if pending is None:
                continue
            owner, key = pending
            if not isinstance(owner.get(key), list):
                owner[key] = []
            owner[key].append(_unquote(stripped[2:].strip()))
            continue

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip()
        if value:
            container[key] = _scalar(value)
            pending = None
        else:
            child: dict = {}
            container[key] = child
            pending = (container, key)
            stack.append((indent, child))
    return _prune(root)


def _prune(node):
    """A key that turned out to hold a list left an empty child dict behind."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            v = _prune(v)
            if v == {}:
                continue
            out[k] = v
        return out
    return node


def _unquote(v: str) -> str:
    return v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'" else v


def _scalar(v: str):
    v = _unquote(v)
    return {"true": True, "false": False}.get(v.lower(), v)



# --------------------------------------------------------------------------
# Denylists (spec §1.4a, §1.5)
#
# Real names and the real organization are never committed in plaintext — the
# file would itself be the disclosure the check exists to prevent. Terms are
# stored as salted SHA-256 of the lowercased term; the salt is a CI secret.
# A plaintext file is used when present, for local runs, and is gitignored.
# --------------------------------------------------------------------------
SALT = os.environ.get("CONTENT_SCAN_SALT", "")

# A hashed denylist loads whether or not the salt is right, and a wrong salt
# matches nothing — the rules go inert with no symptom. The canary is a fixed
# term whose hash is committed in config.yml: if it does not reproduce, the
# salt in this environment is not the one the denylists were built with.
CANARY_TERM = "content-scan-canary"


def digest(term: str) -> str:
    return hashlib.sha256((SALT + term.strip().lower()).encode("utf-8")).hexdigest()


@dataclass
class Denylist:
    plain: set[str]
    hashes: set[str]

    def hit(self, candidate: str) -> bool:
        c = candidate.strip().lower()
        if c in self.plain:
            return True
        return bool(self.hashes) and digest(c) in self.hashes

    def __bool__(self) -> bool:
        return bool(self.plain or self.hashes)


def load_denylist(stem: str) -> Denylist:
    def lines(name: str) -> list[str]:
        p = CONF_DIR / name
        if not p.exists():
            return []
        return [
            ln.strip()
            for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]

    return Denylist(
        plain={t.lower() for t in lines(f"{stem}.txt")},
        hashes=set(lines(f"{stem}.hashes")),
    )


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_OK = [
    re.compile(r"\[[A-Z][A-Z ]+\]@"),
    re.compile(r"@example\.(com|org|net)\b", re.I),
    re.compile(r"@(\S*\.)?(invalid|test|localhost)\b", re.I),
]

PHONE = [
    re.compile(r"(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}"),
    re.compile(r"\+\d{1,3}[-. ]\d{2,4}[-. ]\d{3,4}[-. ]\d{3,4}"),
]
# The reserved range is 555-0100 through 555-0199 only. 414-555-5555 looks
# reserved and is not.
PHONE_OK = [re.compile(r"\d{3}[-. ]555[-. ]01\d{2}"), re.compile(r"\[CONTACT PHONE\]")]

TENANCY = re.compile(
    r"https?://(?:"
    r"docs\.google\.com/\S+"
    r"|drive\.google\.com/\S+"
    r"|\S*\.sharepoint\.com/\S+"
    r"|\S*\.atlassian\.net/\S+"
    r"|\S*\.slack\.com/(?:archives|files)/\S+"
    r"|\S*\.notion\.(?:so|site)/\S+"
    r"|\S*\.box\.com/\S+"
    r"|\S*\.dropbox\.com/s/\S+"
    r"|\S*\.zoom\.us/(?:rec|j)/\S+"
    r")"
)

SECRETS = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("api-secret", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("chat-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("us-ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

ORG_SUFFIX = re.compile(r"\b(Corp|Inc|LLC|Ltd|GmbH|PLC)\b\.?")

ARTIFACTS = ["gd2md-html alert", "Output copied to clipboard", "Docs to Markdown version"]

# §1.4b — a person-shaped value in an identity-bearing table column.
NAME_COLUMNS = ("name", "owner", "approver", "contact", "reviewer")
CELL_NAME = re.compile(r"^([A-Z][a-z]+ [A-Z][A-Za-z'’-]+)$")
SEPARATOR_ROW = re.compile(r"^\|?[\s:|-]*-[\s:|-]*\|?$")

PLACEHOLDER = re.compile(r"\[([A-Z][A-Z0-9 _/-]{2,})\]")
MALFORMED_PLACEHOLDER = re.compile(r"\[[A-Z][A-Z ]{2,}(?!\])[^\]\n]{0,40}$")

SUPPRESS = re.compile(r"<!--\s*scan-ok:\s*\S.*?-->")
FILENAME_OK = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")

# Candidate n-grams tested against the hashed denylists.
TOKEN = re.compile(r"[A-Za-z][A-Za-z'’.-]*")


def relpath(p: Path) -> str:
    """Path relative to the repo root, tolerant of symlinked roots such as
    macOS /tmp, where Path.relative_to would raise."""
    return Path(os.path.relpath(p.resolve(), ROOT)).as_posix()


def mask(text: str) -> str:
    """Never print the thing we just found in full. A CI log is not private."""
    text = text.strip()
    if len(text) <= 4:
        return "*" * len(text)
    return text[:2] + "*" * (len(text) - 4) + text[-2:]


def truncate(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= 40 else text[:37] + "..."


@dataclass
class Finding:
    path: str
    line: int
    tier: str
    rule: str
    match: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.tier}:{self.rule}:{self.match}"


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------
class Scanner:
    def __init__(self, conf: dict):
        self.conf = conf
        self.names = load_denylist("known-names")
        self.orgs = load_denylist("known-orgs")
        self.vendors = [
            v.strip()
            for v in (CONF_DIR / "vendors.txt").read_text(encoding="utf-8").splitlines()
            if v.strip() and not v.startswith("#")
        ]
        self.allow_terms = [t.lower() for t in conf.get("allow_terms", [])]
        self.vendor_enabled = bool(
            conf.get("rules", {}).get("vendor_in_mandate", {}).get("enabled", False)
        )
        self.mandate = re.compile(
            r"\b(MUST NOT|MUST|SHALL NOT|SHALL|REQUIRED|Required for)\b"
        )
        self.findings: list[Finding] = []
        self.placeholders_seen: set[str] = set()

    def emit(self, path, line, tier, rule, match):
        self.findings.append(Finding(path, line, tier, rule, truncate(match)))

    # -- per-line rules -------------------------------------------------
    def scan_line(self, rel: str, n: int, line: str, suppressed: bool):
        # Placeholders are harvested even from suppressed lines: a suppression
        # says "this match is legitimate", not "ignore this line entirely".
        if not self._meta_file:
            self.placeholders_seen.update(m.group(1) for m in PLACEHOLDER.finditer(line))

        # A document that quotes the scan's own patterns — the specification
        # itself — matches them by construction. That is what the reasoned
        # suppression comment is for. It is not a way to pass a real finding:
        # an identity leak in a template is fixed, not annotated.
        if suppressed:
            return

        for m in EMAIL.finditer(line):
            if not any(ok.search(m.group()) for ok in EMAIL_OK):
                self.emit(rel, n, BLOCK, "email", mask(m.group()))

        for pat in PHONE:
            for m in pat.finditer(line):
                if not any(ok.search(m.group()) for ok in PHONE_OK):
                    self.emit(rel, n, BLOCK, "phone", mask(m.group()))
                    break

        for m in TENANCY.finditer(line):
            self.emit(rel, n, BLOCK, "tenancy-url", truncate(m.group()))

        for rule, pat in SECRETS:
            for m in pat.finditer(line):
                self.emit(rel, n, BLOCK, rule, mask(m.group()))

        for artifact in ARTIFACTS:
            if artifact.lower() in line.lower():
                self.emit(rel, n, BLOCK, "conversion-artifact", artifact)

        self.scan_denylists(rel, n, line)

        if MALFORMED_PLACEHOLDER.search(line):
            self.emit(rel, n, BLOCK, "malformed-placeholder", line)

        if self.allowed(line):
            return

        if ORG_SUFFIX.search(line):
            self.emit(rel, n, WARN, "org-suffix", ORG_SUFFIX.search(line).group())

        self.scan_table_name(rel, n, line)

        if self.vendor_enabled and not self.path_exempt(rel):
            self.scan_vendor_mandate(rel, n, line)

    def allowed(self, line: str) -> bool:
        low = line.lower()
        return any(term in low for term in self.allow_terms)

    def path_exempt(self, rel: str) -> bool:
        return rel in self.conf.get("vendor_check_exempt", [])

    def scan_denylists(self, rel: str, n: int, line: str):
        """Hashed denylists need candidates, not a regex. Test every 1-3 word
        run of word tokens against both lists."""
        if not (self.names or self.orgs):
            return
        tokens = [m.group() for m in TOKEN.finditer(line)]
        i = 0
        while i < len(tokens):
            # Longest match first, so a two-word organization is not reported as
            # two separate one-word hits.
            for size in (3, 2, 1):
                if i + size > len(tokens):
                    continue
                phrase = " ".join(tokens[i : i + size])
                cleaned = phrase.rstrip(".,;:").replace("’", "'")
                variants = {cleaned, re.sub(r"'s$", "", cleaned)}
                rule = None
                if any(self.names.hit(v) for v in variants):
                    rule = "known-name"
                elif any(self.orgs.hit(v) for v in variants):
                    rule = "known-org"
                if rule:
                    self.emit(rel, n, BLOCK, rule, mask(phrase))
                    i += size
                    break
            else:
                i += 1
                continue
            if rule is None:
                i += 1

    def scan_table_name(self, rel: str, n: int, line: str):
        if not self._name_columns or "|" not in line:
            return
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for idx in self._name_columns:
            if idx >= len(cells):
                continue
            value = cells[idx]
            if value.startswith("[") or set(value) <= set("-: "):
                continue
            if CELL_NAME.match(value):
                self.emit(rel, n, WARN, "table-person-name", value)

    def scan_vendor_mandate(self, rel: str, n: int, line: str):
        if not self.mandate.search(line):
            return
        for vendor in self.vendors:
            for m in re.finditer(rf"\b{re.escape(vendor)}\b", line):
                window = line[max(0, m.start() - 120) : m.end() + 120]
                if self.mandate.search(window):
                    self.emit(rel, n, WARN, "vendor-in-mandate", vendor)
                    return

    # -- per-file rules -------------------------------------------------
    def scan_file(self, path: Path):
        rel = relpath(path)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return
        lines = text.splitlines()

        suppress_next = False
        self._name_columns: list[int] = []
        self._meta_file = rel in self.conf.get("structure_exempt", [])
        for n, line in enumerate(lines, 1):
            suppressed = suppress_next or bool(SUPPRESS.search(line))
            suppress_next = bool(SUPPRESS.search(line))
            self._track_name_columns(line, lines[n] if n < len(lines) else "")
            self.scan_line(rel, n, line, suppressed)

        if rel in self.conf.get("structure_exempt", []):
            return
        self.scan_structure(rel, path, lines, text)

    def _track_name_columns(self, line: str, next_line: str):
        """A markdown table header tells us which columns carry identities. It
        is a header only if a separator row sits beneath it."""
        if "|" not in line:
            if not line.strip():
                self._name_columns = []
            return
        if not SEPARATOR_ROW.match(next_line.strip()):
            return
        cells = [c.strip().lower().strip("*") for c in line.strip().strip("|").split("|")]
        self._name_columns = [i for i, c in enumerate(cells) if c in NAME_COLUMNS]

    def scan_structure(self, rel: str, path: Path, lines: list[str], text: str):
        if not FILENAME_OK.match(path.name):
            self.emit(rel, 1, BLOCK, "filename-convention", path.name)

        if not lines or lines[0].strip() != "---":
            self.emit(rel, 1, BLOCK, "frontmatter-missing", "no opening --- block")
            body = text
        else:
            end = next((i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---"), None)
            if end is None:
                self.emit(rel, 1, BLOCK, "frontmatter-unterminated", "no closing ---")
                body = text
            else:
                keys = {
                    ln.split(":", 1)[0].strip()
                    for ln in lines[1:end]
                    if ":" in ln and not ln.startswith((" ", "\t", "-"))
                }
                for required in self.conf.get("frontmatter_required", []):
                    if required not in keys:
                        self.emit(rel, 1, BLOCK, "frontmatter-key", required)
                body = "\n".join(lines[end + 1 :])

        if len(body.strip().encode("utf-8")) < 200:
            self.emit(rel, 1, WARN, "empty-document", f"{len(body.strip())} bytes of body")

        for n, line in enumerate(lines, 1):
            for m in re.finditer(r"\]\((?!https?:|#|mailto:)([^)#]+\.md)(?:#[^)]*)?\)", line):
                target = (path.parent / m.group(1)).resolve()
                if not target.exists():
                    self.emit(rel, n, WARN, "broken-link", m.group(1))


def readme_index_check(scanner: Scanner, files: list[Path]):
    """§2.5 — README index matches disk, and every placeholder is documented."""
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8")

    listed = {
        # str.lstrip("./") strips a character set, not a prefix, and would eat
        # the leading dot of a path like .content-scan/README.md.
        m.group(1)[2:] if m.group(1).startswith("./") else m.group(1)
        for m in re.finditer(r"\]\((?!https?:)([^)#]+\.md)\)", text)
    }
    on_disk = {relpath(p) for p in files if p.name != "README.md"}
    for missing in sorted(on_disk - listed):
        scanner.emit("README.md", 1, WARN, "readme-index-missing", missing)
    # Stale means the link points at nothing. A link to a real file that the
    # scan does not cover — .content-scan/README.md — is not stale.
    for stale in sorted(l for l in listed - on_disk if not (ROOT / l).exists()):
        scanner.emit("README.md", 1, WARN, "readme-index-stale", stale)

    documented = {m.group(1) for m in PLACEHOLDER.finditer(text)}
    for undocumented in sorted(scanner.placeholders_seen - documented):
        scanner.emit("README.md", 1, WARN, "placeholder-undocumented", f"[{undocumented}]")


def collect(conf: dict, targets: list[str]) -> list[Path]:
    excludes = conf.get("exclude", [])
    roots = [Path(t) for t in targets] if targets else [ROOT]
    out: list[Path] = []
    for r in roots:
        r = r if r.is_absolute() else (ROOT / r)
        candidates = sorted(r.rglob("*.md")) if r.is_dir() else [r]
        for p in candidates:
            rel = relpath(p)
            if any(fnmatch.fnmatch(rel, pat) for pat in excludes):
                continue
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Repository content scan")
    ap.add_argument("paths", nargs="*", help="files or directories (default: repo root)")
    ap.add_argument("--warn-only", action="store_true", help="never exit non-zero")
    ap.add_argument("--require-denylist", action="store_true",
                    help="fail if no name/org denylist loaded (use in CI)")
    ap.add_argument("--print-canary", action="store_true",
                    help="print the salt canary hash for config.yml")
    ap.add_argument("--hash-denylist", metavar="FILE",
                    help="print salted hashes for a plaintext denylist and exit")
    args = ap.parse_args()

    if args.print_canary:
        if not SALT:
            print("CONTENT_SCAN_SALT is not set.", file=sys.stderr)
            return 2
        print(digest(CANARY_TERM))
        return 0

    if args.hash_denylist:
        if not SALT:
            print("CONTENT_SCAN_SALT is not set; hashes would be unsalted.", file=sys.stderr)
            return 2
        src = Path(args.hash_denylist)
        src = src if src.is_absolute() else CONF_DIR / src
        for ln in src.read_text(encoding="utf-8").splitlines():
            if ln.strip() and not ln.startswith("#"):
                print(digest(ln))
        return 0

    conf = load_config(CONF_DIR / "config.yml")
    scanner = Scanner(conf)
    files = collect(conf, args.paths)
    for f in files:
        scanner.scan_file(f)
    if not args.paths:
        readme_index_check(scanner, files)

    blocks = [f for f in scanner.findings if f.tier == BLOCK]
    warns = [f for f in scanner.findings if f.tier == WARN]

    for f in blocks + warns:
        print(f)

    print(
        f"\nScanned {len(files)} file(s): {len(blocks)} BLOCK, {len(warns)} WARN.",
        file=sys.stderr,
    )
    if args.require_denylist:
        expected = conf.get("salt_canary")
        if not expected:
            print("error: config.yml has no salt_canary; cannot verify the salt.",
                  file=sys.stderr)
            return 2
        if digest(CANARY_TERM) != expected:
            print(
                "error: CONTENT_SCAN_SALT is unset or wrong — the hashed name and "
                "organization denylists would match nothing. Rules 1.4a and 1.5 are "
                "inert until it is corrected.",
                file=sys.stderr,
            )
            return 2

    if not (scanner.names or scanner.orgs):
        note = (
            "no denylist loaded — set CONTENT_SCAN_SALT and provide "
            ".content-scan/known-names.hashes to enable rules 1.4a and 1.5."
        )
        if args.require_denylist:
            print(f"error: {note}", file=sys.stderr)
            return 2
        print(f"note: {note}", file=sys.stderr)

    return 1 if blocks and not args.warn_only else 0


if __name__ == "__main__":
    sys.exit(main())
