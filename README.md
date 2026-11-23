# repo-onboard

A reusable **install-and-configure patch** for Claude Code: it gives any repo the setup first
built by hand for [sharons-cookbook](https://github.com/tancookjr-ops/sharons-cookbook) —
in one guided pass.

- **ICM workspace**: a small `CLAUDE.md` map, `CONTEXT.md` contracts, pipelines with human
  checkpoints (via [icm-architect](https://github.com/tancookjr-ops/icm-architect)).
- **Rules and working practices** adapted from BorealCodex (data safety, one source of truth,
  branches, guarded folders, supply chain, secrets, pickup/handoff).
- **Deploys**: staging on every push, one-click Promote, GitHub Pages fallback with a
  sandboxed `/staging/`, optional FTP — plus content checks and mirror-drift checks as gates.
- **Supply chain**: SHA-pinned actions, Dependabot with a 7-day cooldown, committed lockfiles,
  `npm ci --ignore-scripts`, audit-driven upgrades.
- Optional **design-tool backup import** with every known tool fix applied automatically.

## Use it
In a Claude Code session on the repo to set up, say:

> **onboard this repo with repo-onboard**

That shorthand works because the owner's cloud environment installs this skill at the
start of every session (setup script → `~/.claude/skills/repo-onboard`). In an
environment without it, use the full form:
`onboard this repo with https://github.com/tancookjr-ops/repo-onboard`.

**Existing repos are safe.** The patch reads the repo's own agent docs, rules and
workflows first (`kit/scripts/existing.py`), writes in *their* layout (e.g. `AGENTS.md`
maps, a `docs/` shelf, their `SECRETS.md`), never overwrites a file (overlaps become
`*.onboard-new` and are merged by `references/merge-policy.md`: keep theirs, add only what
is missing, move — never reword — to reach ICM shape), never touches existing workflows,
and `kit/scripts/preserved.py` proves every original line still exists before the PR.

Claude clones this kit, surveys the repo, asks a few rounds of multiple-choice questions,
shows one proposal for your approval, then applies, verifies against your real branches,
opens one pull request, merges it (if you allowed), watches the staging deploy and fixes
failures. It never promotes to production — that stays your call.

## What is in here
| Path | What |
|---|---|
| `SKILL.md` | the workflow Claude follows (phases 0–7) |
| `intake/questions.md` · `intake/answers.example.json` | the question rounds · a filled example (sharons-cookbook) |
| `kit/apply.py` · `kit/templates/` | renders the files from the answers; never overwrites (conflicts → `.onboard-new`) |
| `kit/scripts/` | `inventory.py` + `existing.py` (read-only surveys), `verify.sh` + `preserved.py` (pre-PR proof), `import-design-backup.sh`, and the installed `package-site.sh` / `sync-mirrors.sh` |
| `references/merge-policy.md` | how onboarding merges into a repo's existing docs and rules |
| `references/lessons.md` | why each step exists — what the by-hand run cost |
