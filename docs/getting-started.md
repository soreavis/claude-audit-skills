# Getting started

## Install

Run these in Claude Code:

```text
/plugin marketplace add soreavis/claude-audit-skills
/plugin install audit@soreavis-skills
```

If the install summary tells you to restart, you can instead run:

```text
/reload-plugins
```

To check it worked, type `/audit:` and see whether the commands appear. If they
do not, see [Troubleshooting](troubleshooting.md).

## Your first audit

Start with one audit on a small part of the project rather than everything at
once:

```text
/audit:audit-security --scope=src/
```

This reports findings and changes nothing. Every audit is read-only by default;
fixes only happen when you pass `--fix`.

## The four flags that matter

Most audits accept the same four. Learn these and you can drive any of them.

| Flag | What it does |
|---|---|
| `--scope=<path>` | Only look at this directory. Default is the whole project. |
| `--report` | Write the full report to `_local/reports/<audit>-<date>.md`. |
| `--fix` | Apply fixes after auditing. Off by default. |
| `--audit-only` | Report without fixing. This is already the default. |

Individual audits add their own flags — `audit-security` has `--skip-deps`,
`audit-compliance` takes extra frameworks, and so on. Each skill's own
documentation lists them.

## Running several audits at once

`audit-all` runs a group of audits and combines the output into one report:

```text
/audit:audit-all --tier=standard --report
```

Tiers are presets:

| Tier | Runs | Use when |
|---|---|---|
| `quick` | security, deploy | A fast check on a personal project or MVP |
| `standard` (default) | security, deploy, forms, a11y, responsive | Most public-facing web projects |
| `full` | hallucination, security, deep, deps, compliance, tech-stack, forms, a11y, seo, responsive, deploy | Before launching something paid, regulated, or customer-facing |

Adjust a tier instead of building a list by hand:

```text
/audit:audit-all --tier=quick --include=a11y
/audit:audit-all --tier=full --skip=compliance
```

`audit-all` does not fix anything itself. With `--fix` it passes the flag down to
each sub-audit that supports one; the rest ignore it.

## Where reports go

`--report` writes to `_local/reports/`. Add `_local/` to your `.gitignore` — the
reports quote your source code, and on a public repo that is a way to publish
code you did not mean to publish.

## A reasonable habit

Run `--tier=quick` while building, and `--tier=full --report` before a release.
Keep the release reports; `audit-diff` compares two of them and tells you what
changed since last time.

## Time and cost

`full` runs eleven audits and reads a large part of your codebase. On a big
project it takes a while and uses a substantial number of tokens. `--scope` is
the main lever if that matters to you.
