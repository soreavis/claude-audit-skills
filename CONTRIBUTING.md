# Contributing

Contributions are welcome — bug reports, new audits, and extra checks for existing ones.

## Repo layout

This is a single Claude Code plugin (`audit`) that bundles many audit skills:

```
.claude-plugin/marketplace.json     # lists the `audit` plugin
plugins/audit/
  .claude-plugin/plugin.json
  skills/<name>/SKILL.md             # each becomes the command /audit:<name>
```

The skill **directory name** is the command suffix: `skills/security/` → `/audit:security`. The `name:` in frontmatter is a display label.

## Adding a new audit

1. Create `plugins/audit/skills/<name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: audit-<name>
   description: <what it audits, when to use it>
   user-invocable: true
   argument-hint: "[--fix] [--scope=<path>] [--report]"
   ---
   ```
2. Write the methodology in the body. Keep findings **evidence-based** — every finding must cite a real `file:line` found via Grep/Glob/Read. Follow the anti-hallucination rules the other skills use (no invented identifiers, no speculation).
3. If it produces a report and should be part of `/audit:all`, add it to the covered set and tiers in `skills/all/SKILL.md`.
4. Update the command table in `README.md` and add a `CHANGELOG.md` entry.

## Validating

Before opening a PR:

```bash
claude plugin validate .
claude plugin validate ./plugins/audit
```

CI runs the same manifest checks (valid JSON, every skill has a `SKILL.md` with frontmatter, plugin sources resolve).

## Submitting changes

1. Branch (`feat/<name>` or `fix/<name>`)
2. Make your changes
3. Ensure `claude plugin validate .` passes
4. Open a pull request describing what changed and why

## Testing a skill locally

```bash
/plugin marketplace add <path-to-your-clone>
/plugin install audit@soreavis-skills
/reload-plugins
/audit:<name>
```
