# 🔒 scripts/ — packaging and checks (guarded)

One job: build what gets published and refuse anything that breaks the rules.
Touch only when the task explicitly says so; give the owner an impact summary first.

| File | Does | Run by |
|---|---|---|
| [[@scripts_rows]]

## Inputs
- Reference (every run): `../_shared/rules.md` §1–2, §5–6

## Laws here
- The staging sandbox must fail loudly, never pass silently.
- Test every change on the real branches before pushing: the repo-onboard `verify.sh`
  packages the working tree as staging and the live branch as production.

**Not a scripts task?** Return to `../CLAUDE.md`.
