#!/usr/bin/env python3
"""preserved.py — prove onboarding obliterated nothing. Part of repo-onboard.

    python3 -I preserved.py <repo-dir> <base-ref>

For every agent / rules / secrets / runbook doc and every workflow that existed at
<base-ref> (e.g. origin/develop before onboarding), checks that each meaningful line
of the original still exists somewhere in the working tree — in the same file or
moved into another one (moving content into its ICM home is allowed; losing it is
not). Exit 1 and list the missing lines if anything was lost, renamed away or deleted.
"""
import os, re, subprocess, sys

DOC = re.compile(r'(^|/)(CLAUDE|AGENTS|CONTEXT|SECRETS|CONTRIBUTING|MAP|STATE|REPO-INDEX|COMMIT-MAP|HANDOVER|LEDGER)\.md$'
                 r'|RUNBOOK|SECURITY[-\w]*\.md$|claude-repo-brief\.md$|copilot-instructions\.md$|\.cursorrules$'
                 r'|^docs/prompts/.*\.md$|^\.github/workflows/.*\.ya?ml$|^\.github/dependabot\.ya?ml$', re.I)


def git(repo, *a):
    return subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True).stdout


def norm(line):
    s = re.sub(r'[`*_>|#]', '', line)
    s = re.sub(r'^\s*([-+]|\d+\.)\s+', '', s)
    return re.sub(r'\s+', ' ', s).strip().lower()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    repo, base = os.path.abspath(sys.argv[1]), sys.argv[2]
    before = [f for f in git(repo, 'ls-tree', '-r', '--name-only', base).splitlines() if DOC.search(f)]
    if not before:
        print(f'✔ no agent/rules docs existed at {base} — nothing to preserve'); return
    # Everything text-like in the working tree (tracked or not, minus ignored) is "somewhere".
    now = set(git(repo, 'ls-files', '--cached', '--others', '--exclude-standard').splitlines())
    corpus = []
    for f in now:
        p = os.path.join(repo, f)
        if os.path.isfile(p) and os.path.getsize(p) < 2_000_000 and f.endswith(('.md', '.yml', '.yaml', '.txt', '.cursorrules', '.json')):
            corpus.append(norm(open(p, encoding='utf-8', errors='replace').read().replace('\n', ' ¶ ')))
    blob = ' ¶ '.join(corpus)
    lost, gone_files = {}, []
    for f in before:
        if f not in now:
            gone_files.append(f)
        old = git(repo, 'show', f'{base}:{f}')
        miss = [l.strip() for l in old.splitlines() if len(norm(l)) >= 12 and norm(l) not in blob]
        if miss:
            lost[f] = miss
    checked = len(before)
    if not lost:
        print(f"✔ preserved: every meaningful line of {checked} pre-existing doc/workflow file(s) still exists"
              + (f" ({len(gone_files)} file(s) moved: {', '.join(gone_files)})" if gone_files else ''))
        return
    print(f'✖ content from {len(lost)} of {checked} pre-existing file(s) is missing:')
    for f, miss in lost.items():
        print(f'  {f}{" (file removed)" if f in gone_files else ""}: {len(miss)} line(s)')
        for l in miss[:8]:
            print(f'    - {l[:110]}')
    sys.exit(1)


if __name__ == '__main__':
    main()
