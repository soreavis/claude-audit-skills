#!/usr/bin/env python3
"""Validate the audit plugin marketplace.

Checks, in order:
  1. marketplace.json and every plugin.json parse as JSON.
  2. Each marketplace plugin `source` resolves to a real directory.
  3. Each skill has a SKILL.md whose frontmatter parses as YAML (not a regex
     approximation of it) and sets a non-empty name + description.
  4. Anti-hallucination guardrail: every SKILL.md carries an anti-hallucination
     rules heading AND evidence-grounding language. This is the gate that keeps
     the repo's core promise — every audit finding must trace to real evidence —
     from silently drifting as skills are added.

Run locally before a PR (`python3 build/validate.py`); CI runs the same file.
"""
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.S)
AH_HEADING = re.compile(r"^#{1,6}\s+anti[- ]?hallucination", re.I | re.M)
EVIDENCE = re.compile(r"file:line|Grep|never invent", re.I)

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        err(f"{path.relative_to(ROOT)}: invalid JSON — {e}")
        return None


marketplace = load_json(MARKETPLACE)
if marketplace is None:
    print("VALIDATION FAILED:\n  - " + "\n  - ".join(errors))
    sys.exit(1)

skill_dirs: list[Path] = []
for plugin in marketplace.get("plugins", []):
    name = plugin.get("name", "<unnamed>")
    source = (ROOT / plugin.get("source", "")).resolve()
    if not source.is_dir():
        err(f"plugin '{name}': source {plugin.get('source')!r} is not a directory")
        continue
    if load_json(source / ".claude-plugin" / "plugin.json") is None:
        continue
    skills_root = source / "skills"
    skill_dirs += sorted(d for d in skills_root.iterdir() if d.is_dir()) if skills_root.is_dir() else []

if not skill_dirs:
    err("no skill directories found under any plugin")

for d in skill_dirs:
    skill = d / "SKILL.md"
    rel = skill.relative_to(ROOT)
    if not skill.is_file():
        err(f"{d.name}: missing SKILL.md")
        continue
    text = skill.read_text()

    match = FRONTMATTER.match(text)
    if not match:
        err(f"{rel}: no YAML frontmatter block at the top of the file")
        continue
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        err(f"{rel}: frontmatter does not parse as YAML — {e}")
        meta = None
    if not isinstance(meta, dict) or not meta.get("name") or not meta.get("description"):
        err(f"{rel}: frontmatter must set a non-empty 'name' and 'description'")
    else:
        # The Agent Skills spec requires name == parent folder. Claude Code is
        # lenient about it, so a mismatch works locally and the skill is simply
        # DROPPED, with no error, by conformant loaders — the failure is silent
        # in exactly the runtimes you cannot test from here.
        if meta["name"] != d.name:
            err(f"{rel}: name {meta['name']!r} must equal its folder {d.name!r} "
                f"(spec requirement; mismatches are silently dropped by other runtimes)")
        if len(meta["description"]) > 1024:
            err(f"{rel}: description is {len(meta['description'])} chars, over the 1024 spec cap "
                f"(over-cap skills are dropped without warning)")
        if any(c in f"{meta['name']}{meta['description']}" for c in "<>"):
            err(f"{rel}: angle brackets in name/description can inject into the system prompt")

    if not AH_HEADING.search(text):
        err(f"{rel}: missing an anti-hallucination rules heading (grounding guardrail is mandatory)")
    if not EVIDENCE.search(text):
        err(f"{rel}: no evidence-grounding language (expected 'file:line', 'Grep', or 'never invent')")

# --- private data ---------------------------------------------------------
#
# A wrong manifest gets fixed in the next commit. A machine path, a client name
# or a personal address is scraped the moment it lands on a public repo, and
# removing it costs a history rewrite that every clone and fork has to follow.
#
# Two shapes are worth naming, because both shipped in sibling repos of this one:
#
#   - Home directories arrive DASH-MANGLED from tooling that flattens paths
#     (`-Users-<name>-<project>`), so a guard looking only for a leading
#     `/Users/` never sees them.
#   - Client and employer names leak through COMMIT MESSAGES far more often than
#     through files, because messages get far less review than diffs do.
#
# Identifiers are matched by SHA-256, never in plaintext. A denylist written in
# the clear publishes, inside the guard, the exact strings the guard exists to
# keep out — which is how one sibling repo leaked a private address, inside the
# very check meant to catch it.

import hashlib
import subprocess

BANNED = {
    "95aae01e3ad9faaf0679cff78c8948fd",
    "d85074cb992106e8f9d3fcee509c8faf",
    "29ac921146e53202b38bc6145b0431e4",
    "55f7c00f1c064164f28a53a7803f1bc8",
}

MACHINE_PATHS = [
    (re.compile(r"/private/tmp/claude-[0-9]+/"), "agent sandbox path"),
    (re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+/"), "macOS home directory"),
    (re.compile(r"(?<![\w-])-Users-[A-Za-z0-9._-]+-"), "dash-mangled macOS home directory"),
]
FREE_MAIL = re.compile(
    r"[a-zA-Z0-9._%+-]+@(gmail|googlemail|yahoo|hotmail|outlook|live|icloud|proton|"
    r"protonmail|gmx|seznam|aol)\.[a-z.]{2,}", re.I)
SECRETS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s:@]+@"), "credentialed connection string"),
    (re.compile(r"(?i)authorization\s*:\s*(bearer|basic)\s+[A-Za-z0-9._~+/=-]{16,}"),
     "auth header with credential"),
    (re.compile(r"""(?i)\b(api[_-]?key|secret|token|password|credential)s?\b\W{0,3}[:=]\s*"""
                r"""["'][A-Za-z0-9/+_.-]{16,}["']"""), "assigned credential literal"),
]


def _scan(where, text):
    for i, line in enumerate(text.splitlines(), 1):
        at = f"{where}:{i}"
        # Check the whole token AND its dot/dash-separated parts: a client name
        # usually arrives inside a hostname or a path segment rather than alone,
        # so hashing only the full token misses the very shape that leaked.
        # (Deliberately no example here — naming one would put the identifier
        # back in the clear, which is the mistake this whole block exists to
        # prevent. It happened once already, in this comment.)
        for tok in re.findall(r"[A-Za-z0-9._-]{4,}", line):
            for part in {tok, *re.split(r"[.\-_]", tok)}:
                if len(part) >= 4 and hashlib.sha256(part.lower().encode()).hexdigest()[:32] in BANNED:
                    err(f"{at}: operator/client identifier — use a placeholder")
        for rx, what in MACHINE_PATHS:
            if rx.search(line):
                err(f"{at}: {what} — use a placeholder")
        m = FREE_MAIL.search(line)
        if m:
            err(f"{at}: personal email {m.group(0)}")
        for rx, what in SECRETS:
            if rx.search(line):
                err(f"{at}: {what} — never commit a credential")


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


for rel in _git("ls-files").split("\n"):
    # validate.py holds every pattern by definition; scanning it fails on itself.
    if not rel or rel.endswith("validate.py"):
        continue
    if not rel.endswith((".md", ".py", ".json", ".yml", ".yaml", ".sh", ".txt")):
        continue
    f = ROOT / rel
    if f.is_file():
        _scan(rel, f.read_text(errors="ignore"))

# Commit messages — the shape that actually leaked in sibling repos.
for entry in _git("log", "--all", "--format=%H%x00%B%x00").split("\0\0"):
    parts = entry.split("\0")
    if len(parts) >= 2 and parts[0].strip():
        _scan(f"commit {parts[0].strip()[:9]}", parts[1])

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skills validated — manifests, spec limits, frontmatter, anti-hallucination guardrail, private data")
