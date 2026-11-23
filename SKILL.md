---
name: repo-onboard
description: Shorthand trigger — "onboard this repo with repo-onboard". Install and configure the full "sharons-cookbook" setup on another repo in one guided pass, adapting to (never overwriting) the repo's existing agent docs, rules and workflows — ICM workspace (CLAUDE.md map, CONTEXT.md contracts, pipelines with human checkpoints), BorealCodex-derived rules and working practices, GitHub Actions deploys (staging on push, one-click promote, GitHub Pages fallback with a sandboxed /staging/, optional FTP), mirror-drift and content checks, Dependabot cooldown, SHA-pinned actions, and optional import of a design-tool backup zip. Use when the user asks to onboard, set up, bootstrap, patch or "update this repo the same way" as sharons-cookbook, or to apply the repo-onboard patch.
---

# repo-onboard — the installation and configuration patch

One intake, one approval, then automated: inventory → apply → verify → pull request →
merge → watch the deploy → fix loop. The owner is asked everything **up front**; after
the approval gate, only failures that need them interrupt.

The kit: `kit/apply.py` (renders `kit/templates/` from an answers file),
`kit/scripts/` (`inventory.py`, `verify.sh`, `import-design-backup.sh`, plus the
`package-site.sh` / `sync-mirrors.sh` it installs). Why each step exists:
`references/lessons.md`. A filled example: `intake/answers.example.json`.
Question bank and answer mapping: `intake/questions.md`.

## Phase 0 — Get the kit and the target (automatic)
1. Target repo checked out; if the session lacks it, `add_repo` it (push access).
2. The kit lives in ONE place: `https://github.com/tancookjr-ops/repo-onboard`. Clone it
   (shallow) into the session's scratchpad and run it from there — never commit a copy of
   the kit into the target (one home per fact; the target's CLAUDE.md links here instead).
3. If `install_icm_architect`: clone `https://github.com/tancookjr-ops/icm-architect` (shallow)
   into `.claude/skills/icm-architect/` (SKILL.md, LICENSE, README.md, references/, assets/ only).
4. Branch: `<work_prefix>onboard` from the staging branch (create the staging branch from
   the default branch only if the owner said to).

## Phase 1 — Inventory (automatic, read-only)
`python3 -I kit/scripts/inventory.py <repo> --json <scratchpad>/facts.json` and
`python3 -I kit/scripts/existing.py <repo> --json <scratchpad>/existing.json` — the second
finds the repo's OWN agent docs, rules, secrets/runbooks and workflows: which entry file
is canonical, the folder-map file name, the knowledge shelf, ICM conformance, which
onboarding rule topics they already cover, duplicated facts, workflow name collisions,
and proposes `paths` + `modules` (e.g. deploy off when the repo deploys itself).
Record the base ref now (`git rev-parse origin/<staging>`) for the Phase 5 preservation check.
Use the facts to **prefill every intake default**: branches, staging/production guess,
storage prefixes (sandbox), mirror candidates, CDN tags without integrity, design backup,
personal emails, lockfiles ignored. Also read the README and any existing CLAUDE.md /
AGENTS.md so the project summary and jobs are proposed, not asked cold.

## Phase 2 — Intake (the input interface)
Ask with **AskUserQuestion**, in the rounds of `intake/questions.md` (≤4 questions each,
recommended option first, defaults from Phase 1). Every question also accepts free text.
- Ask the **device/session** round first: it decides how uploads and owner steps are given.
- **Uploads:** a design backup or other large file goes through a GitHub **Release asset**
  (`https://github.com/<repo>/releases/new`, tag `onboard-upload`, *Publish*, not draft) —
  works from an iPad and up to 2 GB. Public repo → download it directly; private → the owner
  downloads/attaches or the session uses its GitHub access. Never ask for files in chat.
- **Secrets:** never asked for. Name the GitHub secrets; the owner enters values in Settings
  (or the environment's credential form).
- Save answers to `<scratchpad>/answers.json` (schema = `intake/answers.example.json`).

## Phase 3 — Proposal and approval (the one gate before changes)
Show in one message: target tree, migration map (old → new → role, from icm-architect
restructure mode), files to be written, duplicates → mirror/archive/delete, automation
level, the owner's settings checklist — and, when the repo has its own docs, the
**merge plan** from `references/merge-policy.md`: conventions adopted, ICM fixes (moves,
never rewording), per topic keep / add / ignore, and the true conflicts as questions. Ask **Approve / Change something** with
AskUserQuestion. Nothing is written before "Approve". If the owner chose "delete" for a
duplicate, that is the only deletion the patch makes.

## Phase 4 — Apply (automatic)
1. Design backup (if any): `bash kit/scripts/import-design-backup.sh <repo> <zip-or-url>`
   (applies the known tool fixes itself), then remove duplicates the owner chose to delete.
2. `python3 -I kit/apply.py answers.json <repo>` — writes only files that don't exist, in the
   repo's own conventions (`paths`), for the chosen `modules`. It never overwrites: each
   existing file stays as is and gets a `<file>.onboard-new` beside it.
3. **Merge** every `.onboard-new` by `references/merge-policy.md` (keep theirs, add only
   what is missing, ignore what doesn't apply, move — never reword — to reach ICM shape),
   log each decision in `<archive_dir>/onboarding-merge.md`, ask the owner only about
   true conflicts, then delete the `.onboard-new` files.
4. Fill every `{{FILL: …}}` in the `work/*/NN_*/` contracts (`CONTEXT.md` or the repo's floor-file name) with **icm-architect** (build mode,
   step 4) from what the inventory and README show. Add a content checker as
   `scripts/check-<thing>.(mjs|sh|py)` if the content has a structure (see sharons-cookbook's
   `scripts/check-recipes.mjs` for the pattern). Leave a `{{FILL}}` only if the owner must decide.
5. `bash scripts/sync-mirrors.sh` (mirrors start identical).
6. Supply chain: un-ignore and commit lockfiles of any tooling, `npm ci --ignore-scripts`.

## Phase 5 — Verify (automatic; never open a PR on a FAIL)
`bash kit/scripts/verify.sh <repo> <staging> <production>` — packages the working tree as
staging AND the live production branch as production, runs every `scripts/check-*`, mirror
check, SHA-pin check, CLAUDE.md length, walk test. On FAIL: read the output, fix, re-run.
A production *warning* (live site already missing a file) is reported, not blocking.
Then `python3 -I kit/scripts/preserved.py <repo> <base-ref>` — must print `✔ preserved`
(every line of every pre-existing doc and workflow still exists somewhere).

## Phase 6 — Ship (automatic up to the automation level chosen)
1. One commit per concern on the onboard branch (Conventional Commits), push.
2. Open ONE pull request into the staging branch (mirror any PR template's headings).
3. `auto_merge: true` → merge it (`merge_pull_request`, method from answers) — **only if the
   owner's settings checklist items that block the first deploy are confirmed done** (Pages
   source = GitHub Actions). Otherwise stop and say what is missing.
4. Watch **Deploy to Staging** (or, when the repo keeps its own deploys, its own staging
   workflow and **Repo checks**) for the merge commit (`actions_list` → the run for that
   commit). Don't sleep-poll in the foreground; wait with the tools the session offers.
5. Failure → `get_job_logs` (failed only) → diagnose from the exact text → fix on a new
   `<work_prefix>onboard-fix-N` branch from the staging branch → verify → PR → merge → watch.
   At most `max_fix_rounds`; then stop and report with the log excerpt.
6. **Never promote.** Production is the owner's release check, always.

## Phase 7 — Hand over
- Entry at the top of `work/LEDGER.md` (what changed with PR links, what waits on the owner).
- Final message: what was installed, verify/deploy results, staging URL to check, the owner
  checklist with direct links, and anything not verified.

## Rules while running
- Follow the target's own `CLAUDE.md` once it exists; before that, `_shared/rules.md` of this kit's templates.
- Plain language to the owner; device-appropriate steps; one owner action at a time.
- Report exactly what ran and what it printed; never claim a check you did not run.
