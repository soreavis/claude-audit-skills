---
name: audit-deps
description: Dependency health audit — licenses, outdated packages, unused deps, bundle size impact, duplicates, and vulnerabilities. Works on Node.js, Python, Go, and Rust projects.
user-invocable: true
argument-hint: "[--fix] [--report] [--skip-licenses] [--skip-outdated] [--skip-bundle]"
---

# Dependency Health Audit

Deep audit of project dependencies beyond just vulnerabilities. Covers licenses, staleness, bloat, duplicates, and bundle impact.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — auto-fix: remove unused deps, update safe patches
  - `--report` — save report to `_local/reports/deps-audit-<YYYY-MM-DD>.md`
  - `--skip-licenses` — skip license compliance check
  - `--skip-outdated` — skip outdated version check
  - `--skip-bundle` — skip bundle size analysis
  - No flags = full audit, report only

## Setup

### Detect Package Manager & Stack

| Check | How | Records |
|-------|-----|---------|
| Node.js | `package.json` exists | npm/yarn/pnpm (check for lockfile type) |
| Python | `requirements.txt`, `pyproject.toml`, `Pipfile` | pip/poetry/pipenv |
| Go | `go.mod` | go modules |
| Rust | `Cargo.toml` | cargo |
| Lockfile | Check for `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `go.sum`, `Cargo.lock` | Lockfile type + committed status |

If multiple package managers detected (monorepo), audit each independently.

## Checks

### Check 1: Vulnerability Scan — Severity: by vuln level

**How to run (execute the actual command):**
- Node.js: `npm audit --json` (or `yarn audit --json` or `pnpm audit --json`)
- Python: `pip-audit --format json` (if installed) or `safety check --json`
- Go: `govulncheck ./...` (if installed)
- Rust: `cargo audit --json` (if installed)

**If the audit tool is not installed:** Report "Tool not installed — run `[install command]` to enable vulnerability scanning" and mark as WARN, not FAIL. Do NOT fabricate vulnerability data.

**Parse results:**
- Count by severity: critical, high, moderate, low
- For each critical/high: report package name, version, vulnerability ID, fix version (if available)
- Separate production deps from dev deps (production vulns are higher severity)

**Findings:**
- CRITICAL: production dep with critical/high vulnerability that has a fix available
- HIGH: production dep with moderate vulnerability
- MEDIUM: dev dep with any vulnerability
- LOW: vulnerability with no fix available (informational)

### Check 2: License Compliance — Severity: varies

**Skip if** `--skip-licenses` flag.

**How to check:**
- Node.js: read `node_modules/*/package.json` for `license` field. Or run `npx license-checker --json` if available.
- Python: `pip-licenses --format json` if available
- Go: check `go.sum` packages against known license databases
- Rust: `cargo license` if available

**If license tool not available:** Read lockfile, extract package names, and check `node_modules/<pkg>/package.json` license field directly (Node.js). For other stacks, report "Install [tool] for license scanning."

**Classify licenses:**

| Category | Licenses | Risk |
|----------|----------|------|
| Permissive (safe) | MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, 0BSD, Unlicense, CC0-1.0 | None |
| Weak copyleft (caution) | LGPL-2.1, LGPL-3.0, MPL-2.0, EPL-1.0 | MEDIUM — OK for most uses but review obligations |
| Strong copyleft (flag) | GPL-2.0, GPL-3.0, AGPL-3.0 | HIGH — may require open-sourcing your code |
| Unknown | No license field, `UNLICENSED`, custom | HIGH — legal risk, cannot determine usage rights |
| Commercial | Proprietary, paid | WARN — verify license is valid for this project |

**Findings:**
- HIGH: GPL/AGPL dependency in a non-GPL project
- HIGH: dependency with no license or unknown license
- MEDIUM: weak copyleft dependency (note obligation)
- PASS: all permissive licenses

### Check 3: Outdated Dependencies — Severity: varies

**Skip if** `--skip-outdated` flag.

**How to check:**
- Node.js: `npm outdated --json` (or `yarn outdated --json`)
- Python: `pip list --outdated --format json`
- Go: `go list -u -m all`
- Rust: `cargo outdated -R --format json` (if installed)

**If command fails or tool not installed:** Report what worked and skip what didn't.

**Classify staleness:**

| Behind by | Severity | Risk |
|-----------|----------|------|
| Patch (1.2.3 → 1.2.5) | LOW | Bug fixes, safe to update |
| Minor (1.2.3 → 1.4.0) | MEDIUM | New features, usually backward-compatible |
| Major (1.2.3 → 2.0.0) | HIGH | Breaking changes, needs migration |
| EOL / Deprecated | CRITICAL | No security patches, must replace |

**How to detect EOL/deprecated:**
- Check `npm info <pkg> deprecated` for Node.js packages (only for packages flagged as outdated, not all packages)
- Grep for `deprecated` in package metadata
- Known EOL packages: `request`, `moment` (suggest `date-fns` or `dayjs`), `tslint` (suggest `eslint`), `csurf`

**Findings:**
- CRITICAL: deprecated/EOL production dependency
- HIGH: major version behind on production dependency
- MEDIUM: minor version behind on production dependency
- LOW: patch version behind

### Check 4: Unused Dependencies — Severity: MEDIUM

**How to check (Node.js):**
1. Read `package.json` to get list of all dependencies (both `dependencies` and `devDependencies`)
2. For each dependency name:
   - Grep source files for: `import.*from\s+['"]<pkg>`, `require\(\s*['"]<pkg>`, `import\s+['"]<pkg>`
   - Also check config files that reference deps: `next.config.*`, `tailwind.config.*`, `postcss.config.*`, `vitest.config.*`, `jest.config.*`, `.eslintrc*`, `babel.config.*`
   - Also check `package.json` scripts for CLI tools (e.g., `tsc`, `eslint`, `vitest`)
3. If a dependency is not imported/referenced anywhere → it's unused

**Known exceptions (NOT unused even if not imported directly):**
- `typescript` — used by tsc, referenced in tsconfig
- `@types/*` — used by TypeScript compiler
- `eslint-config-*`, `eslint-plugin-*` — referenced in eslint config
- `prettier` — used by editor/CLI
- `tailwindcss` — referenced in postcss/tailwind config
- `postcss`, `autoprefixer` — referenced in postcss config
- Peer dependencies of other packages

**How to check (Python):**
- Compare `requirements.txt` entries with `import` statements across `.py` files
- Note: Python package name and import name often differ (e.g., `Pillow` → `import PIL`). Use `pip show <pkg>` to get the import name if available.

**Findings:**
- MEDIUM: production dependency that appears unused (list each with evidence: "no imports found")
- LOW: dev dependency that appears unused

### Check 5: Duplicate Dependencies — Severity: LOW

**Node.js only.**

**How to check:**
- Run `npm ls --all --json` and parse for packages appearing at multiple versions
- Or read `package-lock.json` and search for package names that appear with different version numbers

**Findings:**
- MEDIUM: same package at 2+ significantly different versions (e.g., `lodash` 3.x and 4.x)
- LOW: same package at slightly different versions (patch differences)

### Check 6: Bundle Size Impact — Severity: varies

**Skip if** `--skip-bundle` flag or if project is backend-only (no client-side bundle).

**How to check:**
- If `next build` output exists (`.next/`): check `.next/analyze` or run build with `ANALYZE=true` if available
- Check for large known-heavy packages in deps: `moment` (suggest `date-fns`), `lodash` (suggest `lodash-es` or individual imports), `aws-sdk` (suggest `@aws-sdk/client-*`), `firebase` (suggest individual imports)
- If `next/bundle-analyzer` or `webpack-bundle-analyzer` is configured, note its availability

**Findings:**
- HIGH: heavy package where a lighter alternative exists (moment → date-fns, lodash → lodash-es)
- MEDIUM: full library imported where tree-shakeable alternative exists
- LOW: bundle analyzer not configured (recommendation to add)

## Report

```markdown
# Dependency Audit — [Project Name]
**Date:** YYYY-MM-DD | **Stack:** [detected] | **Package Manager:** [detected]
**Total deps:** X production, Y dev

## Summary
| Check | Critical | High | Medium | Low | Status |
|-------|----------|------|--------|-----|--------|
| Vulnerabilities | X | X | X | X | [OK/WARN/FAIL] |
| Licenses | X | X | X | X | [OK/WARN/FAIL] |
| Outdated | X | X | X | X | [OK/WARN/FAIL] |
| Unused | — | — | X | X | [OK/WARN] |
| Duplicates | — | — | X | X | [OK/WARN] |
| Bundle Size | — | X | X | X | [OK/WARN] |

## Critical Actions
[all critical/high findings]

## Dependency Details
[per-dependency breakdown for flagged items]
```

## Fix Phase (with --fix flag)

If `--fix` is passed:

### Safe auto-fixes:
1. **Remove unused deps:** `npm uninstall <pkg>` for each confirmed unused package. Run build/tests after to verify nothing breaks.
2. **Update patch versions:** `npm update` (updates within semver range). Run tests after.
3. **Replace deprecated packages:** Only if there's a 1:1 drop-in replacement (e.g., `moment` → `dayjs` is NOT 1:1, so just recommend it). Do NOT attempt complex migrations.

### NOT auto-fixed (recommend only):
- Major version updates (breaking changes)
- License replacements (requires legal review)
- Bundle size optimizations (requires code changes)
- Vulnerability fixes requiring major updates

### After fixes:
- Run build command
- Run test suite
- If anything breaks, revert and report what failed

## Anti-Hallucination Rules

- **Run real commands.** `npm audit`, `npm outdated`, etc. produce real data. Do NOT fabricate vulnerability counts or version numbers.
- **If a tool is not installed, say so.** Do NOT guess what `pip-audit` would find. Report "tool not installed."
- **Known exceptions list is exhaustive.** Only the packages listed in Check 4 exceptions are exempt. Do NOT add others without Grep evidence of usage.
- **License data comes from package metadata.** Read actual `license` fields from `package.json` files. Do NOT guess licenses based on package name.
- **Bundle size claims need evidence.** Do NOT say "lodash adds 500KB" without checking. Just flag known-heavy packages and recommend alternatives.
- **Never fabricate package names, versions, or vulnerability IDs.** Every finding must reference real data from command output or file reads.
- **Python import name ≠ package name.** Don't flag a Python package as unused just because `import <exact-package-name>` wasn't found. The import name is often different.
