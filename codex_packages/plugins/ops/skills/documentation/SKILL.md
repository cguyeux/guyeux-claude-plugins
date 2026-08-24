---

name: documentation
description: "Write and maintain technical documentation. Trigger with \"write docs for\", \"document this\", \"create a README\", \"write a runbook\", \"onboarding guide\", or when the user needs help with any form of technical writing : API docs, architecture docs, or operational runbooks."
---

# Technical Documentation

Write clear, maintainable technical documentation for different audiences and purposes.

## Document Types

### README
- What this is and why it exists
- Quick start (< 5 minutes to first success)
- Configuration and usage
- Contributing guide

### API Documentation
- Endpoint reference with request/response examples
- Authentication and error codes
- Rate limits and pagination
- SDK examples

### Runbook
- When to use this runbook
- Prerequisites and access needed
- Step-by-step procedure
- Rollback steps
- Escalation path

### Architecture Doc
- Context and goals
- High-level design with diagrams
- Key decisions and trade-offs
- Data flow and integration points

### Onboarding Guide
- Environment setup
- Key systems and how they connect
- Common tasks with walkthroughs
- Who to ask for what

### Research code documentation

Documentation for an analysis repository has a different reader and a different
failure mode from product documentation. The reader is a reviewer, a co-author, or
the same person in eighteen months, and the failure mode is a result that cannot
be reproduced rather than an endpoint that cannot be called.

- **Every script states its inputs, its outputs and the command that produced the
  result in the paper.** A script whose invocation is not recorded is a result
  that cannot be checked.
- **Pin what varies.** Reference genome and version, database snapshot date, tool
  versions, random seed, thresholds. "We used the WHO catalogue" is not
  reproducible; "WHO catalogue v2, downloaded 2026-03-14" is.
- **Record what was excluded and why.** The filtering decisions are usually more
  consequential than the analysis, and they are what a reviewer will ask about.
- **Separate the narrative from the reference.** The lab notebook carries the
  chronology, the state file carries what is currently proven, the README carries
  how to run it. Do not let one drift into doing the job of another.
- **Do not document what the code already says.** A docstring restating the
  function signature is maintenance debt. Document the choices the code cannot
  express: why this threshold, why this outgroup, why this test.

## Principles

1. **Write for the reader** : who is reading this and what do they need?
2. **Start with the most useful information** : do not bury the lede
3. **Show, do not tell** : code examples, commands, screenshots
4. **Keep it current** : outdated docs are worse than no docs
5. **Link, do not duplicate** : reference other docs instead of copying
6. **Write down the failure you just debugged** : the thing that cost two hours
   and is not obvious from the code is the highest-value sentence in the document

## Related

For a research project, the structured artifacts (`cahier_de_labo.md`,
`etat_des_decouvertes.md`, `pistes.md`) have their own dedicated skills and
conventions; this skill covers the technical documentation around them (README,
runbooks, architecture notes).

## Codex workflow guardrail

This packaged copy imports a Claude-origin project workflow into Codex. Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, archiving a project, or launching remote compute, require an explicit user request in the current turn. Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files are moved to the trash rather than permanently deleted.
