---
name: audit-forms
description: Audit and harden all forms in a project against spam, bots, and security vulnerabilities. Detects tech stack, runs a 38-point security checklist, and optionally auto-fixes issues. Use when asked to secure forms, add spam protection, audit form security, or harden forms.
user-invocable: true
argument-hint: "[--fix] [--scope=<form-name>] [--report] [--client-only] [--server-only]"
---

# Harden Forms: Security Audit + Auto-Fix

Comprehensive form security audit with 38-point checklist across 4 categories. Detects tech stack automatically and applies framework-specific fixes.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — auto-fix all critical/high/medium issues after audit
  - `--scope=<name>` — audit only a specific form (matched by component name, route, or page slug)
  - `--report` — save full report (see report location logic below)
  - `--client-only` — run only client-side checks (C1-C12)
  - `--server-only` — run only server-side checks (S1-S14)
  - No flags = audit all forms, report only, no auto-fix

### Flag Precedence

`--client-only` and `--server-only` are mutually exclusive. If both passed, use `--server-only` (server-side issues are higher severity).

### Report Location Logic

When `--report` is used:
1. If `_local/reports/` exists -> save there
2. Else if `_local/` exists -> create `_local/reports/` and save there
3. Else -> save to project root as `form-security-audit-<YYYY-MM-DD>.md` (warn user it's tracked by git)

## Execution Strategy

**For projects with 1-3 forms:** Run all checks in the main conversation (no agents needed).
**For projects with 4+ forms:** Spawn one Agent per form to parallelize. Each agent gets the form's file paths and the 38-point checklist. Collect results and aggregate.

## Phase 1: Stack Detection & Form Discovery

### 1.1 Detect Tech Stack

Read project files to identify the framework. Use these concrete checks:

| Check | How |
|-------|-----|
| Framework | Read `package.json` deps for: `next`, `express`, `fastify`, `hono`, `nuxt`, `@angular/core`. Read `requirements.txt`/`pyproject.toml` for `django`, `flask`. Read `Gemfile` for `rails`. |
| Test framework | Check `package.json` devDeps for: `vitest`, `jest`, `mocha`. Check Python for `pytest`. |
| CSS approach | Check for `tailwindcss` in deps, `.module.css` files, `styled-components` in deps. |
| Form libraries | Check deps for: `react-hook-form`, `formik`, `vee-validate`, `@tanstack/react-form`. |
| Build/lint commands | Read `package.json` scripts for `build`, `lint`, `test`. Note exact commands. |

If no framework detected, assume Static HTML / Vanilla JS.

### 1.2 Find All Forms

Search the codebase using these specific patterns:

```
# Client-side forms
Glob: **/*.{tsx,jsx,vue,html,svelte}
Grep: "<form[\s>]|<Form[\s>]|onSubmit=|handleSubmit|useForm\(|<Formik|action=\{|method=[\"']POST"

# Server-side endpoints
Glob: **/api/**/*.{ts,js,py,rb}
Grep: "export.*(async\s+)?function\s+POST|app\.post\(|fastify\.post\(|router\.post\(|@app\.route.*POST|def\s+create"

# Next.js Server Actions
Grep: "use server" in **/*.{ts,tsx} files (check if file contains form-handling logic)

# Form submission calls (to link client to server)
Grep: "fetch\(.*(POST|post)|axios\.post\(|\.submit\("
```

**If zero forms found:** Print "No forms found in the project. Nothing to audit." and STOP. Do not continue to Phase 2.

### 1.3 Classify Each Form

For each form found, determine:
- **Client component** — file path, line number
- **API route** — where it submits to. Trace `fetch(` or `action=` to find the endpoint. If can't determine, note "unknown endpoint."
- **Context** — public (unauthenticated) or authenticated. Check if the form/page is behind auth middleware or a login-protected route. If unclear, assume public (higher severity).
- **Has file uploads** — Grep the form component for `type="file"`, `multipart/form-data`, `new FormData`
- **Existing protections** — note any found (honeypot, CAPTCHA, rate limiting, validation)

Present summary table:
```
Found N form(s):

| Form | Client | API Route | Context | Uploads | Existing Protections |
|------|--------|-----------|---------|---------|---------------------|
```

## Phase 2: 38-Point Security Audit

Run all checks against each form. Mark each as **PASS**, **FAIL**, or **N/A**.

### Grade Calculation

Grade is based on APPLICABLE checks only (exclude N/A):
- Count PASS checks. Count total applicable checks (38 minus N/A count).
- Score = PASS count.
- Adjusted total = 38 minus N/A count.
- Grade thresholds (as percentage of adjusted total): A (90%+), B (80%+), C (65%+), D (50%+), F (<50%)

Example: form with no uploads (C11, S11 = N/A) has adjusted total of 36. Score 33/36 = 92% = A.

### Context-Aware Severity

Checks marked with "(public)" have their severity reduced by one level for authenticated-only forms. Specifically: C1, C2, C3, C10, S3, S4, S5, S6.

### Client-Side Protections (C1-C12)

**C1: Honeypot Field** — Severity: HIGH (public)
- Search in the form component for: hidden input with `aria-hidden`, off-screen positioning (`position: absolute`, `left: -9999`, `opacity: 0` + `height: 0`), `tabIndex={-1}`
- PASS: hidden field exists, rendered but invisible, has `autoComplete="off"`
- FAIL: no honeypot found in the form component
- Fix: Add hidden div with off-screen CSS. Use a legitimate-sounding field name (`website`, `url`, `company_url`) — not obvious names like `honeypot` or `trap`.

**C2: Timing Check** — Severity: HIGH (public)
- Search for: `useRef(Date.now())`, `mountedAt`, `startTime`, timestamp tracking on component mount
- PASS: mount time recorded, elapsed time included in submission payload
- FAIL: no timing tracked
- Fix: Add `useRef(0)` + `useEffect(() => { ref.current = Date.now() }, [])`, include elapsed ms in POST body

**C3: Interaction Tracking** — Severity: MEDIUM (public)
- Search for: `addEventListener("mousemove"`, `addEventListener("keydown"`, `addEventListener("touchstart"`, interaction counter
- PASS: at least 2 event types tracked, count sent with submission
- FAIL: no interaction tracking
- Fix: Add ref counter, passive event listeners on form element

**C4: Client-Side Validation** — Severity: HIGH
- Search for: validation function, required field checks before submit, form library validation (react-hook-form `register({ required })`, Formik `validationSchema`)
- PASS: validation runs before submission, errors shown per field
- FAIL: no validation or only HTML5 `required` attribute without JS validation
- Fix: Add validation function checking all required fields with inline error display

**C5: Email Validation** — Severity: MEDIUM
- Search for: email regex, email format check in validation
- PASS: rejects obviously invalid emails (no `@`, no domain, 1-char TLD)
- FAIL: no email validation or only checks for `@`
- Fix: Add practical email regex. No client-side regex is RFC-perfect — the goal is catching typos.

**C6: Phone Format Validation** — Severity: MEDIUM
- Search for: phone regex or phone validation in the form
- PASS: validates input contains primarily digits
- FAIL: no phone validation or accepts any string
- N/A: form has no phone field
- Fix: Validate based on form's stated format requirements

**C7: Field maxLength Attributes** — Severity: LOW
- Search for: `maxLength` on input/textarea elements
- PASS: all text inputs have maxLength
- FAIL: missing maxLength on any text input
- Fix: Add maxLength to all text inputs/textareas

**C8: Submit Button Disabled During Submission** — Severity: LOW
- Search for: `disabled={` on submit button, `submitting` or `isSubmitting` state, `formState.isSubmitting`
- PASS: button disabled while request is in flight
- FAIL: button stays enabled during submission
- Fix: Add submitting state, set true before fetch, false in finally block

**C9: Loading/Progress Indicator** — Severity: LOW
- Search for: spinner, "Submitting..." text, loading state conditional rendering during submission
- PASS: visual feedback shown while submitting
- FAIL: no indication of submission in progress
- Fix: Add spinner/text in button during submission

**C10: CAPTCHA Integration** — Severity: HIGH (public), N/A for authenticated forms
- Search for: `reCAPTCHA`, `hCaptcha`, `Turnstile`, `grecaptcha`, `@hcaptcha`, `cf-turnstile`
- PASS: CAPTCHA token generated client-side and sent with submission
- FAIL: no CAPTCHA on a public-facing form
- N/A: form is authenticated-only
- Fix: Add invisible CAPTCHA (Turnstile or reCAPTCHA v3)

**C11: File Upload Validation** — Severity: CRITICAL
- N/A if form has no file uploads
- Search for: `accept=` attribute on file input, client-side size/type checks
- PASS: file input has `accept` attribute and client checks file size
- FAIL: unrestricted file input
- Fix: Add `accept` whitelist, check `file.size < MAX_SIZE` before submission

**C12: Validation Error Accessibility** — Severity: MEDIUM
- Search for: `aria-live`, `role="alert"` on error message containers
- PASS: error messages are announced to screen readers
- FAIL: errors appear visually but not announced
- Fix: Add `role="alert"` to error message containers

### Server-Side Protections (S1-S14)

**S1: CSRF Check** — Severity: CRITICAL
- Search the API route for: `origin` header check, CSRF token validation, framework CSRF middleware
- PASS: origin/host match verified, or framework CSRF protection active
- FAIL: no CSRF protection on POST endpoint
- Fix: Add origin/host header comparison, reject on mismatch

**S2: Rate Limiting** — Severity: HIGH
- Search for: rate limiter (in-memory Map, Redis, `express-rate-limit`, `django-ratelimit`, WAF config reference)
- PASS: rate limiting per IP/fingerprint
- FAIL: no rate limiting
- Fix: Add rate limiter. Note: in-memory rate limiters reset on serverless cold starts.

**S3: Honeypot Server Validation** — Severity: HIGH (public)
- Search API route for: check on honeypot field value
- PASS: non-empty honeypot returns silent fake success `{ success: true }`
- FAIL: honeypot not checked server-side, or returns error (reveals detection to bot)
- Fix: If honeypot field truthy, return `{ success: true }` immediately

**S4: Timing Server Validation** — Severity: MEDIUM (public)
- Search for: elapsed time check in API route
- PASS: submission < minimum time threshold returns silent success
- FAIL: timing not checked server-side
- Fix: Check elapsed time, return silent success if too fast

**S5: Interaction Count Validation** — Severity: MEDIUM (public)
- Search for: interaction count check in API route
- PASS: interaction count < threshold returns silent success
- FAIL: not checked
- Fix: Check count, return silent success if too low

**S6: Gibberish Detection** — Severity: MEDIUM (public)
- Search for: vowel ratio check, consonant run detection, gibberish scoring
- PASS: gibberish detected and silently rejected
- FAIL: no content quality check
- Fix: Add scoring function. IMPORTANT: short names (< 8 chars) skip vowel ratio to avoid false positives on names like "Schmidt", "Schwartz".

**S7: Server-Side Field Validation** — Severity: HIGH
- Search for: required field checks, type/format validation in API route
- PASS: all fields validated server-side (mirrors client validation)
- FAIL: server accepts any payload without validation
- Fix: Add validation function checking presence, type, and format

**S8: Server-Side Length Limits** — Severity: MEDIUM
- Search for: `.length` checks, `.max()` validation, string length limits in API route
- PASS: all text fields have server-enforced length limits
- FAIL: no length limits on server
- Fix: Add per-field length checks

**S9: Silent Bot Rejection** — Severity: MEDIUM
- Check that honeypot/timing/interaction/gibberish failures return `{ success: true }` (200 OK), NOT error codes
- PASS: bot-detected submissions return fake success
- FAIL: bot detection returns 400/403 (reveals detection to bot)
- Fix: All spam detection responses should return `{ success: true }`

**S10: Error Messages Don't Expose Internals** — Severity: HIGH
- Search API route catch blocks for: stack traces, file paths, SQL errors, API keys, internal URLs in responses
- PASS: all errors return generic messages to client
- FAIL: errors expose internal details
- Fix: Return generic messages, log details server-side only

**S11: File Upload Server Validation** — Severity: CRITICAL
- N/A if no file uploads
- Search for: MIME type check, file size limit, filename sanitization in API route
- PASS: server validates file type (magic bytes), enforces size limit, sanitizes filename
- FAIL: server accepts any file
- Fix: Validate MIME type, enforce max size, sanitize filename, store outside web root

**S12: Replay Prevention** — Severity: MEDIUM
- Search for: idempotency key, nonce, submission deduplication
- PASS: duplicate submissions detected/rejected
- FAIL: same submission can be replayed
- Fix: Add submission fingerprint to rate limiter

**S13: Security Logging** — Severity: MEDIUM
- Search for: logging of suspicious submissions (rate-limited, spam-detected, validation-failed)
- PASS: suspicious submissions logged with IP, timestamp, reason
- FAIL: no logging
- Fix: Add structured logging for security events

**S14: Log Injection Prevention** — Severity: LOW
- Search for: raw user input in log statements without sanitization
- PASS: logged values truncated/sanitized
- FAIL: raw user input in logs
- Fix: Truncate to 100 chars, strip newlines and control characters

### Infrastructure (I1-I8)

**I1: CSP Headers for External Scripts** — Severity: CRITICAL
- Search config for Content-Security-Policy
- Check that `script-src`, `connect-src`, `frame-src` include domains of form's external dependencies (CAPTCHA provider)
- PASS: CSP includes all required external domains
- FAIL: CSP blocks form dependencies (CAPTCHA silently fails!)
- N/A: no external scripts used by forms
- Fix: Add required domains to CSP directives

**I2: Cookie Security** — Severity: MEDIUM
- Search for `cookies.set` or `Set-Cookie` in form-related code
- Check for `httpOnly`, `secure`, `sameSite` flags
- PASS: all cookie flags set correctly
- FAIL: missing flags
- N/A: no cookies set by form endpoints
- Fix: Add missing security flags

**I3: No Secrets in Client Bundle** — Severity: CRITICAL
- Search client-side form components for: `NEXT_PUBLIC_` env vars, `VITE_` env vars, hardcoded API keys
- PASS: no secrets in client code. Note: CAPTCHA SITE keys are public by design — NOT a finding.
- FAIL: API secrets or private keys in client bundle
- Fix: Move to server-only env vars

**I4: CAPTCHA Badge Handling** — Severity: LOW
- N/A if no CAPTCHA used
- Search for: `.grecaptcha-badge { visibility: hidden }` or equivalent
- PASS: badge hidden AND text attribution present (required by Google TOS)
- FAIL: badge visible, or hidden without attribution
- Fix: Add CSS to hide badge, add attribution text

**I5: Shared Validation (Client <-> Server)** — Severity: HIGH
- Check if validation regex/constants are defined separately in client and server files
- PASS: single shared module imported by both
- FAIL: validation duplicated across files (drift risk)
- Fix: Extract to shared validation module

**I6: No Hardcoded Duplicates** — Severity: MEDIUM
- Search for same string/number constant in 2+ files related to the form
- PASS: constants defined once and imported
- FAIL: duplicated values
- Fix: Extract to shared constants

**I7: dangerouslySetInnerHTML in Form Context** — Severity: HIGH
- Search form components and their parents for `dangerouslySetInnerHTML`
- PASS: not used, or only renders static developer-controlled content
- FAIL: renders external/user content without sanitization
- N/A: no `dangerouslySetInnerHTML` found
- Fix: Add DOMPurify sanitization or convert to structured data

**I8: SRI on External Scripts** — Severity: MEDIUM
- Search for external `<script>` or `<link>` tags loaded by form components
- PASS: external scripts have `integrity` attribute, OR are from dynamic CDNs (Google reCAPTCHA, Google Fonts) where SRI is infeasible
- FAIL: static external scripts without SRI
- N/A: no external scripts
- Fix: Generate SRI hash and add `integrity` + `crossOrigin="anonymous"`

### Testing (T1-T4)

**T1: Spam Detection Tests** — Severity: HIGH
- Search test files for: honeypot, timing, interaction, gibberish test coverage
- PASS: tests for each spam layer with positive and negative cases
- FAIL: no spam protection tests
- Fix: Generate test file covering all spam signals

**T2: Field Validation Tests** — Severity: HIGH
- Search for: test coverage of email, phone, required fields, length limits
- PASS: tests cover valid and invalid inputs
- FAIL: no validation tests
- Fix: Generate test cases for all validated fields

**T3: Config/API Validation Tests** — Severity: MEDIUM
- Search for: tests validating form config against external API (for forms submitting to third-party services)
- PASS: tests verify field names/IDs match live API
- FAIL: no config validation tests
- N/A: form doesn't submit to external services
- Fix: Generate test with live fetch + comparison, skip gracefully when offline

**T4: Gibberish Detection Tests** — Severity: MEDIUM
- Search for: gibberish scoring tests with known spam AND known valid names
- PASS: tests verify spam caught AND real names (including international: Schmidt, O'Brien, Jean-Pierre) pass
- FAIL: no gibberish tests
- N/A: no gibberish detection implemented
- Fix: Generate test with 10+ spam strings and 10+ real names

## Phase 3: Report

Present results as a scorecard:

```markdown
## Form Security Audit — [Project Name]
### Stack: [Framework] | Forms: [count] | Date: [YYYY-MM-DD]

### Summary
| Form | Score | Total | Grade | Critical | High | Medium | Low |
|------|-------|-------|-------|----------|------|--------|-----|
| Contact | 33 | 36 | A (92%) | 0 | 0 | 2 | 1 |

### [Form Name] — Detailed Results
| # | Check | Status | Severity | Details |
|---|-------|--------|----------|---------|
| C1 | Honeypot | PASS | High | Hidden field "website" at line 248 |
| C11 | File Upload | N/A | — | No file uploads |
| S1 | CSRF | FAIL | Critical | No origin check in /api/contact |

### Priority Actions
1. [CRITICAL] [Form] — description (file:line)
2. [HIGH] [Form] — description (file:line)
```

**Print to conversation:** Summary table + Priority Actions. Full detailed results go to file if `--report` is set.

## Phase 4: Fix (with --fix flag)

Apply fixes in dependency order:
1. **Shared validation module** — create if missing (other fixes depend on it)
2. **Server-side protections** — API route fixes (CSRF, rate limit, validation, spam detection)
3. **Client-side protections** — form component fixes (honeypot, timing, interaction, CAPTCHA)
4. **Infrastructure** — CSP headers, cookie flags, SRI
5. **Tests** — generate test file covering all protection layers

After all fixes:
- Run lint command (if detected in stack detection). If no lint configured, skip.
- Run build command (if detected). If no build configured, skip.
- Run tests (if detected). If tests fail, fix the failures.
- If no build/lint/test commands detected, note: "No build/test commands found — manual verification recommended."

Present summary of what was fixed vs what remains.

## Framework-Specific Fix Patterns

### Next.js (App Router)
- API routes: `src/app/api/<name>/route.ts` with `export async function POST`
- Client components: `"use client"` directive
- Server Actions: `"use server"` + `async function` (treat like API route for server-side checks)
- CAPTCHA: `next/script` with `strategy="lazyOnload"`
- CSP: `next.config.mjs` -> `headers()` function
- Tests: vitest or jest in `src/__tests__/` or `__tests__/`

### Next.js (Pages Router)
- API routes: `pages/api/<name>.ts` with `export default handler`
- CSP: `next.config.js` headers
- Same client-side patterns

### Express / Fastify / Hono
- Rate limiting: `express-rate-limit` or framework equivalent
- CSRF: manual origin check (`csurf` is deprecated — use double-submit cookie or `csrf-csrf`)
- Validation: `express-validator`, Joi, or Zod
- Client-side: framework-agnostic

### Django
- CSRF: built-in `{% csrf_token %}` + `CsrfViewMiddleware` (verify enabled, not `@csrf_exempt`)
- Rate limiting: `django-ratelimit` decorator
- Validation: Django forms or DRF serializers

### Static HTML / Vanilla JS
- Client-side protections only
- Server-side requires serverless function (Lambda, Netlify Functions, Cloudflare Workers)
- Plain DOM API for client-side

## Anti-Hallucination Rules

- CAPTCHA SITE keys are public by design — NEVER flag as a secret
- Silent bot rejection (fake 200 success) is INTENTIONAL — NEVER flag as "missing error handling"
- In-memory rate limiters reset on serverless cold starts — note as limitation, recommend WAF as primary
- `SameSite=Strict` is defense-in-depth for CSRF, NOT standalone protection
- Third-party embedded forms (Typeform, HubSpot) are inventoried but NOT auditable — note in report, do NOT fabricate check results
- If a form's API route cannot be found/traced, report "API route: unknown — could not trace submission endpoint" — do NOT guess the endpoint
- If a check's search returns no results, report FAIL (not found) — do NOT assume protection exists without evidence
- **Never invent names.** Do not fabricate hook names (`useFormValidation`), component names, utility names, or file paths. If recommending extraction, say "validation logic duplicated in src/A.tsx:40 and src/B.tsx:60" — do NOT say "extract useSharedValidation hook."
- **Every file path in findings must be real** — confirmed via Grep/Glob/Read. No fabricated paths or line numbers.
