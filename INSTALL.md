# Installing and testing livespec-authoring

`livespec-authoring` is a Claude Code plugin: a set of skills and subagents that author and maintain LiveSpec specs on the local markdown files in your repository. This guide covers installing it for real use, testing a local checkout before it is published, and iterating on it during development.

All commands below are typed at the Claude Code prompt unless prefixed with a shell `$`.

## Prerequisites

- A recent Claude Code (the plugin system, `/plugin`, and `/reload-plugins` must be available).
- A git repository to work in. The plugin reads and writes plain files and shows you diffs.
- Either an existing LiveSpec project (any directory containing a `livespec.yaml`) or the bundled `examples/sample-project/` to try the skills against.

You do **not** need to clone the LiveSpec format repository or visit livespec.dev. The format spec is bundled inside the plugin at `reference/SPEC.md`.

## Option A: install from GitHub (normal use)

Once the repository is published:

```
/plugin marketplace add etherond/livespec-authoring
/plugin install livespec-authoring@livespec
```

- The first command registers this repo as a plugin marketplace. The marketplace is named `livespec` (from `.claude-plugin/marketplace.json`).
- The second installs the `livespec-authoring` plugin from that marketplace. The `@livespec` suffix names the marketplace to install from.

To pin a specific tag or branch:

```
/plugin marketplace add etherond/livespec-authoring#v0.1.0
```

## Option B: test a local checkout (before publishing)

If you have this repository checked out locally and want to test it without pushing, add the local directory as a marketplace:

```
/plugin marketplace add /path/to/livespec-authoring
/plugin install livespec-authoring@livespec
```

The path points at the repository root (the directory containing `.claude-plugin/`), not at the `.claude-plugin/` folder itself. A relative path such as `./livespec-authoring` also works.

### Faster dev loop: `--plugin-dir`

For active development, launch Claude Code with the plugin loaded directly from disk, with no marketplace and no caching:

```
$ claude --plugin-dir /path/to/livespec-authoring
```

This loads the plugin in-place, so edits to skills and agents are picked up without a cache copy. This is the recommended way to iterate on the skill prose.

## Verify it loaded

```
/plugin list
```

You should see `livespec-authoring` enabled. Its skills become available as slash commands:

```
/livespec-context
/scope-features
/specify-feature
/frame-ux
/frame-tech
/implement-feature
/finalize-feature
/sync-spec
```

The subagents (`specifier`, `ux-framer`, `tech-framer`, `architect`, `qa`, `strategist`) become available to the Agent tool. Skills and agents are discovered by convention from the plugin's `skills/` and `agents/` directories; there is no registration step.

If the plugin namespaces its commands, they may appear as `/livespec-authoring:livespec-context` and so on. `/plugin details livespec-authoring@livespec` shows exactly what was registered.

## Smoke test

The quickest end-to-end check uses the bundled fixture.

1. Point Claude Code at the sample project (open that folder, or copy it somewhere and `cd` in):

   ```
   $ cd /path/to/livespec-authoring/examples/sample-project
   ```

2. Run orientation:

   ```
   /livespec-context
   ```

   It should locate `livespec.yaml`, report the project as "Habit Tracker (Sample)" in loose mode, list the concepts (persona, goal, pain_point, constraint, entity) and the two features under `features/habits/`, and read progress from the checkbox state (all ACs open).

3. Try authoring:

   ```
   /specify-feature view-streaks
   ```

   It should propose a new feature file with a summary paragraph, REQs with nested ACs, and links to the relevant concepts, and write `features/habits/view-streaks.md` after you approve. Review the diff: the file must be valid LiveSpec (immutable sequential IDs, ACs nested two spaces, no empty frontmatter block).

Because the sample project is a git-tracked fixture, `git diff` and `git checkout` let you inspect and reset anything the skills write.

## Iterating during development

After editing a skill or agent in this repo:

```
/reload-plugins
```

This picks up changes to skills, agents, and configuration without restarting Claude Code. If you launched with `--plugin-dir`, reload still applies.

## Updating an installed copy

If you installed from a marketplace (Option A or B), updates are controlled by the `version` field in `plugin.json`. Bump `version` to ship changes to installed users; pushing commits without bumping it has no effect, because Claude Code keeps the cached copy for the same version string. During development, prefer `--plugin-dir` to avoid the cache entirely.

## Uninstall

```
/plugin uninstall livespec-authoring@livespec
/plugin marketplace remove livespec
```

## Troubleshooting

- **`/plugin install` cannot find the plugin.** Confirm the marketplace was added (`/plugin marketplace list`) and that you used the `@livespec` suffix. The name after `@` is the marketplace name (`livespec`), not the plugin name.
- **Skills do not appear after editing.** Run `/reload-plugins`. If you installed from a marketplace rather than `--plugin-dir`, the cached copy may be stale; bump `version`, or re-add the local marketplace, or switch to `--plugin-dir` for development.
- **A skill cites `SPEC.md §N` but cannot read the spec.** The spec is bundled at `reference/SPEC.md` and referenced by relative path from each skill. This works only when `reference/` ships inside the plugin (it does). If you restructured the repo, keep `reference/` at the plugin root.
- **Format reference seems out of date.** `reference/SPEC.md` is a vendored copy pinned to a format version (see `reference/README.md`). Re-vendor from the `livespec` repo when the format bumps.
