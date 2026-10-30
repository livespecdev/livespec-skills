# livespec-skills

Companion tooling for **[LiveSpec](https://livespec.dev)**, the open file format for product specifications that stay current with the code they describe.

This repository is a **Claude Code plugin**: a set of skills and subagents that let you and your coding agent author and maintain LiveSpec specs **directly on the local markdown files in your git repository**. No backend, no API, no MCP server, no proprietary app. A skill's output is a git diff you review.

Scope intent into features, specify them, frame the UX and the technical approach, implement against the acceptance criteria, and keep the spec in sync with the code.

## How it works

A LiveSpec project is any directory containing a manifest, `product-spec.yaml` or `livespec.yaml` (equivalent names; `product-spec.yaml` keeps the format's name out of your repository). The skills locate that root, read the four fixed folders (`product/`, `ux/`, `tech/`, `features/`), and read or write the markdown files according to the [format spec](https://livespec.dev). There is no hidden state: everything is plain files versioned in git.

You do not clone the LiveSpec repository or visit livespec.dev to use this. The format spec is **bundled with the plugin** at `reference/SPEC.md` (pinned to `v1.0.0-draft`, with a condensed `reference/CHEATSHEET.md`); the skills read it on demand to resolve format edge cases. Your repository only ever needs a `livespec.yaml` and the four folders.

Two ideas drive the design:

- **The software, not the work.** LiveSpec describes what the software is, not how the work is going. There is no feature `status`, no assignees, no batches. Progress is the checkbox state of spec items (`- [ ]` → `- [x]`).
- **Files are the source of truth.** Every skill produces a reviewable diff. Concept changes (product, UX, tech decisions) are proposed for your review; feature files are the work product and are written directly.

## Install

```
/plugin marketplace add livespecdev/livespec-skills
/plugin install livespec@livespec
```

The marketplace is named `livespec`, hence the `@livespec` suffix. To test a local checkout before it is published, or to develop against it, see [`INSTALL.md`](INSTALL.md).

### Updating

Refresh the marketplace before updating the plugin, otherwise the update compares against a stale clone of this repository:

```
/plugin marketplace update livespec
/plugin update livespec
```

Then restart Claude Code: an update is staged, not applied to the running session.

## The skills

Invoke a skill with its slash command, or just describe what you want and let the dispatcher route.

| Skill | What it does |
|---|---|
| `/spec-context` | Locates the project, maps its concepts and features, and bridges the spec against the codebase. Read-only orientation. |
| `/scope` | Decomposes natural-language intent into a plan of features to write or update (and concepts to extract), then writes them. |
| `/specify` | Authors or refines one feature: summary, requirements, nested acceptance criteria, assumptions, questions. |
| `/frame-ux` | Frames the user experience into the feature's `## UX` section, with optional mockup assets. |
| `/frame-tech` | Frames the technical approach into the feature's `## Tech` section, grounded in the codebase. |
| `/implement` | Works through the acceptance criteria, writes code, places `implements:` / `see-spec:` markers, and checks ACs as they pass. |
| `/finalize` | Adds tests, runs the project's quality gate, commits, and hands off to `/sync`. |
| `/sync` | Reconciles the spec with what was built: checks ACs, adds notes, promotes discovered standing rules to concepts. |
| `/declare` | Writes the pull request description of the branch: what it implements and changes in the spec, rewordings first, what was checked, what to watch. Sets it on the request with `gh` or `glab` once you confirm. |
| `/review` | Has an independent agent, with no access to the session that wrote the code, check the declaration against the diff, then the format's and the project's rules, then the code. Read-only. |
| `/review-spec` | Has an independent agent critically review features before they are built: against the project's principles, constraints and UX and tech concepts, then whether each acceptance criterion can be verified, then placement and granularity, then the framing. `--focus product|ux|tech` narrows it to one aspect when you iterate on it. Read-only, no readiness verdict. |
| `/review-pr` | Runs `/review` on an open pull request (or GitLab merge request), and `/review-spec` when it changes spec files, and posts their findings as comments, one thread each. Meant for a CI job (`--ci`, no confirmation); by hand, for someone else's request, after you confirm. |
| `/check-drift` | Reports where intent and code disagree: `[x]` items with no `implements:` marker, dangling markers, code anchored to open items. |
| `/check-spec` | Reports internal spec inconsistencies: features with no requirements, duplicate IDs, broken links, orphan concepts. |

The two `check-*` skills are read-only diagnostics backed by scripts in `scripts/` (Python 3 stdlib, no dependencies). They can also be run directly:

```bash
python3 scripts/check_spec.py  [PROJECT_ROOT] [--feature SLUG] [--json]
python3 scripts/check_drift.py [PROJECT_ROOT] [--code-root DIR] [--json]
```

Both exit 0 even when they report findings: they are diagnostics, not quality gates. Neither is the LiveSpec **validator**. Level-3 conformance (`SPEC.md` §14) is constitutive of the format and belongs in the [`livespec`](https://github.com/livespecdev/livespec) repository; these two answer editorial and spec-to-code questions that need the user's own codebase.

## Working as a team

Each person runs the skills in their own Claude Code session, on their own branch. The spec files are shared through git like the code, so the usual rules apply: branches, pull requests, review.

**Who enters where.** Nothing in the skills is tied to a role; this is the usual split in a small team.

| Who | Skills | Produces |
|---|---|---|
| Product (PM, founder) | `/scope`, `/specify`, `/review-spec` | Features with requirements and acceptance criteria, concepts proposed for review |
| Design | `/frame-ux`, `/review-spec` | The `## UX` section of a feature, `ux/` concepts proposed |
| Development | `/frame-tech`, `/implement`, `/finalize`, `/declare`, `/review` | The `## Tech` section, the code with its markers, the pull request description |
| Anyone, on someone else's work | `/review-spec`, `/review-pr`, `/spec-context` | Findings, never edits |

`/implement` does not frame a feature on its own: when `## UX` or `## Tech` is missing it asks whether to frame now, wait for whoever owns it, or code without it.

**Two ways to ship a feature.**

- **Spec and code in one pull request.** One person scopes, frames and implements on a branch. `/review-pr` runs `/review` on the change and `/review-spec` on the spec files it touches. Fits small features and teams where the developer writes the spec.
- **Spec first.** Product (and design) open a pull request with the feature file only. `/review-pr` reviews its substance with `/review-spec`; the team discusses on the request and merges it. Development then implements against the merged spec in a second pull request. Fits features where the decision is the hard part.

**Changing a delivered feature.** A checked `REQ` or `AC` whose requirement changes is not reworded: it is cancelled `[-]` with `→ Superseded by [...]` and replaced by a new item, as for UX and tech directions. The code anchored to the old item then shows up in `/check-drift`, which is the point.

**Parallel branches.** IDs are numbered per file, so two branches can both add a `REQ-4` to the same feature, and git may merge them without a conflict. `/check-spec` and `/review` report the duplicate; the branch merged second renumbers the IDs it introduced, with their markers and references (`/specify` describes the procedure, from §8.3).

**In CI.** Two jobs, neither of which ever fails a pipeline because of findings:

- **On each pull request**, `/review-pr --ci` posts the agent review on the request. It needs Claude Code and an API key in the job. Examples: [`examples/ci/`](examples/ci/).
- **On a schedule**, the two check scripts report the drift and the inconsistencies accumulated across the whole spec, which no pull request review sees. They need only Python 3, no Claude Code and no key. Example in the same folder.

## Making the skills self-trigger

Once the plugin is installed, Claude Code loads every skill's description at the start of each session and matches your request against it. So in a repository with a spec manifest, the skills already fire on their own: ask "how does the export feature work?" and `/spec-context` orients itself against the spec; say "implement the export feature" and `/implement` takes over. You rarely need to type the slash command.

That routing is model-driven and best-effort, not a hard rule keyed on the manifest. To make it reliable in a repository you work in often, add a short pointer to **that repository's** `CLAUDE.md` (the spec lives in the user's repo; this is not about editing anything in livespec-skills):

```markdown
## Specs

This repository is a LiveSpec project (see its manifest). Use the
`livespec` plugin skills to read and maintain the spec:

- At session start, or before working on any feature, use `spec-context`
  to orient against the spec.
- When scoping new work, use `scope`; to author one feature,
  `specify`; to build it, `implement`.

Keep the spec files in sync with the code: they are the source of truth.
```

`CLAUDE.md` is read into context every session, so this nudges Claude toward the skills consistently. For a hard guarantee independent of the model's judgment, configure a `SessionStart` hook in `settings.json` instead; a hook cannot invoke a skill directly, but it can inject a reminder to run `/spec-context`.

## The subagents

For heavier or isolated work, the skills can delegate to subagents in `agents/`: `qa` (checks an implementation against a feature's acceptance criteria), `strategist` (explores product opportunities from the spec), and `reviewer` (the fresh-context agent `/review` and `/review-spec` run in). They read the local files only and cannot ask you questions: they return their findings to the session that called them.

## Example project

`examples/sample-project/` is a minimal but valid LiveSpec project (a habit tracker) used to dogfood the skills. It exercises personas, a goal, a pain point, a constraint, an entity, and two linked features. Run any skill against it to see the format in practice.

## Status

Bootstrapping, against LiveSpec `v1.0.0-draft`. The format is not yet frozen, so the skills pin the `SPEC.md` sections they rely on and expect churn until `1.0.0` is locked.

## License

Apache-2.0. See `LICENSE`.
