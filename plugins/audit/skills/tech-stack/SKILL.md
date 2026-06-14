---
name: audit-tech-stack
description: Tech stack compliance audit. Checks code quality conventions — inline styles vs CSS framework, type safety, component architecture, linting, framework best practices. Adapts to detected stack.
user-invocable: true
argument-hint: "[--fix] [--scope=<path>] [--report]"
---

# Tech Stack Compliance Audit

Audit the codebase against best practices for the detected tech stack. Adapts checks based on what's actually in use.

## Arguments

- `$ARGUMENTS` — optional:
  - First positional argument is scope path (e.g., `/audit:tech-stack src/components/`)
  - `--fix` — auto-fix issues after audit
  - `--report` — save report to `_local/reports/tech-stack-audit-<YYYY-MM-DD>.md`
  - No flags = audit only, print results

## Phase 1: Detect the Stack

Read project config files to identify what's in use. This determines which checks to run.

| Check | How | Records |
|-------|-----|---------|
| Framework | `package.json` deps: `next`, `react`, `vue`, `@angular/core`, `svelte`. `requirements.txt`: `django`, `flask`. `go.mod`, `Cargo.toml`. | Framework + version |
| TypeScript | `tsconfig.json` exists? Check `strict` flag value. | TS enabled, strict mode on/off |
| CSS framework | `package.json` deps: `tailwindcss`. Glob for `*.module.css` (CSS modules). `styled-components` in deps. | CSS approach |
| CSS tokens | If Tailwind: read `tailwind.config.*` or `globals.css` for `@theme` block. Extract available design tokens/custom properties. If no Tailwind: check `globals.css` for CSS custom properties (`--color-*`, `--font-*`). | Token list |
| Linting | `package.json` deps: `eslint`, `biome`, `prettier`. Check for `.eslintrc*`, `biome.json`. | Linter names |
| Testing | `package.json` deps/devDeps: `vitest`, `jest`, `mocha`, `playwright`, `cypress`. | Test framework |
| Build commands | `package.json` scripts: `build`, `lint`, `test`, `typecheck`. | Exact commands |

**Stack-dependent checks:** Only run checks relevant to the detected stack. If no TypeScript, skip TypeScript checks. If no Tailwind, skip Tailwind vs inline styles. If no Next.js, skip Next.js best practices.

Print detected stack summary before starting checks:
```
Stack: Next.js 14 + TypeScript (strict) + Tailwind 4
Linting: ESLint + Prettier
Testing: vitest
Scope: [full project or specified path]
```

## Phase 2: Run Checks

### Check 1: CSS Framework vs Inline Styles

**Skip if:** no CSS framework detected (pure inline styling is the approach — nothing to compare against).

For each component file in scope:

**How to count:**
- Grep for `style={{` or `style={` in JSX/TSX files. Count occurrences per file.
- Grep for `className=` in the same files. Count occurrences per file.
- Calculate ratio: inline / (inline + className). Report per file.

**Findings:**
- Flag files where inline ratio > 80% (most styling is inline when a CSS framework exists)
- For each flagged file, categorize the inline styles:
  - **Acceptable inline:** dynamic values that depend on state/props (ternaries, calculated values, animation interpolation)
  - **Should use CSS framework:** static values (fixed padding, margin, colors, font sizes, flex/grid layout)
- Severity: HIGH if static inline styles dominate, MEDIUM if mixed

### Check 2: Design Token Usage

**Skip if:** no design tokens detected (no CSS custom properties, no Tailwind theme config).

**How to search:**
- Grep for hardcoded hex colors in component files: pattern `#[0-9a-fA-F]{3,8}` (exclude comments, SVG path data, and image data URIs)
- Cross-reference each hex value with detected tokens. If a hex matches an available token, flag it.
- Also flag: hex values used in 3+ files that should be extracted to a token.

**Findings:**
- Severity: MEDIUM for each hardcoded hex that has an equivalent token
- Severity: LOW for colors used in 3+ places without a token

### Check 3: TypeScript Compliance

**Skip if:** no TypeScript detected.

**How to search:**
- Grep for `\bany\b` in `.ts` and `.tsx` files (use word boundary `\b` to avoid matching "company", "many", etc.). Exclude: `node_modules/`, type declaration files (`*.d.ts`), test files if they use `any` for mocking.
- Count `: any`, `as any`, `<any>` separately.
- Grep for `@ts-ignore` and `@ts-expect-error`
- Check `tsconfig.json` for `strict: true`. If not strict, flag as HIGH.

**Findings:**
- Severity: HIGH for `strict: false` in tsconfig
- Severity: MEDIUM for each `as any` (type assertion bypass)
- Severity: LOW for `@ts-expect-error` with explanation comment (acceptable), HIGH without explanation

### Check 4: Lint Compliance

**Skip if:** no linter detected.

**How to search:**
- Grep for `eslint-disable` (all forms: `eslint-disable-next-line`, `eslint-disable-line`, `/* eslint-disable */`)
- For each: note if it's scoped (next-line) or file-wide
- Classify: justified (e.g., `no-img-element` for dynamic image gallery, `react-hooks/exhaustive-deps` with documented reason) vs fixable (the underlying issue could be resolved)

**Findings:**
- Severity: HIGH for file-wide disables without justification
- Severity: MEDIUM for fixable next-line disables
- Severity: LOW for justified disables (still count them)

### Check 5: Component Architecture

For each component file in scope:

**How to check:**
- Count lines per file. Flag files > 300 lines.
- Count lines per function/component. Flag functions > 50 lines.
- For React: check if `"use client"` is necessary. It's needed ONLY for: `useState`, `useEffect`, `useRef`, `useContext`, event handlers (`onClick`, `onChange`, etc.), `useRouter` (next/navigation), browser APIs. If none of these are used, `"use client"` is unnecessary.
- Check if component props have type/interface definitions.

**Findings:**
- Severity: HIGH for files > 300 lines (should be split)
- Severity: MEDIUM for functions > 50 lines
- Severity: LOW for unnecessary `"use client"`
- Severity: LOW for untyped props

### Check 6: Framework Best Practices

**Run only checks relevant to the detected framework.**

**Next.js checks:**
- Grep for `<img ` (HTML img) vs `next/image` imports. Flag `<img` usage (should use `next/image` for optimization). Exception: SVGs and tiny icons.
- Check if pages export `metadata` objects (App Router) or use `<Head>` (Pages Router)
- Look for heavy client components that could use `dynamic()` import
- Check for `next/font` usage vs external font loading

**React (non-Next) checks:**
- Check for `React.lazy()` usage on route-level components
- Check for error boundaries

**Vue checks:**
- Check for `defineProps` type safety
- Check for `<script setup>` usage (preferred over options API)

**No framework checks available for the detected stack:** Skip this section and note "No framework-specific checks available for [stack]."

### Check 7: CSS Architecture

**Skip if:** no CSS files detected (pure Tailwind or CSS-in-JS).

**How to check:**
- If global CSS files exist: count total classes, look for duplicate class definitions
- Check for inline styles overriding CSS class properties in the same element
- Look for inconsistent patterns: same visual element styled differently in different components

**Findings:**
- Severity: MEDIUM for duplicate class definitions
- Severity: LOW for inconsistent styling patterns

### Check 8: Shared Component/Pattern Usage

**Skip if:** project has fewer than 5 component files (too small for reuse analysis).

**How to check:**
- Search for near-identical UI patterns across components. Specifically:
  - Same HTML structure + similar styling in 3+ files (candidate for extraction)
  - Same data-fetching pattern duplicated across files
  - Same form validation logic in multiple form components

**NOTE:** Do NOT look for specific component names like "ImageLightbox" or "ZoomHint" — these are project-specific. Instead, look for PATTERNS that are duplicated and SHOULD be shared components, whatever they may be.

**Findings:**
- Severity: MEDIUM for patterns duplicated in 3+ places
- Severity: LOW for patterns duplicated in 2 places

## Phase 3: Scoring

### Scoring Rubric

Each check scores 0-10 based on the ratio of findings to total items checked:

| Score | Meaning |
|-------|---------|
| 10 | No findings |
| 8-9 | Only LOW findings |
| 6-7 | Some MEDIUM findings, no HIGH |
| 4-5 | HIGH findings present |
| 2-3 | Multiple HIGH findings |
| 0-1 | Pervasive issues across the codebase |

**Overall grade** = average of all applicable check scores (skip checks that were N/A):
- A: average 9.0+ (90%+)
- B: average 8.0+ (80%+)
- C: average 7.0+ (70%+)
- D: average 6.0+ (60%+)
- F: average below 6.0

### Report Format

```markdown
## Tech Stack Audit — [Project Name]
### Stack: [detected] | Date: [YYYY-MM-DD] | Scope: [path]

| # | Check | Score | Status | Key Issues |
|---|-------|-------|--------|------------|
| 1 | CSS Framework vs Inline | 7/10 | MEDIUM | 4 files with >80% inline |
| 2 | Design Tokens | N/A | — | No tokens configured |
| 3 | TypeScript | 8/10 | LOW | 3 `as any` casts |
| 4 | Lint Compliance | 9/10 | LOW | 2 justified disables |
| 5 | Component Architecture | 5/10 | HIGH | 2 files >300 lines |
| 6 | Framework Best Practices | 8/10 | LOW | 5 `<img>` should use next/image |
| 7 | CSS Architecture | N/A | — | Pure Tailwind, no CSS files |
| 8 | Shared Patterns | 7/10 | MEDIUM | 3 duplicated patterns |
| **Overall** | **7.3/10** | **C** | |

### Priority Actions
1. [HIGH] Split large components: ComponentA.tsx (450 lines), ComponentB.tsx (380 lines)
2. [HIGH] Enable TypeScript strict mode
3. [MEDIUM] Replace hardcoded #0F2847 with var(--color-navy-dark) in 6 files
...
```

**Print to conversation:** Scorecard table + priority actions.
**Save to file** if `--report` is set, using report location logic (same as other audit skills).

## Phase 4: Fix (with --fix flag)

If `--fix` is passed, apply fixes in this order:

1. **Config fixes** (tsconfig strict mode, eslint config)
2. **Design token replacements** (hardcoded hex -> CSS vars/Tailwind tokens). RULE: only replace if the token is an exact match. Do NOT create new tokens.
3. **CSS framework migration** (static inline styles -> CSS framework classes). RULE: keep dynamic/state-dependent inline styles as-is. Only migrate STATIC values.
4. **Component splitting** (files > 300 lines). RULE: extract sub-components, do NOT change visual output or prop interfaces.
5. **Framework migrations** (`<img>` -> framework image component, add metadata, etc.)

### Fix Rules:
- Page must look identical after fixes (no visual changes)
- Do NOT change component prop interfaces
- Run lint after each file change (if lint command detected)
- Run build after all fixes (if build command detected)
- If no lint/build commands, note: "No lint/build commands found — manual verification recommended."

## Anti-Hallucination Rules

- Do NOT reference specific component names (ImageLightbox, ZoomHint, etc.) — discover what exists in THIS project
- Do NOT assume specific CSS conventions (easing functions, border-radius rules) — discover from the codebase
- Do NOT report TypeScript findings in JavaScript projects
- Do NOT report Tailwind findings in projects without Tailwind
- Do NOT report Next.js findings in non-Next.js projects
- If a check returns 0 findings and 0 items to check, score it N/A (not 10/10)
- If Grep returns no matches for a pattern, report "no instances found" — do NOT invent findings
- Score based only on concrete findings with file:line evidence
- **Never invent names.** Do not fabricate hook names, component names, utility names, or file names in findings or recommendations. If you find duplicated logic, describe the pattern and list the real file paths — do NOT name a hypothetical extraction (e.g., ~~"extract useDragReorder hook"~~).
- **Every file path and line number must be real** — confirmed by tool calls during this audit. No fabricated evidence.
