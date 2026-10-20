---
name: review-pr
description: |
  Runs the independent /review on an open pull request (merge request on GitLab) and posts its
  findings as comments on it, one thread per finding plus a summary, after the user confirms. Use
  when the user asks to review a PR or an MR and leave comments on it. For a review before pushing,
  use /review.
argument-hint: "[pull request number, default the current branch's]"
disable-model-invocation: true
---

# Review a pull request

You post an independent review on a pull request (a merge request on GitLab). You do not review it yourself: `/review` does, in a fresh context. Your job is the plumbing around it.

## Step 1: Find the request

Detect the host from `git remote -v`: GitHub uses `gh`, GitLab uses `glab`. If the CLI is missing or not authenticated, say so and stop.

Request = `$ARGUMENTS`, or the one opened from the current branch (`gh pr view` / `glab mr view`). Read its target branch, its head commit and its description. If the local `HEAD` differs from the request's head commit, say so and ask whether to fetch it first: a review of another commit is worthless on this request.

## Step 2: Hand the declaration to the review

Write the request description to `.pr-description.md` (git-ignored; if a local one exists and differs, ask which one is authoritative before overwriting it). This is the only material you pass along.

## Step 3: Run the review

Run `/review <target branch>`. Pass nothing else: no summary of the change, no opinion. Its independence depends on it.

## Step 4: Skip what is already posted

Read the request's existing comments (`gh pr view --comments` / `glab mr view --comments`). Drop a finding already posted by an earlier agent review on the same file and line with the same substance, and list it as already posted.

## Step 5: Confirm, then post

Show the user the comments as they will appear: one per finding, then the summary. Each finding comment starts with `**Agent review** · <fix | decide> · <kind> · \`file:line\``, in the language of the review. Post nothing before the user confirms; they may drop or edit findings.

On confirmation, post each one as its own comment so that it becomes a thread resolved by a fix or an answer:

- GitHub: `gh pr comment <id> --body "<comment>"`;
- GitLab: `glab mr note <id> --message "<comment>"`.

Report what was posted. Do not approve, merge or resolve threads.
