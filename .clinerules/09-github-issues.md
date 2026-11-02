# GitHub issues in commits

When the user asks to commit or push:
- Determine the repo from `git remote get-url origin` (e.g.
  `https://github.com/{owner}/{repo}.git`).
- Fetch the open issues from the public GitHub REST API (no auth needed for a
  public repo):
      https://api.github.com/repos/{owner}/{repo}/issues?state=open
  Ignore any entry with a `pull_request` key (those are PRs, not issues).
- Match the issue titles/bodies against the pending changes (`git diff` / staged
  diff) and the commit message being written.
- If the match is strong/clear, add `Closes #N` (or `Fixes #N` / `Resolves #N`)
  to the commit message yourself, referencing every issue that is addressed.
- If the match is uncertain, propose the reference and confirm with the user
  before adding it.
- Never invent issue numbers — only reference issues that were actually fetched.
- If the API is rate-limited or the repo is private, fall back to asking the user
  to review the issues (or to provide a `GH_TOKEN`).
