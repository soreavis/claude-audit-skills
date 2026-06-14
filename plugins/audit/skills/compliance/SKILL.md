---
name: audit-compliance
description: Regulatory compliance audit against GDPR, ISO 27001:2022, ISO 9001:2015 (and optionally HIPAA, SOC 2, PCI DSS). Scores code on 7 compliance dimensions (data handling, access control, validation, sanitization, audit trail, error handling, documentation) with line-number evidence. Report-only by default; --fix opt-in.
user-invocable: true
argument-hint: "[--framework=gdpr,iso27001,iso9001,hipaa,soc2,pci] [--scope=<path>] [--files=<glob>] [--fix] [--audit-only] [--report] [--strict]"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent
---

# Compliance Audit: GDPR / ISO 27001 / ISO 9001 (+ optional HIPAA, SOC 2, PCI DSS)

Audit code against regulatory compliance frameworks. Score each changed or specified file against 7 compliance dimensions, map findings to specific regulatory clauses, and write a report with line-number evidence. Works on any web, backend, or data-handling project.

**Default behavior: audit-only.** Fixes are opt-in via `--fix`. Writing to `_local/reports/` is opt-in via `--report`.

## When to Use

- After adding new features that touch personal data, user input, or external integrations
- Before a release that changes data handling, authentication, logging, or error paths
- When preparing for an external audit, DPIA, penetration test, or certification renewal
- As part of `/audit:all --tier=enterprise` or on its own when compliance is the concern

Not a substitute for a human DPO, legal counsel, or accredited auditor. This skill finds code-level gaps; it does not certify compliance.

## Arguments

`$ARGUMENTS` — optional flags:

- `--framework=<list>` — comma-separated target frameworks. Valid: `gdpr`, `iso27001`, `iso9001`, `hipaa`, `soc2`, `pci`. Default: `gdpr,iso27001,iso9001` (the free/global core trio).
- `--scope=<path>` — limit to a specific directory (default: entire project, excluding `node_modules`, `dist`, `build`, `.next`, `__pycache__`, `vendor`, `target`).
- `--files=<glob>` — audit only files matching a glob (e.g., `src/api/**/*.ts`). Useful for reviewing a PR diff.
- `--fix` — propose and apply code-level fixes for findings where the remediation is mechanical (missing validators, unsanitized log calls, missing error handling). Architectural findings stay as report items.
- `--audit-only` — explicitly report only (DEFAULT if no fix flag given).
- `--report` — save full report to `_local/reports/compliance-audit-<YYYY-MM-DD>.md`.
- `--report=<path>` — save to a specific path.
- `--strict` — treat every PARTIALLY COMPLIANT rating as a failure and warnings as findings. Use for enterprise / certification contexts.

## Setup

### 1. Detect Tech Stack

Read project files to identify stack. This drives which patterns to search for and which evidence counts as "protection."

| Signal | How | Record |
|---|---|---|
| Language | `package.json` → Node/TS, `pyproject.toml`/`requirements.txt` → Python, `go.mod` → Go, `Cargo.toml` → Rust, `Gemfile` → Ruby, `pom.xml`/`build.gradle` → JVM | Primary language(s) |
| Framework | `next`/`express`/`fastify`/`hono`/`nestjs` → Node; `django`/`flask`/`fastapi`/`starlette` → Python; `gin`/`echo`/`fiber` → Go; `rails`/`sinatra` → Ruby | Framework + version |
| Database | Grep deps for `prisma`, `typeorm`, `sequelize`, `drizzle`, `mongoose`, `pg`, `mysql2`, `sqlalchemy`, `psycopg`, `redis`, `sqlite3` | DB type(s) or "none" |
| Auth | Grep deps for `next-auth`, `passport`, `clerk`, `auth0`, `supabase`, `firebase-auth`, `django.contrib.auth`, `devise`, `lucia` | Auth library or "custom" / "none" |
| Has user data | Grep for user-scoped tables/models, `user_id`, `email`, `phone`, `ssn`, `dob`, `address` | true/false |
| Has file uploads | Grep for `multer`, `formidable`, `multipart`, `request.files`, `UploadFile` | true/false |
| Has logging | Grep for `winston`, `pino`, `bunyan`, `logging.getLogger`, `logrus`, `zap`, structured logger | logger name or "console" / "none" |
| Has analytics/telemetry | Grep for `segment`, `mixpanel`, `amplitude`, `ga4`, `sentry`, `datadog`, `opentelemetry` | list or "none" |
| Deployment target | `Dockerfile`, `vercel.json`, `netlify.toml`, `serverless.yml`, `k8s/`, `cloudformation/` | target or "unknown" |

### 2. Detect Existing Compliance Artifacts

If any of these exist in the project, read them once and use as ground truth:

- `DATA_MAP.md`, `data-map.md`, `docs/data-map.md` — storage locations, PII classifications
- `dpia.md`, `docs/dpia.md`, `_project/reports/dpia.md` — existing DPIA
- `compliance-strategy.md`, `compliance/`, `_project/compliance*.md` — existing strategy docs
- `PRIVACY.md`, `privacy-policy.md`, `public/privacy*.html` — privacy policy
- `ROPA.md`, `records-of-processing.md` — GDPR Article 30 records
- `SECURITY.md` — security policy
- `CHANGELOG.md` — recent security/privacy-relevant changes

If a previous `compliance-audit-report.md` exists, read its "Known Open Findings" section and **do not re-flag resolved or deferred items** unless the code has regressed.

### 3. Determine Target Files

- If `--files=<glob>` → audit exactly those files.
- Else if `--scope=<path>` → audit source files under that path.
- Else if the user passed a list of files as the first positional argument → audit those.
- Else if the argument is `full` → audit all source files in the default source roots (`src/`, `app/`, `lib/`, `api/`, `pkg/`, `internal/`).
- Else → audit files changed since the last commit on `main` (`git diff --name-only main...HEAD`). If not a git repo or no diff, fall back to `full` with a warning printed to the user.

Print the resolved file list count before starting: `Auditing N files under frameworks: [list]`.

## The Seven Compliance Dimensions

Every audited file gets rated on all 7 dimensions. Rating scale: **C** (compliant), **PC** (partially compliant), **NC** (non-compliant), **N/A** (dimension does not apply to this file).

### D1 — Data Handling & Minimization
**Frameworks:** GDPR Art. 5 (data minimization, storage limitation, purpose limitation); ISO 27001 A.8.10 (information deletion), A.8.12 (data leakage prevention); HIPAA §164.312(a)(2)(iv); PCI DSS 3.x; SOC 2 CC6.5.

**Checks:**
- Does the code persist only the fields it needs? Look for `SELECT *`, `.findAll()` without projection, wildcard spreads into storage.
- Are there `fields` / `projection` / `select` parameters exposed to callers so they can minimize what they retrieve?
- Are there size caps on responses, uploads, and exports (e.g., `limit`, `max_records`, upload `max_size`)?
- Is data kept only as long as needed? Grep for retention policies, TTLs, expiry fields, cleanup jobs.
- Are temporary files and in-memory buffers cleaned up on error paths?
- Is there a "right to erasure" / anonymization path for any personal data this file touches?

**PASS evidence:** explicit `fields`/`projection` param, hard limits, retention/TTL config, cleanup in `finally` blocks.
**FAIL evidence:** unbounded queries, no size caps, PII written to persistent storage with no retention policy.

### D2 — Access Control & Tenant Isolation
**Frameworks:** GDPR Art. 32 (security of processing); ISO 27001 A.5.15 (access control), A.5.18 (access rights), A.8.2 (privileged access); HIPAA §164.312(a)(1); SOC 2 CC6.1-CC6.3; PCI DSS 7.x.

**Checks:**
- Is authentication required for every non-public endpoint / tool / handler? Grep for route definitions, check for auth middleware.
- Is the calling user / tenant / profile explicitly resolved and passed through, or is it global state?
- Is there authorization per resource (not just per endpoint)? Look for `owner_id === user.id` checks, RBAC lookups, policy engines.
- Is multi-tenancy enforced at the query layer, not just the filter layer? A filter that can be removed by a malicious client is not isolation.
- Is role-based data masking applied to fields the caller isn't authorized to see?

**PASS evidence:** auth middleware wraps the file's handlers, per-resource ownership checks, tenant-scoped queries at the ORM/DB layer.
**FAIL evidence:** handlers that read `user_id` from the request body, missing `@auth_required` decorators, `where` clauses that skip tenant scoping.

### D3 — Input Validation
**Frameworks:** ISO 27001 A.8.28 (secure coding); OWASP ASVS 5.x; PCI DSS 6.2.4; HIPAA §164.312(c)(1).

**Checks:**
- Is every input validated at the boundary before it reaches business logic? Look for schema validators (Zod, Joi, Yup, Pydantic, class-validator, struct tags, JSON Schema).
- Are type coercions explicit? No silent `parseInt(x)` without a range check.
- Are IDs, filenames, emails, URLs, dates, enums validated by type-specific validators — not regex-by-accident?
- Are filter operators, sort fields, and pagination params validated against allowlists?
- Are file uploads validated for MIME type AND magic bytes AND size?
- Is data size capped before parsing (no `JSON.parse(req.body)` on unbounded input)?

**PASS evidence:** every public entry point has schema validation on its inputs, allowlist checks on enum-ish params.
**FAIL evidence:** raw `req.body` fields flow into queries, regex-only email validation, missing size caps on JSON parsing.

### D4 — Output Sanitization & PII Protection
**Frameworks:** GDPR Art. 32 (pseudonymization, encryption); ISO 27001 A.8.24 (cryptography), A.8.11 (data masking); HIPAA §164.312(e); PCI DSS 3.4, 4.1.

**Checks:**
- Is PII masked / redacted in logs? Grep for logger calls with full request/response bodies. Look for field allowlists or denylists.
- Is PII stripped from error messages returned to clients?
- Is data encrypted in transit (HTTPS enforced, no `http://` URLs for API calls)?
- Is sensitive data encrypted at rest where the framework requires it (HIPAA: PHI at rest; PCI: PAN encrypted or tokenized)?
- Are there field-level masking rules for privileged vs. non-privileged callers?
- For GDPR strict mode / jurisdictions: is there a code path that produces PII-free logs for audit trail purposes?

**PASS evidence:** structured logger with field allowlist, masking middleware applied globally, HTTPS-only config, log scrubbing in strict mode.
**FAIL evidence:** `logger.info(req.body)`, stack traces returned to clients, `http://` base URLs, PII in error responses.

### D5 — Audit Trail & Logging
**Frameworks:** GDPR Art. 30 (records of processing), Art. 33 (breach notification requires logs); ISO 27001 A.8.15 (logging), A.8.16 (monitoring); HIPAA §164.312(b); PCI DSS 10.x; SOC 2 CC7.

**Checks:**
- Is every security-relevant action logged (auth, access denial, privilege elevation, data export, deletion)?
- Do log entries have: timestamp, actor, action, resource, outcome, correlation/request ID?
- Are logs structured (JSON) not free-form strings?
- Are logs tamper-resistant (append-only storage, external shipping) — or at least, are they shipped off the host?
- Is log retention configured and documented? GDPR requires retention to be proportionate; ISO 27001 A.8.15 requires defined retention.
- Are clocks synchronized? Look for NTP config in Docker/infra files.

**PASS evidence:** structured logger with correlation IDs, auth/access/delete events logged, log shipping configured, retention set.
**FAIL evidence:** `print()` / `console.log` for important actions, no correlation IDs, free-form strings, no log retention config.

### D6 — Error Handling
**Frameworks:** GDPR Art. 32 (confidentiality — no info leakage); ISO 27001 A.5.24 (incident management), A.8.29 (security testing); OWASP ASVS 7.x.

**Checks:**
- Are typed exceptions converted to generic errors at the boundary? No stack traces returned to clients.
- Are sensitive fields (tokens, passwords, keys, internal IDs) stripped from error messages?
- Are errors logged server-side with full context BUT returned to clients with generic messages?
- Are async errors caught (unhandled promise rejections, goroutine panics, thread exceptions)?
- Is there a global error handler / middleware that acts as a last-resort shield?
- Are retry-safe errors distinguished from permanent failures (important for data integrity)?

**PASS evidence:** global error handler, typed error classes converted to safe client messages, full context in server logs.
**FAIL evidence:** `res.status(500).send(err.stack)`, bare `raise` in handlers, unhandled async errors, sensitive data in error messages.

### D7 — Documentation & Transparency
**Frameworks:** GDPR Art. 12-14 (transparency), Art. 30 (ROPA), Art. 35 (DPIA); ISO 9001 7.5 (documented information); ISO 27001 A.5.1 (policies), A.5.10 (acceptable use); HIPAA §164.316.

**Checks:**
- Do public functions, endpoints, or tools have docstrings / OpenAPI descriptions that explain what data they touch?
- Are data fields annotated with PII classification where that matters (tags, comments, JSON Schema `x-pii`, Prisma `/// PII`)?
- Are breaking changes and security fixes mentioned in `CHANGELOG.md`?
- Is there a privacy policy / data map / DPIA for the data flows this file participates in?
- Are environment variables documented with their purpose and sensitivity level?
- For GDPR: is there a ROPA entry (Art. 30) covering the processing activity this file implements?

**PASS evidence:** docstrings on public surface, PII annotations, changelog entries for security fixes, DATA_MAP entry for new storage.
**FAIL evidence:** undocumented public handlers, new storage location not in DATA_MAP, new PII field with no classification.

## Finding Format

Every finding uses this format. The identifier `F-{XX}` is sequential within this audit run (start at `F-01`).

```markdown
### F-{XX} ({severity}) — {framework}: {title}

**Dimension:** D{N} — {dimension name}
**Description:** {one or two sentences describing the gap}
**Regulatory Requirement:** {specific clause, e.g., "GDPR Art. 32(1)(a) — pseudonymization of personal data"}
**Affected Files:**
- `path/to/file.ts:42` — {what was found}
- `path/to/other.ts:118` — {what was found}
**Evidence:** {actual code snippet or grep hit}
**Mitigation:** {concrete remediation — code-level where possible}
**Status:** OPEN
```

**Severity levels:**
- **HIGH** — active regulatory non-compliance; demonstrable harm path; or a control required by a framework the project claims to follow is missing.
- **MEDIUM** — partial compliance; control exists but has gaps; defense-in-depth weakness.
- **LOW** — documentation gap, cosmetic, or belt-and-braces improvement.
- **INFO** — observation, no finding; recorded so a future audit knows it was considered.

**Framework tag format:** `GDPR`, `ISO27001`, `ISO9001`, `HIPAA`, `SOC2`, `PCI`. If a finding spans multiple frameworks, use the strictest (e.g., `GDPR+HIPAA`).

## Workflow

### Phase 1 — Plan

1. Detect stack and compliance artifacts (see Setup).
2. Resolve the target file list.
3. Resolve the framework list from `--framework` (default: gdpr, iso27001, iso9001).
4. Print the plan:
   ```
   Compliance Audit
   Frameworks: GDPR, ISO 27001:2022, ISO 9001:2015
   Stack: Next.js 14 + TypeScript + Prisma/Postgres + NextAuth
   Files: 12 files under src/api/**
   Mode: audit-only
   ```

### Phase 2 — Audit Each File

For every target file:

1. **Read the file.** Actually read it — do not infer from filename.
2. **Classify relevance.** Mark each dimension as `N/A` (e.g., D2 on a pure utility file with no handlers, D4 on a file with no outputs) or "applicable."
3. **Run the dimension checks.** For each applicable dimension, use Grep/Glob against the file and its immediate collaborators to find evidence. Every finding must cite an actual file:line found via tool calls — never invented.
4. **Rate the file.** For each applicable dimension: C / PC / NC.
5. **Write findings** for every PC and NC rating. C ratings do not generate findings (but they do generate an INFO entry in the summary).

For large audits, delegate each file (or group of files) to an `Agent` tool call with a self-contained prompt, so per-file context doesn't bloat the main conversation. The agent prompt should include: the file path, the framework list, the 7 dimensions from this skill, and the finding format. Run agents **sequentially**, not in parallel, so you can feed each one context from the previous (for example, resolved findings that should not be re-flagged).

### Phase 3 — Aggregate & Rate

1. **Deduplicate.** If the same gap appears in multiple files via a shared helper, merge into one finding listing all affected files.
2. **Count.** Tally: HIGH, MEDIUM, LOW, INFO. Count files at each dimension rating.
3. **Compute an overall grade** per framework:
   - **A** — zero HIGH, ≤2 MEDIUM per 1,000 LOC
   - **B** — zero HIGH, ≤5 MEDIUM per 1,000 LOC
   - **C** — ≤1 HIGH, ≤10 MEDIUM per 1,000 LOC
   - **D** — ≤3 HIGH
   - **F** — ≥4 HIGH, or any HIGH involving personal data breach surface
4. **In `--strict` mode:** every PARTIALLY COMPLIANT rating counts as a MEDIUM finding, and the grade ceiling is capped at B until strict findings are resolved.

### Phase 4 — Write the Report

Print the summary to the conversation. Save the full report only if `--report` is set.

**Report location logic** (same as other audit-* skills):
1. If `_local/reports/` exists → save there
2. Else if `_local/` exists → create `_local/reports/` and save there
3. Else if `.gitignore` contains `_local` → create `_local/reports/` and save there
4. Else → save to project root as `compliance-audit-<YYYY-MM-DD>.md` and **warn** the user it's tracked by git

Filename format: `compliance-audit-<YYYY-MM-DD>.md`. If running multiple times per day, append `-N`.

**Report format:**

```markdown
# Compliance Audit Report — [Project Name]
**Date:** YYYY-MM-DD | **Frameworks:** [list] | **Scope:** [path]
**Stack:** [detected] | **Mode:** [audit-only | fix] | **Strict:** [yes/no]

## Executive Summary

| Framework | Grade | HIGH | MEDIUM | LOW | INFO |
|-----------|-------|------|--------|-----|------|
| GDPR | B | 0 | 3 | 2 | 1 |
| ISO 27001:2022 | B | 0 | 2 | 1 | 0 |
| ISO 9001:2015 | A | 0 | 0 | 1 | 0 |
| **Overall** | **B** | **0** | **5** | **4** | **1** |

## Dimension Scores

| Dimension | Files C | Files PC | Files NC | N/A |
|-----------|---------|----------|----------|-----|
| D1 — Data Handling | 8 | 3 | 0 | 1 |
| D2 — Access Control | 9 | 2 | 1 | 0 |
| D3 — Input Validation | 7 | 4 | 1 | 0 |
| D4 — Output Sanitization | 10 | 1 | 0 | 1 |
| D5 — Audit Trail | 6 | 5 | 1 | 0 |
| D6 — Error Handling | 8 | 3 | 0 | 1 |
| D7 — Documentation | 5 | 6 | 1 | 0 |

## Known Open Findings (from prior audits)

- {list any carried over, with status}

## New Findings

### HIGH

{F-01, F-02, ... with full detail}

### MEDIUM

{F-03, F-04, ...}

### LOW

{F-05, F-06, ...}

### INFO

{F-07, ...}

## Priority Actions

1. {top 5-10 most impactful findings with file:line}

## Artifacts Updated

- `DATA_MAP.md` — [updated / no change / not present]
- `_project/reports/dpia.md` — [updated / no change / not present]
- `_project/reports/compliance-audit-report.md` — [this file]

---AUDIT-SUMMARY---
audit: compliance
critical: 0
high: N
medium: N
low: N
score: [A-F grade]
skipped: false
skip_reason:
---END-SUMMARY---
```

The `---AUDIT-SUMMARY---` block must appear at the **end** of the report, formatted exactly as above, so `audit-all` can parse it. In this skill, `critical` maps to HIGH findings that are also regulatory non-compliance (i.e., HIGH + framework citation).

### Phase 5 — Update Compliance Artifacts (only if findings warrant)

After writing the report, inspect findings for the following triggers:

- **New PII field or storage location** → update `DATA_MAP.md` (or create one at project root if missing)
- **Material change to risk profile** (new data category, new third-party processor, new cross-border transfer) → update `dpia.md`
- **Any finding at HIGH** → append a row to `CHANGELOG.md` under `[Unreleased]` with `### Security` category
- **New environment variable discovered during audit** → ensure it's documented in `README.md` or project config docs

Only modify these files if they already exist or the finding clearly justifies creating one. Never create compliance boilerplate that isn't backed by a specific finding.

### Phase 6 — Fix (only with --fix flag)

If `--fix` is the active flag, apply **mechanical** fixes only:

- **D3 — missing validators:** add schema validation at the entry point using the project's existing validator library. If no validator library is in use, add a finding recommending one but do NOT introduce a new dependency.
- **D4 — PII in logs:** replace `logger.info(req.body)` with a field-allowlisted log call, or remove the call.
- **D4 — stack traces to clients:** wrap the handler in a try/catch that logs server-side and returns a generic message.
- **D5 — missing correlation IDs:** add correlation ID middleware if the framework supports it; otherwise add a finding.
- **D6 — missing try/catch:** wrap async handlers at the boundary.
- **D7 — missing docstrings on public handlers:** add concise docstrings describing inputs, outputs, and data touched. Do NOT fabricate purpose — if unclear, leave a TODO and a finding.

**Never auto-fix:**
- D1 — data minimization. Architectural, needs human review of query patterns.
- D2 — access control. Getting auth wrong automatically is worse than leaving it unfixed.
- Any finding where the fix requires knowing business intent (retention periods, field sensitivity, tenant model).

After fixing: run the project's build/lint/test commands (if detected) and fix any breakage. Append a `## Fixes Applied` section to the report.

## Anti-Hallucination Rules

These are non-negotiable:

- **Every finding must cite a real file:line** found via Read/Grep/Glob. No speculation.
- **Never invent regulatory clause numbers.** If unsure, cite only the framework (e.g., "GDPR Art. 32"), not a specific sub-clause you can't verify.
- **Never claim a control exists without seeing the code.** "The handler probably validates input" is not a PASS; grep for the validator, or rate it NC.
- **Never cite certifications the project doesn't have.** If the project claims ISO 27001 in its docs, verify by reading those docs; don't assume.
- **Do not re-flag resolved findings.** Read any prior `compliance-audit-report.md` and respect its "Resolved" / "Deferred" sections unless the code has regressed.
- **Distinguish "requires infrastructure review" from a finding.** Many controls (WAF, DNS, backup encryption) can't be verified from code. Report those as `INFO — requires infrastructure review`, not as findings.

## Known Limitations

- **Code-level only.** This skill cannot verify: backup encryption at rest, DR drills, staff training records, physical security, vendor DPAs, cookie consent UX, actual breach notification procedures, insurance, legal basis for processing.
- **No certification.** A clean report does not make the project "GDPR compliant" or "ISO 27001 certified." It means the code-level controls this skill checks are in place.
- **Framework evolution.** GDPR guidance, ISO 27001 Annex A (2022 revision), and HIPAA OCR guidance change. Re-run periodically.
- **Jurisdiction.** This skill assumes EU/EEA for GDPR, global for ISO, US for HIPAA. It does not cover CCPA, LGPD, PIPL, UK DPA 2018, or sector-specific rules (FERPA, GLBA, etc.) — add them via issue if needed.

## Integration with /audit:all

When invoked via `/audit:all`, this skill receives a condensed instruction from the orchestrator and writes its report to a numbered file (e.g., `mega-audit-9-compliance-YYYY-MM-DD.md`). It must end with the `---AUDIT-SUMMARY---` block so the orchestrator can parse counts.

Default framework list when invoked from `audit-all` is `gdpr,iso27001,iso9001`. Tier `enterprise` adds `hipaa,soc2,pci` if the project's stack suggests they apply (HIPAA if health data signals; PCI if payment processing; SOC 2 always in enterprise tier).
