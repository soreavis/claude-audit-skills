---
name: audit-deep
description: Deep audit of code quality, security, and injection attack surface. Launches three parallel agents covering dead code, OWASP Top 10, and content injection vectors.
user-invocable: true
argument-hint: "[--fix] [--scope=<path>] [--security-only] [--quality-only] [--injection-only] [--report[=<path>]]"
---

# Deep Audit: Code Quality + Security + Injection Surface

Run a comprehensive three-pillar audit of the entire codebase. Launches three parallel agents and aggregates findings.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — automatically fix issues after audit (default: report only)
  - `--scope=<path>` — limit audit to specific directory (default: entire project)
  - `--security-only` — run only the security audit (Agent 2)
  - `--quality-only` — run only the code quality/simplify audit (Agent 1)
  - `--injection-only` — run only the hallucination/injection audit (Agent 3)
  - `--report` — save full report (see report location logic below)
  - `--report=<path>` — save report to a specific file path

If no flags are provided, all three audits run in parallel (report only, no auto-fix).

### Flag Precedence

Only ONE `--*-only` flag is allowed. If multiple are passed, use this priority: `--security-only` > `--quality-only` > `--injection-only`. Log which was selected.

### Report Location Logic

When `--report` is used without a path:
1. If `_local/reports/` exists → save there
2. Else if `_local/` exists → create `_local/reports/` and save there
3. Else if `.gitignore` contains `_local` → create `_local/reports/` and save there
4. Else → save to project root as `deep-audit-<YYYY-MM-DD>.md` (warn user it's tracked by git)

Filename format: `deep-audit-<YYYY-MM-DD>.md`

## Setup

Before launching agents:

1. **Detect project scope.** If no `--scope` given:
   - Glob for `src/`, `app/`, `lib/`, `pages/`, `components/` — use whatever exists
   - If none exist, use the project root (excluding `node_modules/`, `.next/`, `dist/`, `build/`, `vendor/`, `__pycache__/`)
   - Record the scope path to pass to each agent

2. **Detect build/lint/test commands.** Read `package.json` scripts, or check for `Makefile`, `pyproject.toml`, `Cargo.toml`. Record the exact commands for the fix phase. If none found, note "no build/lint configured."

3. **Detect tech stack.** Read `package.json` (or equivalent) to identify: framework, language, CSS approach. Pass this to each agent so they tailor their search patterns.

## Standardized Finding Format

Every agent MUST report findings in this format (one per finding):

```
### [SEVERITY] Category — Short description
- **File:** path/to/file.ts:42
- **Evidence:** <the problematic code or pattern found>
- **Impact:** <what could go wrong>
- **Fix:** <concrete remediation>
```

Severity values: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

If an agent returns findings in a different format, reformat them into this structure during aggregation.

## Phase 1: Launch Audit Agents

Unless a `--*-only` flag narrows scope, launch ALL three agents concurrently in a single message using the Agent tool. Each agent runs in its own context and returns findings.

### Agent 1: Code Quality & Simplify

**Agent tool prompt:**

> Audit code quality in the project at [cwd]. Scope: [scope path]. Tech stack: [detected stack].
>
> Use Grep and Glob to search for these specific patterns. For each finding, report the file path, line number, severity, and suggested fix using the format: `### [SEVERITY] Category — description` with File, Evidence, Impact, Fix fields.
>
> **1. Dead code:**
> - Grep for `import .* from` in [scope], then check if imported names are used in the file
> - Grep for `// ` followed by code patterns (commented-out code, not comments)
> - Look for functions/variables defined but never referenced
>
> **2. Redundant state (React/Vue projects only):**
> - Grep for `useState` where the value is derived from another state or props
> - Grep for `useEffect` that could be replaced with direct computation
> - Grep for inline array/object literals in JSX (e.g., `style={{ }}`, `options={[...]}` recreated every render)
>
> **3. Copy-paste patterns:**
> - Look for near-identical code blocks (same structure, different variable names) within and across files
>
> **4. Over-engineering:**
> - Find abstractions used in only one place (wrapper components, utility functions called once)
> - Grep for `process.env.NODE_ENV` checks shipping dev tools to production
>
> **5. Type issues (TypeScript projects only):**
> - Grep for `: any` and `as any` (exclude test files and type declaration files)
> - Grep for `@ts-ignore` and `@ts-expect-error`
> - IMPORTANT: use pattern `\bany\b` to avoid matching words like "company" or "many"
>
> **6. CSS conflicts:**
> - Grep for `style={{` in the same component that uses `className=` (inline overriding classes)
> - Look for duplicate CSS class definitions across stylesheets
>
> **7. Unnecessary re-renders (React projects only):**
> - Grep for inline object/array creation in JSX props: `prop={{ }}`, `prop={[ ]}`
> - Look for expensive computations without useMemo on frequently-rendered components
>
> **8. Memory leaks:**
> - Grep for `setTimeout|setInterval|addEventListener` inside `useEffect` and check for cleanup return
> - Pattern: `useEffect` containing `setTimeout` or `addEventListener` without a corresponding `clearTimeout`, `removeEventListener`, or `return () =>` cleanup
>
> End your response with:
> ```
> ---FINDINGS-SUMMARY---
> critical: N
> high: N
> medium: N
> low: N
> ---END-SUMMARY---
> ```

### Agent 2: Security Audit

**Agent tool prompt:**

> Audit security in the project at [cwd]. Scope: [scope path]. Tech stack: [detected stack].
>
> Use Grep and Glob to search for these OWASP Top 10 and web security issues. For each finding, include file:line evidence using the format: `### [SEVERITY] Category — description` with File, Evidence, Impact, Fix fields.
>
> **1. XSS:**
> - Grep for `dangerouslySetInnerHTML` — for each instance, trace the data source. Static content = LOW, external/user content = CRITICAL.
> - Grep for `innerHTML\s*=` (vanilla JS)
> - Grep for `v-html` (Vue)
> - Check CSP headers: search `next.config`, middleware, or server config for Content-Security-Policy. Flag `unsafe-inline` or `unsafe-eval`.
>
> **2. Authentication:**
> - Grep for cookie-setting code: `cookies.set`, `Set-Cookie`, `setCookie`. Check for `httpOnly`, `secure`, `sameSite` flags.
> - Grep for `===` comparisons on secrets/tokens (should use `timingSafeEqual`)
> - Grep for `Math.random` in security contexts (should use `crypto.randomBytes` or `crypto.getRandomValues`)
>
> **3. CSRF:**
> - Find all POST/PUT/DELETE endpoints. For each, check if it validates Origin/Referer headers or uses CSRF tokens.
> - Check for `sameSite` cookie attribute.
>
> **4. Injection:**
> - Grep for raw SQL: string concatenation or template literals near `query(`, `.raw(`, `execute(`. Parameterized queries are PASS.
> - Grep for `child_process`, `exec(`, `spawn(`, `execSync` — check if user input flows into commands.
> - Grep for `eval(`, `new Function(`, `setTimeout(string)` — dynamic code execution.
>
> **5. Information disclosure:**
> - Grep for `stack` or `message` in catch blocks sent to response (leaking stack traces)
> - Grep for `NEXT_PUBLIC_` or `VITE_` env vars that might contain secrets (API keys, DB URLs)
> - Grep for hardcoded strings matching secret patterns: API keys (length 20+), tokens, passwords
>
> **6. Dependencies:**
> - If `package.json` exists, note that `npm audit` should be run (do NOT run it yourself — just flag it as a recommendation)
> - Check if `package-lock.json` or `yarn.lock` or `pnpm-lock.yaml` exists and is committed
>
> **7. Security headers:**
> - Search config files for: Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, Content-Security-Policy, Referrer-Policy, Permissions-Policy
> - Flag any that are missing entirely
>
> **8. Open redirects:**
> - Grep for `redirect(`, `location.href =`, `window.location =`, `res.redirect(` where the URL comes from user input (query params, request body)
>
> **9. External resources:**
> - Grep for `<script src=`, `<link href=` pointing to external CDNs. Check for `integrity=` attribute (SRI). Dynamic CDNs like Google Fonts are exempt.
>
> **10. Secrets:**
> - Grep for patterns: `sk-`, `pk_`, `AKIA`, `ghp_`, `Bearer `, `password = "`, `secret = "`, `apiKey = "`
> - Check `.env.example` or `.env.local` for names that suggest secrets, then search codebase for those names hardcoded
>
> **IMPORTANT:** Only report findings with concrete file:line evidence. Do NOT speculate about what "might" exist. If a search returns no results, report it as "PASS — no instances found."
>
> End your response with the findings summary block.

### Agent 3: Injection Attack Surface Mapping

**Agent tool prompt:**

> Map the injection/content attack surface in the project at [cwd]. Scope: [scope path]. Tech stack: [detected stack].
>
> Use Grep and Glob to find every path where external or dynamic content enters the rendering pipeline. For each finding, include file:line evidence using the format: `### [SEVERITY] Category — description` with File, Evidence, Impact, Fix fields.
>
> **1. dangerouslySetInnerHTML inventory:**
> - Grep for `dangerouslySetInnerHTML` — for EVERY instance, report: file, line, what data it renders, whether that data is sanitized (DOMPurify, sanitize-html, etc.), and the data's origin (static file, API, user input, CMS)
> - Static/developer-controlled content = LOW. External/dynamic content without sanitization = CRITICAL.
>
> **2. Content injection vectors:**
> - Grep for URL param reading: `searchParams`, `useSearchParams`, `req.query`, `URLSearchParams`, `location.search`
> - For each: trace if the value is rendered in HTML. If rendered without escaping = HIGH.
> - Grep for `localStorage.getItem`, `sessionStorage.getItem`, `document.cookie` — trace into rendering.
>
> **3. Template literal HTML:**
> - Grep for backtick strings containing `<` followed by `${` — template literals building HTML with interpolation
> - This is HIGH if the interpolated value comes from user input.
>
> **4. Client-side state injection:**
> - Grep for `window.location`, `document.referrer`, `navigator.userAgent` used in rendered output
> - These are LOW (not easily exploitable) unless combined with `innerHTML` or `dangerouslySetInnerHTML`.
>
> **5. External content rendering:**
> - Grep for `fetch(` or `axios` responses that are rendered in the UI. Check if the response is validated/typed before rendering.
> - Grep for `<iframe` with dynamic `src` attribute — check if the URL is validated.
>
> **6. Form value reflection:**
> - Find form inputs whose values are displayed back in the UI (e.g., search results showing "You searched for: X"). Check for HTML escaping.
>
> **IMPORTANT:** Do NOT include a "future risk assessment" section. Only report findings with concrete evidence that exists NOW. Speculation about what might become dangerous "if content moves to a CMS" is not a finding — it's noise.
>
> End your response with the findings summary block.

## Phase 2: Aggregate & Report

After all agents return (or fail):

1. **Handle failures.** If an agent returned an error or no findings block, note "Agent N: FAILED — [error message]" in the report. Continue with whatever succeeded.

2. **Deduplicate.** Agent 2 (Security) and Agent 3 (Injection) may both flag `dangerouslySetInnerHTML` or XSS patterns. Merge overlapping findings (same file:line) — keep the more detailed entry, add a note "(also flagged by [other agent])".

3. **Combine and sort.** Merge all findings into a single list, sorted by: CRITICAL first, then HIGH, MEDIUM, LOW. Within each severity, sort by file path.

4. **Count.** Tally: total critical, high, medium, low. Count unique file:line pairs only (after dedup).

5. **Report format:**

```markdown
# Deep Audit Report — [Project Name]
**Date:** YYYY-MM-DD | **Scope:** [path] | **Stack:** [detected]

## Summary
| Pillar | Critical | High | Medium | Low | Status |
|--------|----------|------|--------|-----|--------|
| Code Quality | X | X | X | X | [OK/FAILED] |
| Security | X | X | X | X | [OK/FAILED] |
| Injection Surface | X | X | X | X | [OK/FAILED] |
| **Total (deduplicated)** | **X** | **X** | **X** | **X** | |

## Findings

### Critical
[findings...]

### High
[findings...]

### Medium
[findings...]

### Low
[findings...]

## Priority Actions
1. [top 5-10 most impactful findings with file:line]
```

6. **Print to conversation:** The summary table + priority actions. Do NOT print all findings — they're in the report.

7. **Save report** if `--report` flag is set, using the report location logic.

## Phase 3: Fix (if --fix flag)

If `--fix` is passed:

1. Detect build/lint/test commands (from Setup)
2. Read the report (from file if saved, or from the aggregation in memory)
3. Fix all **critical** findings first, then **high** findings
4. For **medium** findings: fix only if the change is <= 5 lines in a single file
5. Skip **low** findings
6. After all fixes: run build command (if available), then lint (if available). Fix any breakage.
7. Append a "Fixes Applied" section to the report listing what was changed.

If `--fix` is NOT passed: print the summary and say "Run `/audit:deep --fix` to fix critical and high issues."

**Do NOT ask "Want me to fix?" and wait** — the user will invoke `--fix` explicitly if they want fixes.

## Anti-Hallucination Rules

- **Never invent names.** Do not fabricate hook names (`useDragReorder`), component names (`AboutModal`), variable names, or file names that weren't found via Grep/Glob/Read. If you found duplicated drag-and-drop logic, say "drag-and-drop logic duplicated in src/A.tsx:40, src/B.tsx:55, src/C.tsx:120" — do NOT say "extract useDragReorder hook."
- **Findings must cite evidence.** Every finding must include a real file path and line number found via tool calls. "Noted but not fixed" items must also reference real files. If you can't cite a file:line, the finding doesn't exist.
- **Describe the problem, not a prescriptive solution.** Say "scroll-lock logic duplicated in 5 files" with the 5 file paths. Do NOT say "extract useLockBodyScroll hook" — naming the solution implies you verified it doesn't already exist and that this name is appropriate, which you haven't.
- **Never assume component/function existence.** Do not reference `AboutModal`, `VERSION`, or any identifier unless Grep confirmed it exists in the codebase.
- **Deferred items follow the same rules.** "Noted but not fixed" / deferred items must describe the duplication pattern + real file paths. No invented names for future extractions.
