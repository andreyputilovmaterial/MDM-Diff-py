# Non-interactive terminal commands

- Always run Git with `--no-pager` and disable editors and prompts so a command can
  never block a non-interactive session:

      git --no-pager -c core.editor=true ...

  or equivalently prefix with env vars:

      GIT_PAGER=cat GIT_EDITOR=true GIT_TERMINAL_PROMPT=0 git ...

  This stops pagers (`less`), editors (`vim`), and credential/host-key prompts from
  hanging the terminal.
- Avoid interactive commands and pagers; prefer non-interactive alternatives that exit
  automatically (e.g. `git add -A` not `git add -p`; `git commit --amend --no-edit`;
  `git switch` not `git checkout -p`).
- Never use here-documents (`<<'EOF'` … `EOF`) for commit messages or scripts. The
  terminal is driven by typed text, so a long quoted block gets echoed and wrapped and
  the closing delimiter can be mangled, leaving the shell stuck at the `heredoc>` prompt.
  Use multiple `-m` flags instead, one per paragraph:

      git commit -m "subject" -m "first paragraph" -m "second paragraph"

  For a long body, write the message with `printf` to a temp file and use
  `git commit -F /tmp/commit-msg.txt`.
- Prefer commands that terminate on their own. Do not start long-running or watching
  processes (`tail -f`, `watch`, dev servers) unless required; if required, run them in
  the background and redirect output to a log file.
