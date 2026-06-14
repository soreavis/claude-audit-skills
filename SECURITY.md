# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Scope

These are Claude Code skills — Markdown methodology files that read your codebase via `Grep` / `Glob` / `Read` and, only with an explicit `--fix`, edit files in the project you point them at. They do not handle credentials, make network calls, or run as a service. The most relevant security concern is a skill instructing an unsafe `--fix`; report any such case.

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Please report privately via [GitHub Security Advisories](https://github.com/soreavis/claude-audit-skills/security/advisories/new).

Include:
- Which skill and command
- Description and steps to reproduce
- Potential impact
- Suggested fix (if any)

You'll get a response as soon as possible. Please allow time to assess and patch before any public disclosure.
