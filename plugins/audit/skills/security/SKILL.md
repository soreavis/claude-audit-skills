---
name: audit-security
description: Full attack surface audit covering 33 security vectors (OWASP, auth, API, client-side, AI). Reports findings with verdicts per vector. Optionally fixes all findings and verifies. Works on any web project.
user-invocable: true
argument-hint: "[--fix] [--audit-only] [--scope=<path>] [--report] [--skip-deps]"
---

# Security Audit: 33-Vector Attack Surface

Audit all 33 security vectors, report findings with per-vector verdicts, and optionally fix. Works on any web project (Next.js, React, Express, Django, Go, etc.).

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — fix all findings after audit
  - `--audit-only` — report findings without fixing (this is the DEFAULT if no flags given)
  - `--scope=<path>` — limit to specific directory (default: entire project)
  - `--report` — save full report to `_local/reports/security-audit-<YYYY-MM-DD>.md`
  - `--skip-deps` — skip dependency vulnerability check (vector 27)

**Default behavior: audit-only.** Fixes are opt-in via `--fix`.

## Setup

### 1. Detect Tech Stack

Read project files to identify the stack. This determines which vectors are relevant and which tools/commands to use.

| Check | How | Records |
|-------|-----|---------|
| Language | `package.json` → Node/TS, `requirements.txt`/`pyproject.toml` → Python, `go.mod` → Go, `Cargo.toml` → Rust, `Gemfile` → Ruby | Primary language |
| Framework | `next` → Next.js, `express` → Express, `fastify` → Fastify, `hono` → Hono, `django` → Django, `flask` → Flask, `gin` → Gin | Framework name + version |
| Database | Grep for `prisma`, `mongoose`, `sequelize`, `typeorm`, `pg`, `mysql2`, `sqlite3`, `redis` in deps | DB type or "none" |
| Auth | Grep for `next-auth`, `passport`, `clerk`, `auth0`, `supabase`, `firebase` in deps | Auth library or "custom" or "none" |
| Has API routes | Glob for `**/api/**/*.{ts,js,py,rb,go}` or server action files | true/false |
| Has AI features | Grep for `openai`, `anthropic`, `@ai-sdk`, `langchain` in deps | true/false |

### 2. Detect Build/Lint/Test Commands

- Node: read `package.json` scripts for `build`, `lint`, `test`, `typecheck`
- Python: check for `pytest`, `ruff`, `mypy` in deps
- Go: `go build ./...`, `go vet ./...`, `go test ./...`
- Rust: `cargo build`, `cargo clippy`, `cargo test`

Record exact commands. If none found, note "no build/lint configured."

### 3. Determine Vector Relevance

Mark each of the 33 vectors as RELEVANT or N/A based on detected stack:

- Vectors requiring SQL/NoSQL → N/A if no database detected
- Vectors requiring auth → N/A if no auth system
- AI vectors (31-33) → N/A if no AI features
- XXE (10) → N/A if no XML parsing libraries
- Dependency confusion (28) → N/A if no private packages

**N/A vectors still appear in the final report** but with verdict "N/A — [reason]".

## Standardized Finding Format

Every finding uses this format:

```
### Vector N: [Name] — [VERDICT]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Verdict:** Protected / Partially Protected / Not Protected / N/A
- **Evidence:** [file:line and what was found, or "no instances found"]
- **Current protection:** [what's already in place, if anything]
- **Gap:** [what's missing]
- **Fix:** [concrete remediation steps]
```

VERDICT rules:
- **Protected** — all checks pass with evidence
- **Partially Protected** — some protections exist but gaps remain
- **Not Protected** — no protections found
- **N/A** — vector not relevant to this stack

**CRITICAL RULE:** Only assign verdicts based on evidence found via Grep/Glob/Read. If you cannot verify a vector from the codebase (e.g., DNS records, WAF config, infrastructure settings), report it as: "Cannot verify from code — requires infrastructure review" and do NOT assign Protected/Not Protected.

## Phase 1: Launch Four Parallel Audit Agents

Launch ALL four agents concurrently using the Agent tool. Pass each agent: project path, scope, detected stack, and relevant vector numbers.

### Agent 1: Web Application Attack Surface (Vectors 1-10)

**Agent tool prompt:**

> Audit web application security vectors in the project at [cwd]. Scope: [scope]. Stack: [stack summary].
>
> For each vector below, search the codebase using Grep/Glob and report findings using this format:
> `### Vector N: Name — [Protected|Partially Protected|Not Protected|N/A]` with Severity, Verdict, Evidence, Current protection, Gap, and Fix fields.
>
> **Vector 1 — XSS:**
> - Grep for: `dangerouslySetInnerHTML`, `innerHTML\s*=`, `v-html`, `\[innerHTML\]`
> - For each instance: trace the data source. Static/hardcoded = Protected. External data with sanitization (DOMPurify, sanitize-html) = Protected. External data WITHOUT sanitization = Not Protected (CRITICAL).
> - Search config files for Content-Security-Policy header. Check for `unsafe-inline`, `unsafe-eval` (these weaken CSP).
> - If framework auto-escapes (React JSX, Vue templates, Angular) and no bypass found = Protected.
>
> **Vector 2 — CSRF:**
> - Find all POST/PUT/DELETE endpoints: Grep for `export.*POST`, `app.post`, `router.post`, `@app.route.*POST`
> - For each: check if it validates Origin header (`request.headers.get("origin")`) or uses CSRF tokens
> - Check cookies for `sameSite` attribute
> - Django: check `CsrfViewMiddleware` is in MIDDLEWARE and not bypassed (`@csrf_exempt`)
>
> **Vector 3 — Clickjacking:**
> - Search config for `X-Frame-Options` and `frame-ancestors` in CSP
> - If both missing = Not Protected
>
> **Vector 4 — SQL/NoSQL Injection:** [SKIP if no database detected]
> - Grep for string concatenation in queries: `query(\``, `query("` + `+`, `.raw(`, `$where`
> - Grep for parameterized queries: `query($1)`, `?` placeholders, ORM methods
> - If only ORM with no `.raw()` usage = Protected
>
> **Vector 5 — Command Injection:**
> - Grep for: `child_process`, `exec(`, `execSync`, `spawn(`, `system(`, `subprocess`, `os.system`
> - For each: check if user input flows into the command. Shell commands with hardcoded strings = LOW.
>
> **Vector 6 — SSRF:**
> - Find server-side fetch/request calls that accept URLs from user input (query params, request body)
> - Check for IP/hostname blocklists
> - If no server-side URL fetching from user input exists = N/A
>
> **Vector 7 — Open Redirect:**
> - Grep for `redirect(`, `res.redirect(`, `location.href =` where URL comes from user input
> - Check for hostname validation or allowlist
>
> **Vector 8 — Path Traversal:**
> - Grep for `fs.readFile`, `fs.createReadStream`, `open(`, `Path.join` with user input
> - Check for `../` sanitization
> - If no file operations with user input = N/A
>
> **Vector 9 — HTTP Parameter Pollution:**
> - Check if request handling validates payload schema (Zod, Joi, Yup, class-validator)
> - If using typed schema validation = Protected
>
> **Vector 10 — XXE:** [SKIP if no XML parsing]
> - Grep for XML parsing: `xml2js`, `DOMParser`, `lxml`, `xml.etree`
> - Check if external entity processing is disabled
> - If no XML parsing = N/A
>
> End with findings summary block: `---FINDINGS-SUMMARY---` with critical/high/medium/low counts.

### Agent 2: Authentication & Session Security (Vectors 11-15)

**Agent tool prompt:**

> Audit authentication and session security in the project at [cwd]. Scope: [scope]. Stack: [stack summary]. Auth system: [detected auth library or "custom" or "none"].
>
> If no auth system detected: report all 5 vectors as N/A with note "No authentication system found." and STOP.
>
> For each vector, search the codebase and report findings.
>
> **Vector 11 — Brute Force:**
> - Find auth endpoints: Grep for login, register, password-reset, invite routes
> - For each: check for rate limiting (in-memory Map, Redis, express-rate-limit, django-ratelimit)
> - Check if rate limiter fails closed (returns error when unavailable, not silently passes)
>
> **Vector 12 — Session Fixation:**
> - Check if sessions are regenerated after login (Grep for `regenerate`, `rotate`, new session creation post-auth)
> - Check for session IDs in URLs
>
> **Vector 13 — Session Hijacking:**
> - Find all cookie-setting code. Check flags: `httpOnly`, `secure`, `sameSite`
> - Grep for auth tokens in `localStorage` (should be httpOnly cookies instead)
> - Grep for session data in URL parameters
>
> **Vector 14 — Credential Stuffing:**
> - Check for account-level rate limiting (not just IP-based)
> - Check for MFA support
> - Check password complexity requirements
>
> **Vector 15 — Broken Authentication:**
> - Check middleware/guard coverage: find the auth middleware, then check if all routes are covered (look for unprotected routes)
> - Grep for `===` comparison on secrets (should use `timingSafeEqual` or `hmac.compare_digest`)
> - Grep for `Math.random` in auth context (should use `crypto.randomBytes`)
> - Grep for secrets in URL query params
>
> End with findings summary block.

### Agent 3: API & Infrastructure Security (Vectors 16-25)

**Agent tool prompt:**

> Audit API and infrastructure security in the project at [cwd]. Scope: [scope]. Stack: [stack summary].
>
> For each vector, search the codebase and report findings. Vectors that require infrastructure access (DNS, WAF, CDN config) should be reported as "Cannot verify from code — requires infrastructure review."
>
> **Vector 16 — API Rate Limiting:**
> - Find all public API endpoints. Check for rate limiting on each.
> - Flag expensive operations (AI calls, file uploads, email sending) without strict limits.
>
> **Vector 17 — Mass Assignment:**
> - Grep for `Object.assign(`, `...req.body`, `Object.fromEntries(` spreading user input into objects without field allowlisting
> - Check for Zod/Joi schema parsing (`.parse()` or `.validate()`) which provides allowlisting = Protected
>
> **Vector 18 — Broken Object-Level Authorization:**
> - Check CRUD endpoints: do they verify the requesting user owns the resource?
> - Look for resource access by ID without ownership check
>
> **Vector 19 — Excessive Data Exposure:**
> - Grep for `catch` blocks that return `error.message` or `error.stack` to the client
> - Check API error responses for internal details
>
> **Vector 20 — DoS:**
> - Check for request body size limits on POST endpoints
> - Grep for regex patterns and check for catastrophic backtracking (nested quantifiers: `(a+)+`, `(a|b)*c`)
> - Check for timeouts on external API calls (`AbortSignal.timeout`, `signal`, request timeout config)
>
> **Vector 21 — DNS Rebinding:** Cannot verify from code. Report: "Requires infrastructure review — check DNS resolver and SSRF protections for TOCTOU."
>
> **Vector 22 — HTTP Request Smuggling:** If using standard framework (Express, Next.js, Django, etc.) = Protected (framework handles parsing). Only flag if manual HTTP parsing found.
>
> **Vector 23 — Man-in-the-Middle:**
> - Check for HSTS header
> - Grep for `http://` in fetch/request calls to external APIs (should be `https://`)
> - Check cookie `secure` flag
>
> **Vector 24 — Subdomain Takeover:** Cannot verify from code. Report: "Requires DNS audit — check CNAME records for dangling references."
>
> **Vector 25 — Security Headers:**
> - Search all config/middleware for each header: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
> - For each: report found (with value) or missing
>
> End with findings summary block.

### Agent 4: Client-Side & AI Security (Vectors 26-33)

**Agent tool prompt:**

> Audit client-side and AI security in the project at [cwd]. Scope: [scope]. Stack: [stack summary]. Has AI features: [true/false].
>
> **Vector 26 — Prototype Pollution:**
> - Grep for `Object.assign(`, `_.merge(`, `deepMerge(` where first argument receives user data
> - Grep for `JSON.parse(` on user-controlled strings without schema validation after
> - Check for `__proto__` or `constructor` sanitization
>
> **Vector 27 — Supply Chain Attack:**
> - Check if lockfile exists: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `go.sum`, `Cargo.lock`
> - Grep for external `<script src="http` or `<link href="http` without `integrity=` attribute
> - Note: recommend running `npm audit` / `pip-audit` / `cargo audit` but do NOT run it (may require network). Report as "Recommendation: run [command]."
> - If `--skip-deps` flag was passed, skip this vector entirely and mark N/A.
>
> **Vector 28 — Dependency Confusion:**
> - Check for `.npmrc` or `.yarnrc` scoped registry config
> - Check if private package names (from `package.json` name field) could conflict with public registry
> - If package name is scoped (`@company/name`) = lower risk
> - If no private packages = N/A
>
> **Vector 29 — Browser Cache Poisoning:**
> - Check Cache-Control headers on API endpoints (sensitive endpoints should use `no-store`)
> - Check for `Vary` headers on personalized responses
>
> **Vector 30 — Tabnabbing:**
> - Grep for `target="_blank"` or `target='_blank'` — check for `rel="noopener noreferrer"` (or `rel="noopener"` at minimum)
> - React 19+ and modern browsers auto-add noopener, so this is LOW in modern stacks
>
> **Vectors 31-33 — AI Security:** [SKIP ALL if no AI features detected — report as N/A]
>
> **Vector 31 — Prompt Injection:**
> - Grep for AI SDK calls: `openai.chat`, `anthropic.messages`, `generateText`, `streamText`
> - For each: trace if user input is interpolated into the prompt. Check for sanitization (strip control chars, limit length).
>
> **Vector 32 — AI Data Poisoning:**
> - Check if AI responses are cached (in DB, Redis, localStorage). If cached: check for schema validation on read.
>
> **Vector 33 — Model Extraction:**
> - Check if AI error responses leak model names or versions
> - Grep for model name strings in client-side code
>
> End with findings summary block.

## Phase 2: Aggregate & Prioritize

After all four agents return:

1. **Handle failures.** If an agent failed, mark its vectors as "AGENT FAILED — could not assess." Still produce the report with available data.

2. **Build the 33-vector table.** For each vector 1-33, extract the verdict from the agent results. If a vector wasn't covered (agent failure), mark it "Unassessed."

3. **Count verdicts:**
   - Protected: vectors with "Protected" verdict
   - Partially Protected: vectors with "Partially Protected"
   - Not Protected: vectors with "Not Protected"
   - N/A: vectors not relevant to this stack
   - Unassessed: agent failures
   - Infrastructure-only: vectors requiring infrastructure review

4. **Produce report:**

```markdown
# Security Audit Report — [Project Name]
**Date:** YYYY-MM-DD | **Scope:** [path] | **Stack:** [detected]

## Scorecard: X/33 vectors assessed, Y protected

| # | Vector | Verdict | Severity | Evidence |
|---|--------|---------|----------|----------|
| 1 | XSS | Protected | — | CSP strict, no dangerouslySetInnerHTML |
| 2 | CSRF | Not Protected | CRITICAL | No origin check on POST /api/contact |
| ... | ... | ... | ... | ... |
| 33 | Model Extraction | N/A | — | No AI features |

## Findings by Severity

### Critical
[all critical findings with file:line]

### High
[all high findings]

### Medium / Low
[grouped]

## Infrastructure Review Needed
[vectors that cannot be verified from code]

## Recommendations
[dep audit commands to run, WAF config suggestions, etc.]
```

5. **Print to conversation:** Scorecard table + critical/high findings. Not the full report.

6. **Save report** if `--report` flag is set.

## Phase 3: Fix (only with --fix flag)

If `--fix` was passed:

### Fix Order:
1. **Critical** — fix immediately
2. **High** — fix next
3. **Medium** — fix all
4. **Low** — quick wins only (< 5 lines)

### Framework-Adaptive Fixes

Do NOT blindly apply TypeScript/Next.js patterns. Match fixes to the detected stack:

**For Node.js/TypeScript projects:** use the patterns below.
**For Python/Django projects:** use Django equivalents (middleware, decorators, Django forms).
**For Go projects:** use Go standard library equivalents.
**For other stacks:** read framework docs and apply idiomatic fixes.

### Common Fix Patterns (Node.js/TypeScript):

**Timing-safe comparison:**
```typescript
import { timingSafeEqual } from 'crypto';
const a = Buffer.from(userValue, 'utf8');
const b = Buffer.from(expectedValue, 'utf8');
if (a.length !== b.length || !timingSafeEqual(a, b)) { /* reject */ }
```

**Origin validation:**
```typescript
const origin = request.headers.get("origin");
const host = request.headers.get("host");
if (origin && host && !origin.includes(host)) {
  return Response.json({ error: "Forbidden" }, { status: 403 });
}
```

**Rate limiting (in-memory):**
```typescript
const RATE_LIMIT = new Map<string, { count: number; resetAt: number }>();
function checkRateLimit(ip: string, max: number, windowMs: number): boolean {
  const now = Date.now();
  const entry = RATE_LIMIT.get(ip);
  if (!entry || now > entry.resetAt) {
    RATE_LIMIT.set(ip, { count: 1, resetAt: now + windowMs });
    return true;
  }
  if (entry.count >= max) return false;
  entry.count++;
  return true;
}
```

**Security headers (Next.js):**
```javascript
headers: [
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(self)" },
]
```

**Cookie hardening:**
```typescript
{ httpOnly: true, secure: true, sameSite: "strict", path: "/" }
```

## Phase 4: Verify (after fixes)

Run the build/lint/test commands detected in Setup:

1. Run type checker (if available)
2. Run test suite (if available)
3. Run build (if available)
4. If anything fails, fix it before declaring done

If no build/lint/test commands were detected, skip verification and note: "No build/test commands found — manual verification recommended."

## Phase 5: Final Report

Update the report with fixes applied:

```
## Fixes Applied
| Vector | Finding | Fix | File(s) Changed |
|--------|---------|-----|-----------------|
| 2 | No CSRF check | Added origin validation | src/app/api/contact/route.ts |

## Updated Scorecard
Protected: X/33 (was Y/33 before fixes)
```

Print the updated scorecard to the conversation.

## Anti-Hallucination Rules

- **Never invent names.** Do not fabricate function names, component names, hook names, or file names. Every identifier in findings must be confirmed via Grep/Glob/Read.
- **Findings must cite evidence.** Every finding needs a real file:line reference. If a Grep returns no matches, the finding doesn't exist — do not invent it.
- **Describe problems, not prescriptive solutions.** Say "no origin check on POST endpoint at src/api/route.ts:15" — do NOT say "add validateOrigin() middleware" (that function doesn't exist).
- **Cannot verify = say so.** For infrastructure-only vectors (DNS, WAF, CDN), report "Cannot verify from code" — do NOT hallucinate "Protected" or "Not Protected."
- **N/A means truly not applicable.** If the project has no database, vector 4 (SQL injection) is N/A — do not fabricate SQL findings.
