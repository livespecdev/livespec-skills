# livespec-authoring

Companion tooling for **[LiveSpec](https://livespec.dev)**, the open file format for product specifications that stay current with the code they describe.

This repository is a **Claude Code plugin**: a set of skills and subagents that let you and your coding agent author and maintain LiveSpec specs **directly on the local markdown files in your git repository**. No backend, no API, no MCP server, no proprietary app. A skill's output is a git diff you review.

Scope intent into features, specify them, frame the UX and the technical approach, implement against the acceptance criteria, and keep the spec in sync with the code.

## How it works

A LiveSpec project is any directory containing a `livespec.yaml` manifest. The skills locate that root, read the four fixed folders (`product/`, `ux/`, `tech/`, `features/`), and read or write the markdown files according to the [format spec](https://livespec.dev). There is no hidden state: everything is plain files versioned in git.

You do not clone the LiveSpec repository or visit livespec.dev to use this. The format spec is **bundled with the plugin** at `reference/SPEC.md` (pinned to `v1.0.0-draft`, with a condensed `reference/CHEATSHEET.md`); the skills read it on demand to resolve format edge cases. Your repository only ever needs a `livespec.yaml` and the four folders.

Two ideas drive the design:

- **The software, not the work.** LiveSpec describes what the software is, not how the work is going. There is no feature `status`, no assignees, no batches. Progress is the checkbox state of spec items (`- [ ]` → `- [x]`).
- **Files are the source of truth.** Every skill produces a reviewable diff. Concept changes (product, UX, tech decisions) are proposed for your review; feature files are the work product and are written directly.

## Install

```
/plugin marketplace add etherond/livespec-authoring
/plugin install livespec-authoring@livespec
```

The marketplace is named `livespec`, hence the `@livespec` suffix. To test a local checkout before it is published, or to develop against it, see [`INSTALL.md`](INSTALL.md).

## The skills

Invoke a skill with its slash command, or just describe what you want and let the dispatcher route.

| Skill | What it does |
|---|---|
| `/livespec-context` | Locates the project, maps its concepts and features, and bridges the spec against the codebase. Read-only orientation. |
| `/scope-features` | Decomposes natural-language intent into a plan of features to write or update (and concepts to extract), then writes them. |
| `/specify-feature` | Authors or refines one feature: summary, requirements, nested acceptance criteria, assumptions, questions. |
| `/frame-ux` | Frames the user experience into the feature's `## UX` section, with optional mockup assets. |
| `/frame-tech` | Frames the technical approach into the feature's `## Tech` section, grounded in the codebase. |
| `/implement-feature` | Works through the acceptance criteria, writes code, places `livespec:` markers, and checks ACs as they pass. |
| `/finalize-feature` | Adds tests, runs the project's quality gate, commits, and hands off to `/sync-spec`. |
| `/sync-spec` | Reconciles the spec with what was built: checks ACs, adds notes, promotes discovered standing rules to concepts. |

## Making the skills self-trigger

Once the plugin is installed, Claude Code loads every skill's description at the start of each session and matches your request against it. So in a repository with a `livespec.yaml`, the skills already fire on their own: ask "how does the export feature work?" and `/livespec-context` orients itself against the spec; say "implement the export feature" and `/implement-feature` takes over. You rarely need to type the slash command.

That routing is model-driven and best-effort, not a hard rule keyed on `livespec.yaml`. To make it reliable in a repository you work in often, add a short pointer to **that repository's** `CLAUDE.md` (the spec lives in the user's repo; this is not about editing anything in livespec-authoring):

```markdown
## Specs

This repository is a LiveSpec project (see `livespec.yaml`). Use the
`livespec-authoring` skills to read and maintain the spec:

- At session start, or before working on any feature, use `livespec-context`
  to orient against the spec.
- When scoping new work, use `scope-features`; to author one feature,
  `specify-feature`; to build it, `implement-feature`.

Keep the spec files in sync with the code: they are the source of truth.
```

`CLAUDE.md` is read into context every session, so this nudges Claude toward the skills consistently. For a hard guarantee independent of the model's judgment, configure a `SessionStart` hook in `settings.json` instead; a hook cannot invoke a skill directly, but it can inject a reminder to run `/livespec-context`.

## The subagents

For heavier or isolated work, the skills can delegate to subagents in `agents/`: `specifier`, `ux-framer`, `tech-framer`, `architect`, `qa`, and `strategist`. They operate on the local files only.

## Example project

`examples/sample-project/` is a minimal but valid LiveSpec project (a habit tracker) used to dogfood the skills. It exercises personas, a goal, a pain point, a constraint, an entity, and two linked features. Run any skill against it to see the format in practice.

## Status

Bootstrapping, against LiveSpec `v1.0.0-draft`. The format is not yet frozen, so the skills pin the `SPEC.md` sections they rely on and expect churn until `1.0.0` is locked.

## License

Apache-2.0. See `LICENSE`.
