---
name: audit-deploy
description: Pre-deployment production readiness checklist. Checks build health, debug code, dev URLs, env vars, error tracking, analytics, SEO, legal pages, and git state. Run before every production push.
user-invocable: true
argument-hint: "[--fix] [--scope=<path>] [--report] [--strict]"
---

# Pre-Deploy Production Readiness Audit

Run before every production push. Checks everything that should be verified before code goes live.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — auto-fix issues where possible (remove console.logs, add missing meta tags, etc.)
  - `--scope=<path>` — limit code checks to a specific directory
  - `--report` — save report to `_local/reports/deploy-audit-<YYYY-MM-DD>.md`
  - `--strict` — treat warnings as failures (for CI/CD integration)
  - No flags = audit only, report to conversation

## Setup

### 1. Detect Tech Stack

Read project config to tailor checks:

| Check | How |
|-------|-----|
| Framework | `package.json` deps: `next`, `react`, `vue`, `express`, `django`, `flask` |
| Language | `.ts`/`.tsx` files = TypeScript, `.py` = Python, `.go` = Go |
| Build command | `package.json` scripts: `build`. Or `Makefile`, `Cargo.toml`, `pyproject.toml` |
| Test command | `package.json` scripts: `test`, `test:ci`. Or `pytest`, `go test` |
| Lint command | `package.json` scripts: `lint`. Or `ruff`, `golangci-lint` |
| Deployment target | Check for `vercel.json`, `netlify.toml`, `Dockerfile`, `fly.toml`, `render.yaml`, `app.yaml` |

### 2. Determine Scope

If no `--scope`: scan entire project (excluding `node_modules/`, `.next/`, `dist/`, `build/`, `vendor/`, `__pycache__/`).

## Checks

Each check results in: **PASS**, **WARN**, or **FAIL**.
- FAIL = must fix before deploying
- WARN = should fix, not blocking (unless `--strict`)
- PASS = good to go

### Category 1: Build Health

**B1: Build compiles** — Severity: FAIL
- Run the detected build command (e.g., `npm run build`)
- PASS: build succeeds with exit code 0
- FAIL: build fails
- Note: if no build command detected, WARN "No build command found"

**B2: Type checking passes** — Severity: FAIL
- If TypeScript: run `npx tsc --noEmit`
- If Python with mypy: run `mypy .`
- PASS: no type errors
- FAIL: type errors found
- N/A: no type checker configured

**B3: Lint passes** — Severity: WARN
- Run detected lint command
- PASS: no lint errors (warnings OK)
- WARN: lint errors found
- N/A: no linter configured

**B4: Tests pass** — Severity: FAIL
- Run detected test command
- PASS: all tests pass
- FAIL: test failures
- WARN: no test command found

### Category 2: Debug Code & Dev Artifacts

**D1: No console.log in production code** — Severity: WARN
- Grep for `console.log(`, `console.debug(`, `console.warn(` in source files (exclude test files, config files, server-side logging modules)
- PASS: no instances found
- WARN: instances found with file:line list
- Note: `console.error(` in catch blocks is acceptable. Server-side logger wrappers are acceptable. Only flag client-side components and shared code.
- Fix: remove or replace with structured logger

**D2: No debugger statements** — Severity: FAIL
- Grep for `\bdebugger\b` in source files
- PASS: no instances
- FAIL: instances found

**D3: No TODO/FIXME in shipping code** — Severity: WARN
- Grep for `TODO|FIXME|HACK|XXX` in source files (exclude test files and docs)
- PASS: no instances
- WARN: instances found with file:line list. Print each one so the developer can decide if it's blocking.

**D4: No commented-out code blocks** — Severity: WARN
- Grep for patterns suggesting commented-out code: `// import`, `// const `, `// function `, `/* ... */` containing code-like syntax spanning multiple lines
- PASS: no significant commented-out code found
- WARN: instances found

### Category 3: URLs & Environment

**E1: No hardcoded dev URLs** — Severity: FAIL
- Grep for: `localhost`, `127.0.0.1`, `0.0.0.0`, `:3000`, `:8080`, `:5173`, `http://` (non-https) in source files
- Exclude: config files where dev URLs are expected (`.env.local`, `.env.development`, dev server configs), test files, README
- PASS: no dev URLs in production code
- FAIL: hardcoded dev URLs found in source files
- Fix: replace with env var references

**E2: .env files not committed** — Severity: FAIL
- Check `git ls-files` for any `.env` file (not `.env.example`, not `.env.local.example`)
- Specifically check for: `.env`, `.env.local`, `.env.production` in git tracked files
- PASS: no .env files tracked
- FAIL: .env file committed to git
- Fix: remove from git, add to .gitignore

**E3: Required env vars documented** — Severity: WARN
- Grep source code for env var references: `process.env.`, `os.environ`, `os.Getenv`, `env!(`
- Collect all env var names referenced
- Check if `.env.example` or `.env.template` exists and lists them
- PASS: all referenced env vars are documented in example file
- WARN: env vars referenced in code but missing from example file (list the missing ones)
- Note: if no `.env.example` exists at all, WARN with the full list of referenced env vars

**E4: No secrets in source code** — Severity: FAIL
- Grep for patterns: `sk-`, `pk_live`, `pk_test`, `AKIA`, `ghp_`, `gho_`, `Bearer `, `password\s*=\s*["']`, `secret\s*=\s*["']`, `apiKey\s*=\s*["']`
- Exclude: `.env*` files, test fixtures with fake values
- PASS: no secret patterns found
- FAIL: potential secrets in source code

### Category 4: Error Handling & Monitoring

**M1: Error tracking configured** — Severity: WARN
- Grep deps for: `@sentry/`, `sentry`, `bugsnag`, `logrocket`, `rollbar`, `airbrake`, `honeybadger`, `datadog`
- Or grep source for: `Sentry.init`, `bugsnag.start`, `LogRocket.init`
- PASS: error tracking library found and initialized
- WARN: no error tracking detected. "Production errors will go unnoticed."

**M2: Error boundaries (frontend)** — Severity: WARN
- React: Grep for `componentDidCatch`, `ErrorBoundary`, `error.tsx` (Next.js App Router)
- Vue: Grep for `errorCaptured`, `onErrorCaptured`
- PASS: error boundary/handler found
- WARN: no error boundary — unhandled errors will show blank screen
- N/A: no frontend framework

**M3: Custom 404 page** — Severity: WARN
- Next.js: check for `app/not-found.tsx` or `pages/404.tsx`
- Other frameworks: check for 404 route/component
- Static sites: check for `404.html`
- PASS: custom 404 exists
- WARN: no custom 404 — users see default framework error

**M4: Analytics configured** — Severity: WARN
- Grep deps for: `@vercel/analytics`, `@google-analytics`, `ga-4`, `plausible`, `posthog`, `mixpanel`, `amplitude`, `umami`
- Or grep source for: `gtag(`, `analytics.track`, `posthog.capture`
- PASS: analytics library found
- WARN: no analytics detected. "You won't know if anyone uses this."
- Note: this is advisory — some projects intentionally skip analytics

### Category 5: SEO & Social (web projects only)

Skip this entire category if the project is a backend API, CLI tool, or library (no HTML rendering).

**S1: Meta titles on all pages** — Severity: WARN
- Next.js App Router: check for `metadata` export or `generateMetadata` in all `page.tsx` files
- Next.js Pages Router: check for `<Head><title>` in all page components
- Static: check for `<title>` in all HTML files
- PASS: all pages have titles
- WARN: pages missing titles (list them)

**S2: Meta descriptions** — Severity: WARN
- Same approach as S1, check for `description` in metadata
- PASS: all pages have descriptions
- WARN: pages missing descriptions

**S3: OG/Social images** — Severity: WARN
- Check for `openGraph` in metadata, or `<meta property="og:image"` tags
- PASS: OG images configured
- WARN: no OG images — links shared on social media will look plain

**S4: robots.txt exists** — Severity: WARN
- Check for `public/robots.txt` or `app/robots.txt` (Next.js) or equivalent
- PASS: robots.txt found
- WARN: no robots.txt

**S5: Sitemap configured** — Severity: WARN
- Check for `public/sitemap.xml`, `app/sitemap.ts` (Next.js), or sitemap generation in build
- PASS: sitemap found or configured
- WARN: no sitemap

**S6: Favicon exists** — Severity: WARN
- Check for `public/favicon.ico`, `app/favicon.ico`, `app/icon.tsx`, or `<link rel="icon"` in HTML
- PASS: favicon found
- WARN: no favicon — browser tab shows generic icon

### Category 6: Legal & Compliance

Skip if project is a backend API, CLI tool, or library.

**L1: Privacy policy page** — Severity: WARN
- Grep for: `privacy`, `privacy-policy` in file names or route paths
- PASS: privacy policy page/route found
- WARN: no privacy policy detected

**L2: Terms of service page** — Severity: WARN
- Grep for: `terms`, `terms-of-service`, `tos` in file names or route paths
- PASS: terms page found
- WARN: no terms page detected

**L3: Cookie consent (if cookies/analytics used)** — Severity: WARN
- Only check if M4 (analytics) passed or if cookies are set
- Grep for: `cookie-consent`, `CookieBanner`, `cookie-banner`, `gdpr`, `consent`
- PASS: cookie consent mechanism found
- WARN: analytics/cookies used but no consent mechanism
- N/A: no analytics or cookies

### Category 7: Git & Deploy State

**G1: Clean working tree** — Severity: WARN
- Run `git status --porcelain`
- PASS: no uncommitted changes
- WARN: uncommitted changes exist (list them)

**G2: On expected branch** — Severity: WARN
- Check current branch name via `git branch --show-current`
- WARN if on `main` or `master` directly (should deploy from release branch or via CI)
- PASS: on a feature/release branch, or CI handles deployment
- Note: this is advisory — some workflows deploy from main directly

**G3: No merge conflicts** — Severity: FAIL
- Grep for `<<<<<<<`, `=======`, `>>>>>>>` in source files
- PASS: no conflict markers
- FAIL: conflict markers found

**G4: Lockfile committed** — Severity: FAIL
- Check `git ls-files` for: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `go.sum`, `Cargo.lock`
- PASS: lockfile tracked by git
- FAIL: no lockfile committed (builds will be non-deterministic)

## Report

### Scorecard Format

```markdown
# Deploy Readiness — [Project Name]
**Date:** YYYY-MM-DD | **Branch:** [current] | **Stack:** [detected]

## Result: READY / NOT READY / READY WITH WARNINGS

| Category | Pass | Warn | Fail | Status |
|----------|------|------|------|--------|
| Build Health | X | X | X | [OK/WARN/FAIL] |
| Debug Code | X | X | X | [OK/WARN/FAIL] |
| URLs & Environment | X | X | X | [OK/WARN/FAIL] |
| Error Handling | X | X | X | [OK/WARN/FAIL] |
| SEO & Social | X | X | X | [OK/WARN/FAIL] |
| Legal | X | X | X | [OK/WARN/FAIL] |
| Git State | X | X | X | [OK/WARN/FAIL] |

## Blockers (must fix)
[all FAIL items with file:line]

## Warnings (should fix)
[all WARN items with file:line]

## All Clear
[all PASS items]
```

**Overall verdict:**
- **READY** — zero FAILs, zero WARNs
- **READY WITH WARNINGS** — zero FAILs, some WARNs
- **NOT READY** — one or more FAILs

With `--strict`: WARNs count as FAILs → verdict is READY or NOT READY only.

**Print to conversation:** Verdict + scorecard table + blockers + warnings count. Full details in file if `--report`.

## Fix Phase (with --fix flag)

If `--fix` is passed, fix in this order:

1. **FAIL items first:**
   - D2 (debugger): remove debugger statements
   - E1 (dev URLs): replace with env var references where possible
   - E2 (.env committed): remove from git tracking, add to .gitignore
   - E4 (secrets): move to env vars
   - G3 (merge conflicts): cannot auto-fix — report and stop
   - G4 (lockfile): run `npm install` / equivalent to generate lockfile

2. **WARN items (quick fixes only):**
   - D1 (console.log): remove from client-side code
   - D3 (TODO/FIXME): cannot auto-fix — just list them
   - S4 (robots.txt): create basic `robots.txt` with `User-agent: * Allow: /`
   - S6 (favicon): cannot auto-fix without assets

3. **After fixes:**
   - Run build to verify nothing broke
   - Re-run the audit to show updated scorecard

## Anti-Hallucination Rules

- **Build commands must be detected, not assumed.** If no `build` script found, do NOT guess `npm run build`. Report "no build command detected."
- **Every finding must have file:line evidence** from Grep/Glob/Read. No fabricated paths.
- **Do not fabricate analytics/error tracking.** If Grep for Sentry/etc. returns nothing, report WARN — do NOT assume it's configured elsewhere.
- **Do not assume deployment target.** Check for config files. If none found, report "deployment target unknown."
- **Git commands are real.** Run `git status`, `git branch`, `git ls-files` — report actual output, not assumptions.
- **SEO checks apply only to web frontends.** If the project is an API, CLI, or library, skip Categories 5 and 6 entirely. Detect this by checking: does the project render HTML? (Has `pages/`, `app/`, `index.html`, templates)
- **D1 exceptions are real.** `console.error` in catch blocks and server-side logger modules are acceptable. Do NOT flag these. Only flag `console.log` and `console.debug` in client components.
