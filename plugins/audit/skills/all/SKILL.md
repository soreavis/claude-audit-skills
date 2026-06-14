---
name: audit-all
description: Orchestrator that runs the bundled audit skills (security, deep, deps, compliance, tech-stack, forms, a11y, seo, deploy, responsive, hallucination) in sequence against a project and merges their reports into one combined scorecard. All sibling audits ship in this same plugin — nothing else to install. Use when the user wants to run "all audits" / "the full audit suite" / "every pre-launch check" before shipping.
argument-hint: "[--tier=quick|standard|full] [--include=<name>] [--skip=<name>] [--scope=<path>] [--fix] [--report]"
allowed-tools: Bash, Read, Glob, Grep, Agent
---

# audit-all

Runs the bundled `audit` skills against a project in one pass, then merges their reports into a single combined scorecard.

**Design choice: orchestrate, don't duplicate.** Each audit's canonical checklist lives in its own sibling skill in this plugin (`security`, `deploy`, `compliance`, …). This skill does NOT inline copies of those checklists — it reads each sibling's own `SKILL.md` via an `Agent` subprocess and aggregates the results. When a sibling audit is updated, audit-all picks up the change automatically.

Because every audit is bundled in the same plugin, there is no separate install step and no "missing skill" failure mode — the siblings are always present next to this one.

## Covered audits

The sibling audits this orchestrator can run (all bundled in the `audit` plugin):

| Skill | Command | Focus |
|---|---|---|
| security | `/audit:security` | Attack surface (33 vectors) |
| deep | `/audit:deep` | Code quality + security + injection (3 agents) |
| deps | `/audit:deps` | Dependency health (licenses, outdated, unused, bundle) |
| compliance | `/audit:compliance` | GDPR / ISO 27001 / ISO 9001 (7 dimensions) |
| tech-stack | `/audit:tech-stack` | Stack-convention conformance (8 checks) |
| forms | `/audit:forms` | Form hardening (38 checks) |
| a11y | `/audit:a11y` | WCAG 2.1 AA (29 checks) |
| seo | `/audit:seo` | SEO + GEO (24 checks) |
| deploy | `/audit:deploy` | Pre-deploy readiness (29 checks) |
| responsive | `/audit:responsive` | Mobile / responsive (15 checks) |
| hallucination | `/audit:hallucination` | LLM fabrication risk (46 vectors) |

`diff` (report comparator) is intentionally NOT part of a run-all — it compares two existing reports rather than auditing code. Run it separately with `/audit:diff` after two `audit-all` passes.

## Resolving sibling skills

The sibling audits live next to this skill inside the plugin, one directory per audit:

```
<plugin>/skills/all/SKILL.md      ← this skill
<plugin>/skills/security/SKILL.md
<plugin>/skills/deploy/SKILL.md
... etc
```

Resolve each sibling by its short name relative to THIS skill's directory: `../<name>/SKILL.md`. If the relative path is ambiguous, Glob for `**/skills/<name>/SKILL.md` under the plugin root and take the match. **Do NOT assume a global `~/.claude/skills/<name>/` path** — these audits are plugin-bundled, not standalone installs.

## Arguments

- `--tier=<name>` — preset audit list (see tiers below). Default: `standard`.
- `--include=<name>` — add a specific audit to the resolved list. Repeatable.
- `--skip=<name>` — remove an audit from the resolved list. Repeatable.
- `--scope=<path>` — narrow all sub-audits to a directory.
- `--fix` — pass `--fix` through to every sub-audit that supports it.
- `--report` — save combined report to `_local/reports/audit-all-<YYYY-MM-DD>.md`.

Audit names are the short forms in the table above (`security`, `deep`, `a11y`, …).

## Tiers

Presets that resolve to specific audit lists. Start simple, scale up.

| Tier | Audits | When to use |
|---|---|---|
| `quick` | security, deploy | Fast sanity check; personal projects or MVP |
| `standard` (default) | security, deploy, forms, a11y, responsive | Most public-facing web projects |
| `full` | hallucination, security, deep, deps, compliance, tech-stack, forms, a11y, seo, responsive, deploy | Pre-launch of a paid / regulated / customer-facing product |

Tiers compose with `--include`/`--skip`:

```
/audit:all --tier=quick --include=a11y            # quick + a11y
/audit:all --tier=standard --skip=forms           # standard minus forms
/audit:all --tier=full --skip=hallucination       # full minus hallucination (no AI features)
/audit:all --tier=full --scope=src/ --report      # everything, scoped, saved to file
```

## Execution

### Step 1: Resolve audit list

1. Start with the tier's audit list (or `standard` if no tier).
2. Apply `--include` (adds).
3. Apply `--skip` (removes).
4. Print resolved list + count.

Example output:
```
Tier: standard | Audits: security, deploy, forms, a11y, responsive (5)
```

### Step 2: Locate sibling skills

For each audit in the resolved list, resolve its `SKILL.md` path as described in **Resolving sibling skills** above (`../<name>/SKILL.md` relative to this skill, or Glob fallback). Record the resolved absolute path for each. Every sibling is bundled, so all should resolve; if one genuinely cannot be found, note it and continue with the rest.

### Step 3: Create progress tracker

Write `_local/reports/audit-all-progress-<YYYY-MM-DD>.md` with a checkbox per resolved audit + a table to fill with counts. Update it after EVERY step.

Example:
```markdown
# audit-all Progress — 2026-04-21
## Status
- [ ] security
- [ ] deploy
- [ ] forms
- [ ] a11y
- [ ] responsive
- [ ] Combined report
## Counts
| Audit | Critical | High | Medium | Low | Score |
|-------|----------|------|--------|-----|-------|
```

### Step 4: Run each audit via Agent subprocess

For each audit, sequentially (NOT in parallel — aggregate reports need stable ordering):

Spawn an `Agent` with this prompt template (substitute the resolved absolute path):

```
Run the audit skill at <resolved-path-to>/skills/<name>/SKILL.md against the project at <cwd>.
<If --scope: > Scope: <scope>
<If --fix: > Pass --fix through if the skill supports it.

Read the full SKILL.md and follow its instructions exactly. Do NOT improvise — the skill's own anti-hallucination rules apply.

Write the full report to: _local/reports/audit-all-<name>-<YYYY-MM-DD>.md

At the end of your response, emit ONLY this summary block (parseable):
---AUDIT-SUMMARY---
audit: <name>
critical: N
high: N
medium: N
low: N
score: <whatever the skill returns: grade / count / verdict>
---END-SUMMARY---
```

After the agent returns:
1. Extract the summary block (regex: `---AUDIT-SUMMARY---\n(.+?)\n---END-SUMMARY---`)
2. If the block is missing or unparseable: mark as `UNPARSEABLE` in the tracker — do NOT fabricate counts.
3. Update the progress tracker: check the box, fill the count row.
4. Print a 1-line status to the conversation:
   ```
   [1/5] security complete — 2 critical, 5 high, 11 medium, 4 low
   ```

**If the agent fails or errors:** mark as `FAILED` in the tracker, continue with remaining audits. Don't abort the whole run.

### Step 5: Combined report

After all resolved audits finish (or are marked skipped/failed), produce the combined report.

```markdown
# audit-all Combined Report — <project name>
**Date:** YYYY-MM-DD | **Tier:** <tier> | **Scope:** <scope> | **Audits run:** N of M

## Overall Verdict
<Derive from the sub-audit summaries:>
- **SHIP** — zero critical, zero high across all audits
- **SHIP WITH WARNINGS** — zero critical, some high/medium
- **DO NOT SHIP** — one or more critical findings

## Per-Audit Summary
| Audit          | Critical | High | Medium | Low | Score       |
|----------------|----------|------|--------|-----|-------------|
| security       | 2        | 5    | 11     | 4   | 18/33       |
| deploy         | 0        | 1    | 4      | 3   | WARNINGS    |
| forms          | 0        | 2    | 6      | 2   | B (82%)     |
| a11y           | 1        | 3    | 5      | 2   | C (74%)     |
| responsive     | 0        | 4    | 2      | 1   | 7.8/10      |
| **Totals**     | **3**    | **15** | **28** | **12** |          |

## Audits Skipped / Failed
<list if any>

## Top 10 Priority Actions
<Cross-audit priority list, critical → high → medium>
1. [CRITICAL] [security V5] — SSRF on /api/fetch — src/app/api/fetch/route.ts:22
2. [CRITICAL] [a11y 3a] — Focus outline removed without replacement — src/app/globals.css:18
3. [HIGH] [deploy D1] — console.log in src/components/Header.tsx:42
...

## Full Reports
Each sub-audit has a full report at `_local/reports/audit-all-<name>-<YYYY-MM-DD>.md`.
```

Print to conversation: **overall verdict + per-audit summary table + top 10 priority actions**. The full combined report goes to file if `--report` is set.

## Flag interactions

- `--fix` passes through to each sub-audit. Sub-audits that don't support `--fix` ignore it. audit-all does NOT do its own fixing — it only orchestrates.
- `--scope` passes through to each sub-audit.
- `--tier` + `--include`/`--skip` compose.

## Anti-hallucination rules

- **Vector counts come from sub-audit summary blocks, never fabricated.** If a sub-audit's summary is missing or unparseable, mark it `UNPARSEABLE` in the combined report. Do NOT interpolate or guess counts from agent prose.
- **Priority Actions must come from actual sub-audit findings.** Every line item needs a real file:line reference that came from an audit's report. Never invent file paths.
- **Sub-audit skills are read from their bundled sibling path** (`../<name>/SKILL.md` relative to this skill, or the Glob match). Do NOT reconstruct their logic from memory, and do NOT read from a global `~/.claude/skills/` path.
- **The overall verdict (SHIP / WARNINGS / DO NOT SHIP) is derived mechanically from summary counts.** Do NOT override based on prose judgment.
- **Sub-audits run sequentially, one agent at a time.** Don't launch agents in parallel — the tokens + context pressure aren't worth the latency savings, and aggregating parallel streams is error-prone.
- **If a sub-audit agent fails or times out**, mark it `FAILED` in the tracker and continue. Don't re-run, don't guess what the missing audit would have found.
