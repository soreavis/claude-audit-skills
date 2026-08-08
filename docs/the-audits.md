# The audits

Thirteen skills. Nine look for problems, three are about shipping, and one
compares reports over time.

## Picking one

| If you want to know… | Run |
|---|---|
| Can this be attacked? | `audit-security` |
| Is the code itself any good? | `audit-deep` |
| Are my dependencies a liability? | `audit-deps` |
| Will this survive a GDPR or ISO conversation? | `audit-compliance` |
| Can people with disabilities use it? | `audit-a11y` |
| Does it work on a phone? | `audit-responsive` |
| Will search engines and LLMs find it? | `audit-seo` |
| Are my forms about to be flooded with spam? | `audit-forms` |
| Does it follow this stack's conventions? | `audit-tech-stack` |
| Is my LLM output going to make things up? | `audit-hallucination` |
| Is this ready to deploy? | `audit-deploy` |
| Run a group of these | `audit-all` |
| What changed since last time? | `audit-diff` |

## Finding problems

### audit-security

33 vectors: OWASP categories, authentication, API surface, client-side issues,
and AI-specific ones. Each vector gets its own verdict, so you can see what was
checked and passed, not only what failed.

Extra flag: `--skip-deps` skips the dependency vulnerability check (vector 27),
which is the slowest part. Use it when you have already run `audit-deps`.

### audit-deep

Runs three agents in parallel over dead code, OWASP Top 10, and content
injection. Slower and broader than `audit-security`, and the two overlap.
Use `audit-security` for a focused security pass and `audit-deep` when you want
a general read on code quality as well.

### audit-deps

Licences, outdated packages, unused dependencies, bundle size, duplicates, and
known vulnerabilities. Works on Node.js, Python, Go, and Rust.

The licence check is the part people forget. A GPL dependency inside a
proprietary product is a legal problem, not a technical one, and nothing else in
this suite will notice it.

### audit-compliance

Scores seven dimensions — data handling, access control, validation,
sanitisation, audit trail, error handling, documentation — against GDPR,
ISO 27001:2022, and ISO 9001:2015. HIPAA, SOC 2, and PCI DSS are available on
request.

Report-only unless you pass `--fix`. It tells you what a compliance conversation
will ask about; it is not an audit in the certification sense and no auditor will
accept its output as evidence.

### audit-a11y

WCAG 2.1 AA: semantic HTML, alt text, keyboard navigation, contrast, form
labels, ARIA, focus management, motion preferences.

Some of WCAG cannot be checked by reading code — whether alt text is *accurate*,
whether focus order makes *sense*. This finds the mechanical failures, which are
most of them. It does not make a project accessible on its own.

### audit-responsive

Padding, breakpoints, grid collapse, stacking, sticky elements, touch target
size, overflow, typography scaling, navigation, footer. Works on Next.js, React,
Vue, static HTML, and email templates.

### audit-seo

Meta tags, structured data, crawlability, internal linking, URL structure, and
whether an LLM answering a question about your subject would find you.

### audit-forms

38 checks across spam, bots, and form-specific vulnerabilities. Detects your
stack first, then checks against it. Can harden the forms it finds with `--fix`.

Worth running on anything with a public form. Spam arrives faster than most
people expect.

### audit-hallucination

The odd one out: it audits AI-facing material rather than a web app. Point it at
prompt or skill files, code that calls an LLM API, LLM-generated content, or a
recent diff. Checks 46 vectors for things that push a model toward inventing —
missing tool guards, ungrounded claims, slot-filling pressure.

Useful if you ship anything built on an LLM. Not useful otherwise.

### audit-tech-stack

Whether the code follows its own stack's conventions: inline styles versus the
CSS framework, type safety, component structure, linting. Adapts to the stack it
detects.

## Shipping

### audit-deploy

Pre-deployment checklist: build health, debug code left in, dev URLs, env vars,
error tracking, analytics, SEO basics, legal pages, git state.

The one to run last, immediately before pushing to production. It catches the
embarrassing things — a `console.log` with a token in it, a staging URL, an
uncommitted file.

### audit-all

Runs a group and combines everything into one scorecard with a
SHIP / WARNINGS / DO-NOT-SHIP verdict. See
[Getting started](getting-started.md) for tiers and flags.

It orchestrates only. It has no checks of its own, and it does not fix anything
directly.

### audit-diff

Compares two reports from `_local/reports/` and tells you what improved, what
got worse, and what is new.

This is the argument for keeping reports. A single report tells you the state
today; two tell you the direction, which is usually the more useful number.

## Overlap

Several audits check the same ground from different angles:

- `audit-security` and `audit-deep` both cover OWASP. `audit-deep` is broader
  and slower.
- `audit-security` and `audit-deps` both check dependency vulnerabilities. Use
  `--skip-deps` on the former when running both.
- `audit-forms` and `audit-security` both look at input validation, forms in
  more depth.

Running overlapping audits is not harmful, only slower. `audit-all` tiers are
already arranged to avoid the worst of it.
