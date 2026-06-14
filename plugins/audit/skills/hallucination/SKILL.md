---
name: audit-hallucination
description: >
  Audit any target for hallucination attack surface — prompt/skill files, code calling LLM APIs,
  LLM-generated content, or recent git changes. Identifies fabrication pressure, ungrounded claims,
  missing tool guards, slot-filling pressure, narrative amplification, across 46 hallucination vectors.
  Use when asked to audit hallucination risk, harden prompts, check AI output reliability, verify
  generated content, review LLM integration code, or validate recent AI-assisted code changes.
  Also trigger on "hallucination audit", "grounding check", "fabrication risk", "prompt hardening",
  "anti-hallucination", "verify AI output", or "audit last changes for hallucination".
user-invocable: true
argument-hint: "[--mode=auto|prompt|code|content|diff] [--fix] [--scope=<path>] [--report] [--severity=<level>] [--last=<N>]"
---

# Hallucination Attack Surface Audit

Comprehensive audit for hallucination risk across four target types: prompt/skill files, code calling LLM APIs, LLM-generated content, and recent code changes. Reports findings with severity ratings and optionally applies hardening fixes.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--mode=<mode>` — what to audit (default: `auto`)
    - `auto` — detect target type from scope and apply relevant modes
    - `prompt` — audit SKILL.md, prompt files, system instructions, agent configs
    - `code` — audit application code that calls LLM APIs (OpenAI, Anthropic, LangChain, AI SDK)
    - `content` — audit generated content (markdown, HTML, reports) for fabricated claims
    - `diff` — audit recent git changes for hallucination patterns (phantom imports, invented APIs)
  - `--fix` — apply hardening fixes after audit (default: report only)
  - `--scope=<path>` — target file or directory (default: current directory)
  - `--report` — save full report to `_local/reports/hallucination-audit-<YYYY-MM-DD>.md`
  - `--severity=<level>` — minimum severity to report: `critical`, `high`, `medium`, `low` (default: all)
  - `--last=<N>` — for `--mode=diff`, number of commits to audit (default: 5)

**Default behavior: audit-only.** Fixes are opt-in via `--fix`.

### Report Location Logic

When `--report` is used:
1. If `_local/reports/` exists -> save there
2. Else if `_local/` exists -> create `_local/reports/` and save there
3. Else -> save to project root as `hallucination-audit-<YYYY-MM-DD>.md` (warn user it's tracked by git)

## Setup

### 1. Detect Target Type (for --mode=auto)

If no explicit mode given, detect from scope:

| Signal | Mode |
|--------|------|
| Scope points to a `SKILL.md`, `*.skill`, or file containing YAML frontmatter with `name:`/`description:` | `prompt` |
| Scope points to a directory with `SKILL.md` inside | `prompt` |
| Grep finds `openai`, `anthropic`, `@ai-sdk`, `langchain`, `generateText`, `streamText` in scope | `code` |
| Scope points to `.md` or `.html` file that doesn't match prompt patterns | `content` |
| No scope given + inside a git repo | `diff` (last 5 commits) |
| No scope given + not a git repo + no AI code found | STOP — "No auditable target found. Use --mode and --scope to specify." |

If multiple modes match (e.g., directory has both SKILL.md files AND code calling LLMs), run all matching modes.

### 2. Detect Tech Stack (for code/diff modes)

Read project files to identify:

| Check | How | Records |
|-------|-----|---------|
| Language | `package.json` -> Node/TS, `requirements.txt`/`pyproject.toml` -> Python, `go.mod` -> Go | Primary language |
| AI SDK | Grep for `openai`, `anthropic`, `@ai-sdk/core`, `langchain`, `llama-index` in deps | AI libraries |
| Framework | `next` -> Next.js, `express` -> Express, `fastapi` -> FastAPI, `flask` -> Flask | Framework |
| Test framework | `vitest`, `jest`, `pytest` in deps | Test runner |

### 3. Collect Targets

**Prompt mode:** Glob for `**/SKILL.md`, `**/*.skill`, `**/system-prompt*`, `**/prompt*.*` in scope.
**Code mode:** Grep for files importing AI SDKs. Trace all call sites.
**Content mode:** Read the scoped file(s) directly.
**Diff mode:** Run `git log --oneline -N` then `git diff HEAD~N..HEAD` to collect changed files and their diffs.

## Standardized Finding Format

Every finding uses this format:

```
### [SEVERITY] Vector VN: [Name] — [Short description]
- **Target:** [file path or content reference]
- **Location:** [line number, section, or diff hunk]
- **Evidence:** [the specific text/pattern that creates risk]
- **Risk:** [what hallucination could occur]
- **Remediation:** [concrete fix]
```

Severity values: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

---

## Mode 1: Prompt Audit (--mode=prompt)

Audit prompt files, SKILL.md files, system instructions, and agent configurations for patterns that create hallucination pressure.

Launch two parallel agents:

### Agent 1: Structural Hallucination Pressure (Vectors P1-P8)

**Agent tool prompt:**

> Audit prompt/skill files for structural hallucination pressure at [scope]. Read every target file fully.
>
> For each vector below, search the file content and report findings using the format:
> `### [SEVERITY] Vector PN: Name — description` with Target, Location, Evidence, Risk, Remediation fields.
>
> **Vector P1 — Slot-Filling Pressure:** Severity: HIGH
> - Count the number of required output fields/sections the prompt mandates
> - If the prompt requires populating N items across M categories (e.g., "for each of 6 competitors, report across 3 categories"), calculate total slots: N x M
> - Total slots > 10 with no "nothing found" default = HIGH. > 20 = CRITICAL.
> - Evidence: list the slots and their locations in the prompt
> - Risk: LLM will fabricate to fill empty slots rather than report gaps
> - Remediation: add explicit "nothing found is the default state" instruction, reduce mandatory slots, or make sections optional
>
> **Vector P2 — Fabricated URL Pressure:** Severity: CRITICAL
> - Search for instructions asking the LLM to provide URLs, links, source references, or citations
> - Check: is there an explicit constraint that URLs must come from tool output (search results, API responses)?
> - If prompt asks for URLs without grounding constraint = CRITICAL
> - Evidence: the instruction text requesting URLs
> - Risk: LLM will generate plausible but nonexistent URLs
> - Remediation: add "Every URL must be copied from a search/tool result. Never construct a URL from memory."
>
> **Vector P3 — Fabricated Date Pressure:** Severity: HIGH
> - Search for instructions asking for dates, timestamps, "when it was published", recency claims
> - Check: does the prompt constrain dates to come from tool/search metadata?
> - If prompt asks for dates without grounding constraint = HIGH
> - Evidence: the instruction text requesting dates
> - Risk: LLM will generate plausible but incorrect dates
> - Remediation: add "Only include dates from search result metadata. Otherwise write 'Date: not confirmed'."
>
> **Vector P4 — Fabricated Statistics Pressure:** Severity: HIGH
> - Search for instructions asking for numbers, counts, percentages, metrics, rankings, market share, revenue, user counts
> - Check: are stats constrained to cited sources?
> - If prompt asks for quantitative claims without source constraints = HIGH
> - Evidence: the instruction text requesting statistics
> - Risk: LLM will generate authoritative-sounding but invented numbers
> - Remediation: add "Do not state numbers unless the source explicitly provides them."
>
> **Vector P5 — Fabricated Quote Pressure:** Severity: HIGH
> - Search for instructions asking for quotes, testimonials, "what they said", attributed statements
> - Check: does the prompt require quotes come from actual sources?
> - If prompt asks for quotes without verification = HIGH
> - Evidence: the instruction text requesting quotes
> - Risk: LLM will attribute fabricated statements to real people
> - Remediation: add "Never fabricate quotes. Only include direct quotes found in search results with source attribution."
>
> **Vector P6 — Unverifiable Analysis Pressure:** Severity: MEDIUM
> - Search for instructions asking for strategic analysis, competitive implications, market predictions, sentiment assessment, "why it matters"
> - Check: is the analysis constrained to reference specific findings?
> - Unconstrained analysis sections that don't require grounding in reported facts = MEDIUM
> - Evidence: the instruction text requesting analysis
> - Risk: LLM will generate confident-sounding but ungrounded strategic claims
> - Remediation: add "Analysis must directly reference a specific finding listed above. No freestanding claims."
>
> **Vector P7 — Narrative Amplification:** Severity: MEDIUM
> - Search for instructions asking for summaries, narratives, "highlights", "key takeaways", "executive summary", or synthesis sections
> - Check: does the prompt constrain the narrative to only reference items already in the report?
> - Unconstrained synthesis = MEDIUM (introduces new claims under guise of summarizing)
> - Evidence: the instruction text requesting narrative
> - Risk: synthesis section introduces new fabricated claims not present in the body
> - Remediation: add "This section must ONLY reference findings already listed above. Do not introduce new claims."
>
> **Vector P8 — Confidence Calibration Absence:** Severity: LOW
> - Check: does the prompt include any instruction to express uncertainty, use hedging language, or distinguish confirmed vs unconfirmed items?
> - No uncertainty guidance = LOW
> - Evidence: absence of confidence calibration instructions
> - Risk: all output presented with equal confidence regardless of evidence strength
> - Remediation: add "Mark items as 'Confirmed' (from tool results) or 'Unconfirmed' (uncertain). Never present uncertain information with the same confidence as verified facts."
>
> End with findings summary block: `---FINDINGS-SUMMARY--- critical: N high: N medium: N low: N ---END-SUMMARY---`

### Agent 2: Infrastructure & Guard Rails (Vectors P9-P16)

**Agent tool prompt:**

> Audit prompt/skill files for missing guard rails and infrastructure gaps at [scope]. Read every target file fully.
>
> For each vector, search the file content and report findings.
>
> **Vector P9 — Missing Tool Guard:** Severity: HIGH
> - Check: does the prompt depend on external tools (web search, API calls, database queries) for factual content?
> - If yes: is there an explicit prerequisite check ("if tool X is not available, STOP")?
> - Missing tool guard when prompt requires tools = HIGH
> - Evidence: the tools the prompt depends on + absence of guard
> - Risk: without tools, LLM falls back to training data, producing stale or fabricated results
> - Remediation: add prerequisite section: "This task requires [tool]. If unavailable, STOP and inform the user."
>
> **Vector P10 — Missing Grounding Constraint:** Severity: CRITICAL
> - Check: does the prompt contain an explicit rule like "every factual claim must trace to a tool result"?
> - Search for grounding language: "only from search results", "must come from tool output", "do not generate from memory"
> - Complete absence of grounding constraints in a prompt that asks for factual output = CRITICAL
> - Evidence: the factual output requirements + absence of grounding rules
> - Risk: entire output may be generated from training data with no verification
> - Remediation: add a "Ground Rules" section at the top with explicit grounding requirements
>
> **Vector P11 — Missing "Nothing Found" Default:** Severity: HIGH
> - Check: does the prompt define what to do when no data is found for a required section?
> - Search for: "if no results", "nothing found", "no activity", default empty state language
> - If the prompt requires output for N categories but doesn't define the empty state = HIGH
> - Evidence: the output requirements + absence of empty-state handling
> - Risk: LLM fills every section rather than reporting gaps
> - Remediation: add "The default state is 'nothing found'. Only populate sections with tool-verified results."
>
> **Vector P12 — Training Data Leakage Guard:** Severity: MEDIUM
> - Check: does the prompt explicitly prohibit using training/memorized data as a source?
> - For prompts that ask for current/recent information, absence of this guard = MEDIUM
> - For prompts about historical/static topics, this is N/A
> - Evidence: the recency requirement + absence of training data guard
> - Risk: LLM mixes outdated training data with current search results
> - Remediation: add "Do not use training data as a source. Only tool results count."
>
> **Vector P13 — Missing Research Log / Transparency:** Severity: LOW
> - Check: does the prompt require the LLM to log what searches it ran, what tools it used, or what queries returned?
> - Absence of transparency requirement = LOW
> - Evidence: absence of research logging instruction
> - Risk: reader cannot assess coverage or verify claims
> - Remediation: add a research log section to the output format showing queries run and result counts
>
> **Vector P14 — Allowed Tools Not Declared:** Severity: MEDIUM
> - Check YAML frontmatter for `allowed-tools` field
> - If the prompt depends on specific tools but doesn't declare them in frontmatter = MEDIUM
> - Evidence: tools referenced in prompt body + absence in frontmatter
> - Risk: skill may run with tools the author didn't intend, or without tools it needs
> - Remediation: add `allowed-tools:` to frontmatter listing required tools
>
> **Vector P15 — Self-Verification Fallacy:** Severity: MEDIUM
> - Search for checklist items or instructions asking the LLM to verify its own output accuracy (e.g., "verify sources are real", "check that links work", "ensure dates are correct")
> - Self-verification without tool calls = MEDIUM (LLM cannot reliably self-check hallucinations)
> - Evidence: the self-verification instruction
> - Risk: creates false sense of quality control — LLM will "verify" fabricated content as correct
> - Remediation: replace self-verification with tool-based verification (WebFetch to check URLs, explicit search to confirm claims) or remove the checklist item entirely
>
> **Vector P16 — Output Volume vs. Evidence Ratio:** Severity: MEDIUM
> - Estimate the expected output length/complexity from the prompt's output format section
> - Compare with the likely volume of verifiable evidence available (number of search queries, scope of tools)
> - If expected output vastly exceeds what tools could reasonably provide = MEDIUM
> - Evidence: output format requirements vs tool-based input capacity
> - Risk: LLM fills the gap between available evidence and expected output with fabrication
> - Remediation: reduce output expectations, or add "report length should be proportional to findings — a short report with verified facts is better than a long report with gaps filled by speculation"
>
> End with findings summary block.

---

## Mode 2: Code Audit (--mode=code)

Audit application code that integrates LLM APIs for patterns that propagate, trust, or amplify hallucinations.

Launch two parallel agents:

### Agent 3: LLM Output Handling (Vectors C1-C8)

**Agent tool prompt:**

> Audit code for unsafe LLM output handling at [scope]. Stack: [detected stack].
>
> First, find all LLM API call sites:
> - Grep for: `openai.chat`, `openai.completions`, `anthropic.messages`, `generateText`, `streamText`, `ChatOpenAI`, `ChatAnthropic`, `llm.invoke`, `chain.invoke`, `completion(`, `client.chat.completions.create`
> - For each call site, trace how the response is used downstream.
>
> Report findings using the standard format.
>
> **Vector C1 — Unvalidated LLM Output:** Severity: HIGH
> - For each LLM call: check if the response is validated against a schema (Zod, Joi, TypeScript type guard, Pydantic) before use
> - Raw string response used directly without parsing/validation = HIGH
> - Evidence: the call site and how the response is consumed
> - Risk: malformed, unexpected, or hallucinated content propagates through the application
> - Remediation: add schema validation on every LLM response before downstream use
>
> **Vector C2 — LLM Output in SQL/Commands:** Severity: CRITICAL
> - Trace LLM responses into: SQL queries, shell commands (`exec`, `spawn`), file system operations, `eval()`
> - LLM output flowing into execution context without sanitization = CRITICAL
> - Evidence: the data flow from LLM response to execution
> - Risk: hallucinated or manipulated LLM output causes injection attacks
> - Remediation: never pass raw LLM output to execution contexts; validate against allowlists
>
> **Vector C3 — LLM Output Rendered as HTML:** Severity: HIGH
> - Trace LLM responses into: `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, template literal HTML, `document.write`
> - LLM output rendered as HTML without sanitization = HIGH
> - Evidence: the rendering code
> - Risk: XSS via hallucinated or manipulated LLM content
> - Remediation: sanitize with DOMPurify before rendering, or render as plain text
>
> **Vector C4 — LLM-Generated URLs Followed Blindly:** Severity: HIGH
> - Trace LLM responses into: `fetch()`, `axios`, `redirect()`, `window.location`, `href` attributes
> - LLM output used as URL without validation = HIGH
> - Evidence: the code following LLM-generated URLs
> - Risk: SSRF via hallucinated URLs, phishing via fabricated redirect targets
> - Remediation: validate URLs against an allowlist of domains before following
>
> **Vector C5 — Cached Hallucinations:** Severity: MEDIUM
> - Check if LLM responses are stored: database, Redis, localStorage, file system, in-memory cache
> - Cached without TTL or freshness check = MEDIUM. Cached without any validation = HIGH.
> - Evidence: the caching code
> - Risk: hallucinated content persists and is served to future users as fact
> - Remediation: add TTL, validation before caching, and cache invalidation mechanism
>
> **Vector C6 — Missing Fallback on LLM Failure:** Severity: MEDIUM
> - Check error handling around LLM calls: is there a fallback when the LLM returns unexpected/empty/error responses?
> - No error handling or empty catch = MEDIUM
> - Evidence: the error handling (or absence) around LLM calls
> - Risk: application crashes or shows raw error to user on LLM failure
> - Remediation: add try-catch with meaningful fallback behavior
>
> **Vector C7 — Unbounded Generation:** Severity: LOW
> - Check if LLM calls set `max_tokens` or equivalent length limit
> - No output length limit = LOW
> - Evidence: the LLM call parameters
> - Risk: unexpectedly long outputs consume tokens, break UI, or contain more hallucination surface
> - Remediation: set appropriate max_tokens for the use case
>
> **Vector C8 — Temperature > 0 for Factual Tasks:** Severity: LOW
> - Check `temperature` parameter on LLM calls that produce factual content (not creative writing)
> - Factual task with temperature > 0.3 = LOW
> - Evidence: the temperature setting and task type
> - Risk: higher temperature increases hallucination probability for factual outputs
> - Remediation: use temperature 0-0.2 for factual extraction; higher only for creative tasks
>
> End with findings summary block.

### Agent 4: Trust Architecture (Vectors C9-C14)

**Agent tool prompt:**

> Audit the trust architecture around LLM integrations at [scope]. Stack: [detected stack].
>
> **Vector C9 — LLM Output Displayed as Fact:** Severity: MEDIUM
> - Find where LLM output is shown to users. Check if it's labeled as AI-generated or presented as authoritative fact.
> - AI output presented without disclaimer = MEDIUM
> - Evidence: the rendering code and surrounding UI context
> - Risk: users trust hallucinated content as verified fact
> - Remediation: add "AI-generated" label, or caveat like "This content was generated by AI and may contain errors"
>
> **Vector C10 — LLM Output Feeding LLM Input (Amplification Chains):** Severity: HIGH
> - Trace if LLM output from one call is fed as input to another LLM call without human review
> - Chained LLM calls without intermediate validation = HIGH
> - Evidence: the chain of calls
> - Risk: hallucinations compound — first LLM invents a fact, second LLM builds on it
> - Remediation: add validation/human review between chained LLM calls, or use structured output to constrain
>
> **Vector C11 — No Source Attribution in Output:** Severity: LOW
> - Check if LLM-generated content includes source references that could be verified
> - Factual content without any source trail = LOW
> - Evidence: output format/template
> - Risk: users cannot verify claims, hallucinations go undetected
> - Remediation: require LLM to cite sources; validate citations exist before displaying
>
> **Vector C12 — Mixing LLM Output with Verified Data:** Severity: MEDIUM
> - Check if application mixes LLM-generated content with data from trusted sources (database, API) without visual distinction
> - Mixed content without provenance markers = MEDIUM
> - Evidence: the rendering code mixing sources
> - Risk: hallucinated LLM content inherits credibility of adjacent verified data
> - Remediation: visually distinguish AI-generated sections, or add provenance metadata
>
> **Vector C13 — LLM Writes to Authoritative Stores:** Severity: CRITICAL
> - Check if LLM output is written to: production databases, config files, user profiles, financial records, medical records, legal documents
> - Unreviewed LLM output persisted to authoritative store = CRITICAL
> - Evidence: the write operation
> - Risk: hallucinated data becomes the system of record
> - Remediation: require human review before LLM output is persisted to authoritative stores
>
> **Vector C14 — No Rate Limiting on LLM-Powered Endpoints:** Severity: MEDIUM
> - Check API endpoints that trigger LLM calls. Is there rate limiting?
> - No rate limit on LLM-triggering endpoint = MEDIUM
> - Evidence: the endpoint and absence of rate limiting
> - Risk: abuse generates high volume of hallucinated content, cost overrun
> - Remediation: add rate limiting on all endpoints that trigger LLM calls
>
> End with findings summary block.

---

## Mode 3: Content Audit (--mode=content)

Audit LLM-generated content (markdown, HTML, reports) for hallucination indicators.

Run this in the main conversation (no agents needed — content audit is sequential).

### Content Vectors (Vectors G1-G8)

Read the target file(s) and check each vector:

**Vector G1 — Fabricated URLs:** Severity: CRITICAL
- Extract all URLs from the content
- For each URL: use WebFetch to check if it resolves (200 response). If WebFetch unavailable, use WebSearch to verify the URL exists.
- URLs that return 404, redirect to unrelated pages, or cannot be verified = CRITICAL per URL
- Evidence: the broken/fabricated URL and its context
- If no web tools available: flag all URLs as "UNVERIFIED — cannot confirm without web access" (severity: MEDIUM)

**Vector G2 — Fabricated Citations:** Severity: HIGH
- Search for quoted text attributed to people, organizations, or documents
- Use WebSearch to verify the quote exists. If exact match not found = HIGH
- Evidence: the quote and its attribution
- If no web tools available: flag all attributed quotes as "UNVERIFIED" (severity: MEDIUM)

**Vector G3 — Fabricated Statistics:** Severity: HIGH
- Search for numbers, percentages, dollar amounts, user counts, market share claims, rankings
- For each: check if a source is cited. If cited, verify via WebSearch.
- Unsourced statistics = HIGH. Sourced but unverifiable = MEDIUM.
- Evidence: the statistic and its context

**Vector G4 — Temporal Impossibilities:** Severity: HIGH
- Check all dates and time references for consistency
- Look for: future events described as past, events dated before the entity existed, timeline contradictions within the document
- Evidence: the conflicting dates/claims

**Vector G5 — Entity Confusion:** Severity: MEDIUM
- Check for people, companies, products mentioned. Verify basic facts (e.g., company X makes product Y, person Z holds role W)
- WebSearch to spot-check 3-5 key entity claims
- Misattributed roles, products, or affiliations = MEDIUM
- Evidence: the incorrect claim vs reality

**Vector G6 — Phantom References:** Severity: HIGH
- Check for references to files, functions, APIs, packages, or tools mentioned in the content
- For code references: Grep the codebase to confirm they exist
- For package references: WebSearch to confirm the package exists
- References to nonexistent items = HIGH
- Evidence: the phantom reference

**Vector G7 — Confident Hedging Absence:** Severity: LOW
- Check if the content uses uniformly confident language even for claims that are inherently uncertain
- All claims stated as absolute fact with no hedging = LOW
- Evidence: examples of overconfident claims

**Vector G8 — Internal Consistency:** Severity: MEDIUM
- Check if the document contradicts itself (e.g., summary says 5 items found but body lists 3)
- Count mismatches, contradictory claims between sections = MEDIUM
- Evidence: the contradicting passages

---

## Mode 4: Diff Audit (--mode=diff)

Audit recent git changes for hallucination artifacts — phantom imports, invented APIs, nonexistent files, fabricated test assertions.

### Diff Vectors (Vectors D1-D8)

Run `git log --oneline -N` (N from `--last` flag, default 5) and `git diff HEAD~N..HEAD` to collect changes.

Launch two parallel agents:

### Agent 5: Phantom Code (Vectors D1-D4)

**Agent tool prompt:**

> Audit recent git changes for phantom code patterns. Project: [cwd]. Diff range: HEAD~N..HEAD.
>
> Run `git diff HEAD~N..HEAD --name-only` to get changed files, then examine each.
>
> **Vector D1 — Phantom Imports:** Severity: CRITICAL
> - In added lines: find all import statements
> - For each import: verify the module/file exists (Glob for local imports, check package.json/requirements.txt for packages)
> - Import of nonexistent local file = CRITICAL. Import of nonexistent package = CRITICAL.
> - Evidence: the import statement and what's missing
>
> **Vector D2 — Invented API Calls:** Severity: HIGH
> - In added lines: find method calls on imported modules (e.g., `library.someMethod()`)
> - For each: verify the method exists on that module. For local modules, Read the source. For packages, Grep node_modules or use documentation.
> - Call to nonexistent method = HIGH
> - Evidence: the call and the actual API
>
> **Vector D3 — Nonexistent File References:** Severity: HIGH
> - In added lines: find string references to file paths (config files, data files, image paths, route references)
> - For each: Glob to verify the file exists
> - Reference to nonexistent file = HIGH
> - Evidence: the reference and missing file
>
> **Vector D4 — Fabricated Config Keys:** Severity: MEDIUM
> - In added lines: find configuration keys, environment variable references, CLI flags
> - For env vars: check `.env`, `.env.example`, `.env.local` for the variable name
> - For config keys: check against the library's actual configuration schema
> - Nonexistent config key = MEDIUM
> - Evidence: the config reference
>
> End with findings summary block.

### Agent 6: Semantic Hallucination (Vectors D5-D8)

**Agent tool prompt:**

> Audit recent git changes for semantic hallucination patterns. Project: [cwd]. Diff range: HEAD~N..HEAD.
>
> **Vector D5 — Phantom Test Coverage:** Severity: HIGH
> - In added/modified test files: read each test
> - Check: does the test actually test what its description claims?
> - Look for: tests that always pass (no real assertion), assertions on hardcoded values instead of function output, mocked everything so nothing real is tested, describe/it text that doesn't match the test body
> - Phantom test = HIGH
> - Evidence: the test and what it actually tests vs what it claims
>
> **Vector D6 — Dead Code Addition:** Severity: LOW
> - In added lines: find functions, variables, or exports that are never referenced anywhere in the codebase
> - Grep for each new function/export name across the project
> - Added but unreferenced = LOW
> - Evidence: the unreferenced addition
>
> **Vector D7 — Inconsistent Type Signatures:** Severity: MEDIUM
> - In added lines: find function signatures. Check if parameter types match actual usage at call sites.
> - Function signature doesn't match how it's called = MEDIUM
> - Evidence: the signature vs the call site
>
> **Vector D8 — Comment-Code Mismatch:** Severity: LOW
> - In added lines: find comments. Check if the comment accurately describes the code it's adjacent to.
> - Comment describes different behavior than the code = LOW
> - Evidence: the mismatched comment and code
>
> End with findings summary block.

---

## Phase 2: Aggregate & Report

After all agents return (or for modes run in main conversation):

1. **Handle failures.** If an agent failed, mark its vectors as "AGENT FAILED — could not assess." Continue with available data.

2. **Deduplicate.** Different modes/agents may flag the same issue. Merge by file:line — keep the higher severity entry.

3. **Apply severity filter.** If `--severity` flag was set, drop findings below the threshold.

4. **Count verdicts:**
   - Total vectors assessed (varies by mode — up to 46 across all modes: 16 prompt + 14 code + 8 content + 8 diff)
   - Findings per severity: CRITICAL, HIGH, MEDIUM, LOW
   - Vectors with no findings: PASS

5. **Produce report:**

```markdown
# Hallucination Audit Report — [Target Name]
**Date:** YYYY-MM-DD | **Mode(s):** [modes run] | **Scope:** [path]

## Summary
| Mode | Critical | High | Medium | Low | Status |
|------|----------|------|--------|-----|--------|
| Prompt (P1-P16) | X | X | X | X | [OK/SKIPPED/FAILED] |
| Code (C1-C14) | X | X | X | X | [OK/SKIPPED/FAILED] |
| Content (G1-G8) | X | X | X | X | [OK/SKIPPED/FAILED] |
| Diff (D1-D8) | X | X | X | X | [OK/SKIPPED/FAILED] |
| **Total** | **X** | **X** | **X** | **X** | |

## Hallucination Risk Rating

Based on findings:
- **HARDENED** — 0 critical, 0 high (this target has strong anti-hallucination measures)
- **MODERATE RISK** — 0 critical, 1+ high (some gaps but no critical fabrication paths)
- **HIGH RISK** — 1+ critical (active hallucination vectors that will produce fabricated output)
- **UNHARDENED** — no anti-hallucination measures detected at all

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
1. [top 5-10 most impactful findings with target:location]

## Vector Coverage
[list of all vectors checked with PASS/FAIL/N/A status]
```

6. **Print to conversation:** Summary table + risk rating + priority actions. Not the full report.

7. **Save report** if `--report` flag is set.

## Phase 3: Fix (only with --fix flag)

If `--fix` was passed:

### Fix Strategy by Mode

**Prompt mode fixes:**
- Add missing grounding constraints (Ground Rules section at top of prompt)
- Add tool guard prerequisites
- Add "nothing found" default instructions
- Add confidence calibration instructions
- Add research log to output format
- Reduce slot-filling pressure (make sections optional, add "N/A" guidance)
- Replace self-verification with tool-based verification
- Add `allowed-tools` to frontmatter
- Constrain narrative/analysis sections to reference only existing findings

**Code mode fixes:**
- Add schema validation on LLM responses (Zod for TS, Pydantic for Python)
- Add DOMPurify sanitization before HTML rendering
- Add URL allowlist validation before following LLM-generated URLs
- Add error handling / fallback around LLM calls
- Add "AI-generated" disclaimers to UI
- Add rate limiting on LLM-triggering endpoints
- Set max_tokens where missing

**Content mode fixes:**
- Flag fabricated URLs with `[UNVERIFIED]` markers
- Flag unsourced statistics with `[SOURCE NEEDED]` markers
- Fix internal consistency issues (count mismatches, contradictions)
- Add source attribution where missing
- Note: content fixes are suggestions, not auto-applied (generated content may need human review)

**Diff mode fixes:**
- Remove phantom imports
- Fix invented API calls to use actual methods
- Update nonexistent file references
- Fix comment-code mismatches
- Flag phantom tests for human review (cannot auto-fix test intent)

### Fix Order
1. CRITICAL — fix immediately
2. HIGH — fix next
3. MEDIUM — fix if change is <= 10 lines
4. LOW — skip (report only)

### Post-Fix Verification
- Run build command (if detected)
- Run lint command (if detected)
- Run test suite (if detected)
- If anything fails, fix the breakage before completing
- If no build/lint/test detected: "No build/test commands found — manual verification recommended."

## Anti-Hallucination Rules (for this audit itself)

These rules govern how THIS SKILL operates — preventing the auditor from hallucinating findings:

- **Never invent file paths.** Every file reference in findings must come from Grep/Glob/Read results. If a search returns no matches, the finding doesn't exist.
- **Never fabricate vector results.** If a vector check found no issues, report PASS — do not invent problems to look thorough.
- **Evidence is mandatory.** Every finding must include the actual text/code that creates risk. "May have issues" without evidence is not a finding.
- **Do not assume tool availability.** For content mode URL checks: if WebFetch/WebSearch are unavailable, flag URLs as UNVERIFIED, not as FABRICATED.
- **Severity must match evidence.** A missing best practice is LOW, not CRITICAL. Reserve CRITICAL for patterns that will definitely produce hallucinated output.
- **Count accurately.** Slot counts, finding counts, and vector tallies must be computed from actual analysis, not estimated.
- **Prompt mode reads the full file.** Do not skim or sample — read every line of every target file. Missed vectors due to incomplete reading are worse than a slow audit.
- **Diff mode uses real git output.** Always run actual git commands. Do not reconstruct diffs from memory or assume what changed.
- **Do not audit yourself.** This skill file is not a valid audit target when running in prompt mode against the skills directory. Exclude it from scope.
