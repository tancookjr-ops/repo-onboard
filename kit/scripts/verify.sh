#!/usr/bin/env bash
# verify.sh — prove an onboarded repo will deploy BEFORE opening the pull request.
#
#   bash verify.sh <repo-dir> <staging-branch> <production-branch> [base-ref]
#   base-ref (e.g. the staging tip before onboarding) also runs preserved.py: nothing lost.
#
# Lesson baked in: the first deploy of sharons-cookbook failed because packaging
# was only tested on the working tree, not on the real production branch.
# So this packages the WORKING TREE as staging (what the PR will land) and the
# LIVE production branch as production (what Pages republishes in the same run),
# using the working tree's scripts — exactly what pages.yml does.
set -uo pipefail
REPO="$(cd "${1:?repo dir}" && pwd)"; STAGING="${2:?staging branch}"; PRODUCTION="${3:?production branch}"
cd "$REPO"
TMP="$(mktemp -d)"; trap 'git -C "$REPO" worktree remove --force "$TMP/prod" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
fail=0; ok() { echo "✔ $*"; }; bad() { echo "✖ $*"; fail=1; }

if [ -f scripts/package-site.sh ]; then
  git fetch -q origin "$PRODUCTION" "$STAGING" 2>/dev/null || bad "could not fetch $PRODUCTION / $STAGING from origin"
  if git worktree add -q --detach "$TMP/prod" "origin/$PRODUCTION" 2>/dev/null; then
    bash scripts/package-site.sh "$TMP/prod" "$TMP/site" production >/dev/null 2>"$TMP/p.err" \
      && ok "production ($PRODUCTION) packages$(grep -q '⚠' "$TMP/p.err" && echo ' — with warnings (see below)')" \
      || bad "production ($PRODUCTION) does not package"
    sed 's/^/    /' "$TMP/p.err"
  else bad "no origin/$PRODUCTION to package"; fi
  bash scripts/package-site.sh . "$TMP/site/staging" staging >"$TMP/s.out" 2>&1 \
    && ok "staging (working tree) packages and sandboxes" || { bad "staging does not package"; sed 's/^/    /' "$TMP/s.out"; }
fi

shopt -s nullglob
for c in scripts/check-*; do
  case "$c" in *.mjs|*.js) cmd=(node "$c") ;; *.sh) cmd=(bash "$c") ;; *.py) cmd=(python3 -I "$c") ;; *) continue ;; esac
  "${cmd[@]}" >"$TMP/c.out" 2>&1 && ok "$c: $(tail -1 "$TMP/c.out" | sed "s/^✔ //")" || { bad "$c failed"; tail -15 "$TMP/c.out" | sed 's/^/    /'; }
done
[ -f scripts/sync-mirrors.sh ] && { bash scripts/sync-mirrors.sh --check >"$TMP/m.out" 2>&1 && ok "$(tail -1 "$TMP/m.out" | sed "s/^✔ //")" || { bad "mirrors drifted"; sed 's/^/    /' "$TMP/m.out"; }; }

python3 -I - "$REPO" "${4:-}" <<'PY' || fail=1
import glob, os, re, subprocess, sys
repo, base = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else ''); os.chdir(repo); bad = 0
# Files the onboarding touched (vs base): problems there FAIL; problems in untouched files only WARN.
changed = None
if base:
    out = subprocess.run(['git', 'diff', '--name-only', base], capture_output=True, text=True).stdout.split()
    out += subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], capture_output=True, text=True).stdout.split()
    changed = set(out)
try:
    import yaml
    for f in sorted(glob.glob('.github/*.yml') + glob.glob('.github/workflows/*.yml')):
        d = yaml.safe_load(open(f))
        for job in (d.get('jobs') or {}).values():
            for st in job.get('steps') or []:
                u = st.get('uses', '')
                if u and not u.startswith('./') and not re.search(r'@[0-9a-f]{40}$', u):
                    if changed is None or f in changed:
                        print(f'✖ {f}: action not SHA-pinned: {u}'); bad = 1
                    else:
                        print(f'⚠ {f}: action not SHA-pinned: {u} (pre-existing — report to the owner, workflows are never edited by onboarding)')
    print('✔ workflow YAML parses; actions added by onboarding are SHA-pinned' if not bad else '')
except ImportError:
    print('⚠ PyYAML missing — workflow YAML not checked')
def lines(f): return sum(1 for _ in open(f)) if os.path.exists(f) else 0
entry = 'CLAUDE.md'
if lines('CLAUDE.md') <= 3 and os.path.exists('AGENTS.md'): entry = 'AGENTS.md'   # CLAUDE.md is a pointer
n = lines(entry)
print(f"{'✔' if 0 < n <= 60 else '✖'} {entry} (entry) is {n} lines (target ≤ 60)"); bad |= not (0 < n <= 60)
# walk test: paths named in the catalog files exist (warnings only)
# catalog files only: entry, overview, floor maps, work contracts, and the shelf docs onboarding writes
docs = ['CLAUDE.md', 'AGENTS.md', 'CONTEXT.md'] + glob.glob('**/AGENTS.md', recursive=True) + glob.glob('**/CONTEXT.md', recursive=True) \
     + [f for f in glob.glob('*/*.md') if os.path.basename(f) in ('rules.md', 'working-practices.md', 'release-process.md', 'secrets.md')]
docs = [d for d in dict.fromkeys(docs) if 'node_modules' not in d and '/.claude/' not in d and not d.startswith('.claude/')]
miss = []
for f in docs:
    if not os.path.exists(f): continue
    for p in re.findall(r'`((?:\.\./)*[_a-zA-Z0-9.][_a-zA-Z0-9./-]*/?)`', open(f).read()):
        if '/' not in p or '<' in p or p.startswith('http'): continue
        if not any(os.path.exists(os.path.normpath(os.path.join(b, p))) for b in (os.path.dirname(f), '.')):
            miss.append(f'{f}: {p}')
print(f"✔ walk test: every path in the catalog exists" if not miss else f"⚠ walk test: {len(miss)} path(s) not found (check they are meant to be):\n    " + "\n    ".join(miss[:20]))
sys.exit(bad)
PY

if [ -d design-system/tools/node_modules ]; then
  (cd design-system/tools && npm run -s check 2>&1 | tail -1) | grep -q "^0 errors" && ok "design-system check: 0 errors" || bad "design-system check has errors"
fi

if [ -n "${4:-}" ]; then
  python3 -I "$(dirname "$0")/preserved.py" "$REPO" "$4" || fail=1
fi

echo; [ "$fail" = 0 ] && echo "VERIFY: PASS" || echo "VERIFY: FAIL"
exit "$fail"
