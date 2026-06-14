---
name: audit-diff
description: Compare two audit reports and show what improved, what regressed, and what's new. Works with any audit-* report pair from _local/reports/.
user-invocable: true
argument-hint: "[<older-report>] [<newer-report>] [--report]"
---

# Audit Diff: Compare Two Audit Reports

Compare two audit reports to show progress over time — what improved, what regressed, what's new, what was fixed.

## Arguments

- `$ARGUMENTS` — positional and optional flags:
  - First arg: path to older report (optional — auto-detects if omitted)
  - Second arg: path to newer report (optional — auto-detects if omitted)
  - `--report` — save diff report to `_local/reports/audit-diff-<YYYY-MM-DD>.md`
  - No args = auto-detect the two most recent mega-audit reports

## Auto-Detection

If no report paths given:

1. Glob for `_local/reports/mega-audit-*.md` (combined reports only, not numbered sub-reports like `mega-audit-1-deep-*`)
   - Pattern: `mega-audit-YYYY-MM-DD.md` (no number prefix)
2. Sort by date in filename
3. If 2+ found: use the two most recent as older and newer
4. If only 1 found: print "Only one audit report found. Run `/audit:all` again to generate a second report for comparison." and STOP.
5. If 0 found: print "No audit reports found in `_local/reports/`. Run `/audit:all` first." and STOP.

If paths are given, verify they exist via Read. If a file doesn't exist, print the error and STOP.

## How to Diff

### Step 1: Parse Both Reports

Read both report files. Extract from each:

**From the Executive Summary table:**
- Per-audit row: audit name, status, critical count, high count, medium count, low count, score
- Total row: deduplicated totals

**From the findings sections:**
- Each finding's: severity, description, file:line, audit source
- Each deferred item

**From fixes applied (if present):**
- Each fix: what was changed, which file

**Store as structured data** (in your working memory, not written to a file):
```
Report A (older):
  date: YYYY-MM-DD
  tier: X
  audits: { deep: { critical: N, high: N, ... }, security: { ... }, ... }
  findings: [ { severity, description, file, line, audit }, ... ]
  deferred: [ { description, file }, ... ]
  fixes: [ { description, file }, ... ]

Report B (newer):
  (same structure)
```

### Step 2: Compare Counts

For each audit that appears in BOTH reports:

| Metric | Change | Symbol |
|--------|--------|--------|
| Count decreased | Improved | arrow-down |
| Count increased | Regressed | arrow-up |
| Count unchanged | Same | dash |
| Audit not in older | New | "new" |
| Audit not in newer | Removed | "removed" |

### Step 3: Match Findings

Match findings between reports using file:line + description similarity:

1. **Exact match:** same file, same line (within +/-5 lines for minor code shifts), same severity → finding persists
2. **Fixed:** finding in older but not in newer → it was resolved
3. **New:** finding in newer but not in older → it's new (either a regression or a newly detected issue)
4. **Changed severity:** same file+description but different severity → severity changed

**Matching rules:**
- Match by file path first, then by description similarity
- If a file was renamed (old path doesn't exist, new path appeared with similar findings), note "possible rename" but list as new+fixed rather than guessing
- Do NOT try to match findings across different audits (a deep audit finding doesn't match a security audit finding even if they reference the same file)

### Step 4: Match Deferred Items

Compare deferred items between reports:
- In older AND newer → still deferred (no progress)
- In older but NOT in newer → was resolved (either fixed or refactored)
- In newer but NOT in older → newly deferred

## Report Format

### Conversation Output

Print a concise summary:

```
## Audit Diff: YYYY-MM-DD → YYYY-MM-DD

### Overall Trend: IMPROVING / REGRESSING / MIXED / STABLE

| Audit | Before | After | Change |
|-------|--------|-------|--------|
| Deep | 2C 5H 8M 3L | 0C 3H 6M 3L | -2C -2H -2M (improved) |
| Security | 18/33 | 22/33 | +4 vectors protected |
| Forms | D (52%) | B (82%) | +30% (improved) |
| Tech Stack | C (71%) | B (84%) | +13% (improved) |
| Deploy | NOT READY | WARNINGS | improved |
| **Total** | **2C 12H** | **0C 8H** | **-2C -4H** |

### Fixed Since Last Audit (X items)
1. [was CRITICAL] <description> — <file> (resolved)
2. [was HIGH] <description> — <file> (resolved)
...

### New Issues (Y items)
1. [CRITICAL] <description> — <file> (new)
2. [HIGH] <description> — <file> (new)
...

### Regressions (Z items)
[findings that got worse — severity increased or count increased]

### Still Deferred (N items)
[deferred items that haven't been addressed since last audit]

### Newly Resolved Deferred Items (M items)
[deferred items from last audit that are now fixed]
```

### Overall Trend Logic

- **IMPROVING**: total critical+high decreased AND no new critical findings
- **REGRESSING**: total critical+high increased
- **STABLE**: total critical+high unchanged (within +/-1)
- **MIXED**: some audits improved, others regressed (critical went down but high went up, or vice versa)

### Highlight Colors (for report file)

Use text markers since these are markdown files:
- Improvements: prefix with `[+]`
- Regressions: prefix with `[-]`
- Unchanged: prefix with `[=]`
- New: prefix with `[NEW]`

## Report File (with --report flag)

Save to `_local/reports/audit-diff-<YYYY-MM-DD>.md` with full details:

```markdown
# Audit Diff Report
**Comparing:** mega-audit-YYYY-MM-DD.md → mega-audit-YYYY-MM-DD.md
**Period:** N days between audits
**Trend:** IMPROVING / REGRESSING / MIXED / STABLE

## Summary Table
[full comparison table]

## Detailed Changes

### Fixed Items (X)
[full list with file:line, severity, which audit]

### New Issues (Y)
[full list]

### Regressions (Z)
[full list]

### Unchanged Findings (W)
[findings present in both — still need attention]

### Deferred Item Tracker
| Item | Status | Days Deferred |
|------|--------|--------------|
| <description> | Still deferred | N days |
| <description> | Resolved | — |
| <description> | New | — |

## Score Progression
| Audit | Report 1 | Report 2 | Delta |
|-------|----------|----------|-------|
```

## Comparing Individual Audit Reports

If the user passes paths to individual audit reports (not mega-audit combined reports), the diff still works but with limited scope:

- Read both files
- Extract severity counts and findings
- Compare the same way
- Note: "Comparing individual [audit-name] reports (not full mega-audit)"

## Comparing More Than Two Reports

If `_local/reports/` contains 3+ mega-audit reports and the user asks for a trend:

- Read all mega-audit combined reports (sorted by date)
- Extract total critical+high counts from each
- Print a trend line:
  ```
  Trend: 2024-01-15 (4C 12H) → 2024-02-01 (2C 8H) → 2024-03-15 (0C 5H)
  Direction: Consistently improving
  ```
- Only do this if explicitly asked ("show me the trend") — don't auto-run for all reports

## Anti-Hallucination Rules

- **Parse real data.** Read actual report files. Do NOT fabricate counts or findings. If a report doesn't contain a parseable summary table, say "Could not parse summary from [file] — report format may be non-standard."
- **Matching is best-effort.** Finding matching uses file+description heuristics. When uncertain, list as "possibly fixed" or "possibly new" rather than claiming definite match.
- **Do NOT invent file renames.** If an old finding's file doesn't exist and a new finding appeared in a different file, list them separately. Do NOT claim "file was renamed from A to B" without git evidence.
- **Day count is from filenames.** Calculate days between audits from the YYYY-MM-DD in filenames. Do NOT guess dates.
- **Trend requires 2+ data points.** Never describe a trend from a single report. "IMPROVING" requires proof that numbers went down.
- **Do NOT extrapolate.** Never say "at this rate, you'll reach zero issues by [date]." Trends are descriptive, not predictive.
