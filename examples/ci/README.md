# CI examples

Starting points, to copy into your repository and adapt. Pin the same plugin version as your team uses (`livespec--v0.8.3` here).

| File | Runs | Needs |
|---|---|---|
| `github-review-pr.yml`, `gitlab-review-pr.yml` | `/review-pr --ci` on each pull or merge request: the agent review, posted as resolvable threads | Claude Code, `ANTHROPIC_API_KEY`, a token that can comment |
| `github-spec-health.yml`, `gitlab-spec-health.yml` | The two check scripts on a schedule, over the whole spec | Python 3 only |

None of them fails a pipeline because of findings: they report, people decide. The review jobs fail only when the review could not run (wrong commit checked out, missing authentication).

The review examples have not been run end to end yet. Two points are not covered by Claude Code's documentation and need one manual run: a skill marked `disable-model-invocation` invoked as the prompt of `claude -p`, and `glab` authentication in your GitLab image.
