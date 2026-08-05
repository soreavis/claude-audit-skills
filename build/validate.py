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

    if not AH_HEADING.search(text):
        err(f"{rel}: missing an anti-hallucination rules heading (grounding guardrail is mandatory)")
    if not EVIDENCE.search(text):
        err(f"{rel}: no evidence-grounding language (expected 'file:line', 'Grep', or 'never invent')")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skills validated — manifests, YAML frontmatter, anti-hallucination guardrail")
