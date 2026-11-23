# Merge policy — onboarding a repo that already has its own docs and rules

The owner's existing rules and documents are never obliterated. Onboarding adapts to
them; it only **adds what is missing** and **re-homes what is out of ICM shape** — and
`kit/scripts/preserved.py` proves afterwards that every original line still exists.

Inputs: `existing.py` report (conventions, roles, ICM checks, topic coverage, duplicates,
workflows), `apply.py` report (written / conflicts / skipped), the answers.

## 1. Adopt their conventions (apply.py does this from `paths`)
Entry file (CLAUDE.md or AGENTS.md — keep whichever is canonical; the other stays a
pointer), folder-map name (`AGENTS.md` or `CONTEXT.md`), knowledge shelf (`docs/`,
`_shared/`, …), secrets file, release doc. **Never introduce a parallel name**: no
`CONTEXT.md` beside `AGENTS.md` floor maps, no `_shared/` when `docs/` is the shelf, no
second hand-kept entry file. If existing.py's guess is wrong, fix `paths` and re-run.

## 2. Is it ICM? Fix shape by moving, never by rewording
For each ✖ in existing.py's ICM checks:

| Finding | Do |
|---|---|
| entry file > 60 lines / holds payload | move payload sections into the floor map or shelf doc they belong to; leave a one-line route or law in the entry |
| floor map doesn't say what to read / what it produces | add one "Read first: … · Produces: …" line; keep the rest as is |
| CLAUDE.md and AGENTS.md both hold content | make the less-used one a pointer *after* moving any unique lines into the canonical one (ask which is canonical if unclear) |
| same fact in 2+ files | keep it in the most specific home; replace the other copies with a link |
| no ICM at all (no entry, scattered docs) | run icm-architect **Restructure mode** (inventory → classify catalog / contract / factory / product / dead → migration map) and put the map in the Phase 3 proposal |

Moving and splitting are allowed; changing the wording of an existing rule is not
(except the owner's explicit choice in step 5).

## 3. Merge each conflict (`<file>` kept, `<file>.onboard-new` beside it)
Go section by section through the `.onboard-new`, against the existing file and
existing.py's `topic_coverage`:

| Situation | Decision |
|---|---|
| theirs covers the topic with the same intent | **KEEP theirs** verbatim; add only what ours *enforces* that theirs lacks, as one line |
| theirs covers it with a different intent (true conflict) | **KEEP theirs**; list it for the owner (step 5); never silently change |
| theirs is silent on the topic | **ADD ours**, rewritten in their vocabulary, branch names and paths, at the matching place in their file |
| ours does not apply here (Pages/FTP in a VPS repo; browser-storage rules in a database app) | **IGNORE ours**; note why |
| project-specific laws in theirs (payments, CSP, framework quirks, brand) | **KEEP**, untouched, in place |

File-specific:
- **Entry file** — keep their map and laws; add only missing routes (`work/` pipelines,
  pickup/handoff, rules and practices links). Stay ≤ 60 lines: if additions push it over,
  move payload out (step 2) rather than dropping anything.
- **Secrets file** — keep theirs; add the "never in chat — use the credential form" law
  and rotation rows only if missing.
- **Floor maps** (`.github/`, `scripts/`, `deploy/`, …) — keep theirs; add only missing
  kit laws (SHA pins, `contents: read`, impact summary before change).
- **New shelf docs the kit created** (`rules.md`, `working-practices.md`) — must not
  duplicate laws that already live elsewhere: for every topic theirs covers, replace our
  text with a link to their home; keep our text only for topics they lack.
- **dependabot.yml** — never replace; add a missing ecosystem or `cooldown` to *their*
  entries only if absent; keep their directories, schedules, groups, branches.
- **Workflows** — never replace, rename or edit an existing workflow. Overlapping deploys
  → the deploy module stays off. Add `repo-checks.yml` only if no gate runs `scripts/check-*`.

## 4. Record every decision
`<archive_dir>/onboarding-merge.md` — one row per decision:
`| file | section / topic | keep / add / merge / move / ignore / ask | reason |`.
Then delete each `.onboard-new` (its useful content now lives in the real file).

## 5. Ask only about real conflicts
One AskUserQuestion round (≤ 4 per round): for each true conflict, show both versions
briefly; options **Keep yours (Recommended)** · Adopt the onboarding version · Merge both.

## 6. Prove nothing was lost
`python3 -I kit/scripts/preserved.py <repo> <base-ref>` must print `✔ preserved` before
the pull request. Any ✖ line means content was dropped — put it back (or move it to its
ICM home) and re-run. Never open the PR on a ✖.
