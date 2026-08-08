# Documentation

Four guides. Read them in this order if you are new.

| Guide | What it covers |
|---|---|
| [Getting started](getting-started.md) | Installing the plugin, running your first audit, where reports go |
| [The audits](the-audits.md) | What each of the 13 audits checks, and which one you actually want |
| [Reading a report](reading-a-report.md) | What the verdicts mean, which findings to act on first, what the tool cannot tell you |
| [Troubleshooting](troubleshooting.md) | Commands not appearing, wrong project detected, audits taking too long |

For contributing a new audit, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## What this plugin is

Thirteen audit skills for Claude Code. Each one reads your project and reports
problems with a file and line number for each finding. Most of them can also fix
what they find, but only when you ask with `--fix`.

## What it is not

It is not a scanner in the sense of `npm audit` or a SAST tool. There is no
fixed rule engine underneath. Each audit is a set of instructions that Claude
follows against your code, which has two consequences worth knowing before you
rely on it:

- **Results vary between runs.** The same audit on the same code can find a
  slightly different set of issues. It is not deterministic.
- **It can be wrong.** Every audit is written to demand `file:line` evidence for
  each finding, which makes claims checkable. Check them. A finding without a
  line number you can open is a finding you should not act on.

Use it to find things worth looking at. Do not use it as the only gate before a
release, and do not treat a clean report as proof that a project is secure or
compliant.
