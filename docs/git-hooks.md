# Git hooks

Hooks live in [`.githooks/`](../.githooks) and are versioned with the repo.
Git does not enable versioned hooks automatically — run once per clone:

```bash
git config core.hooksPath .githooks
```

## `commit-msg`

Strips AI-tool attribution lines from every commit message before the commit
is created. Removed lines (case-insensitive):

- `Generated with [Claude Code](...)` / `🤖 Generated with ...`
- `Powered by Claude Code`
- `Co-Authored-By: ...Claude...` / `...anthropic...`
- links to `claude.ai/code` or `claude.com/claude-code`

Trailing empty lines left behind are removed as well. Everything else in the
message is kept untouched.

Test it without committing:

```bash
printf 'msg\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' > /tmp/m
.githooks/commit-msg /tmp/m && cat /tmp/m    # -> "msg"
```
