#!/usr/bin/env python3
"""existing.py — read-only survey of a repo's EXISTING agent docs, rules and automation,
so onboarding adapts to them instead of overwriting them. Part of repo-onboard.

    python3 -I existing.py <repo-dir> [--json out.json]

Finds: entry files (and which one is canonical when one redirects to the other),
floor maps per folder (and their file name: AGENTS.md / CONTEXT.md / CLAUDE.md),
rule / secrets / runbook / skill docs, the knowledge shelf folder, workflows and what
they deploy to, the site type. Scores ICM conformance, maps every onboarding rule topic
to where the repo already covers it, lists likely duplicated facts, and proposes the
`paths` + `modules` for answers.json. Never writes inside the repo.
"""
import collections, glob, json, os, re, sys

SKIP = {'.git', 'node_modules', '.next', 'dist', 'build', '__pycache__', 'vendor'}
AGENT_NAMES = ('CLAUDE.md', 'AGENTS.md', 'CONTEXT.md')
EXTRA_DOCS = re.compile(r'(^|/)(SECRETS\.md|SECURITY[-\w]*\.md|[-\w]*RUNBOOK[-\w]*\.md|CONTRIBUTING\.md|MAP\.md|STATE\.md|REPO-INDEX\.md|'
                        r'claude-repo-brief\.md|copilot-instructions\.md|\.cursorrules|COMMIT-MAP\.md|HANDOVER\.md|LEDGER\.md)$', re.I)
# Onboarding rule topics → words that show a repo already covers them.
TOPICS = {
    'data-safety':   r'migration|schema|database|\bDB\b|localStorage|seed|saved data|storage key',
    'one-source':    r'source of truth|single source|one source|single definition|tokens live once|no second tree|parallel',
    'content':       r'spelling|brand|tone|voice|copy\b|emoji|font',
    'branches':      r'\bdevelop\b|\bmain\b|promote|pull request|\bPRs?\b|branch|Conventional Commits',
    'guarded':       r'untouchable|guard|🔒|never touch|security-critical|only when the task',
    'supply-chain':  r'SHA|pinned|dependabot|npm ci|ignore-scripts|lockfile|supply.chain|tripwire|npx',
    'secrets':       r'secret|\.env|credential|token|rotate',
    'deploys':       r'deploy|staging|rollback|pm2|last good build|nginx',
    'collaboration': r'plain language|one step|placeholder|impact|ask\b|pickup|handoff|lost\?',
}


def read(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


def files(repo):
    for root, dirs, fs in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP and not (root == repo and d == '.claude')]
        for f in fs:
            yield os.path.relpath(os.path.join(root, f), repo).replace(os.sep, '/')


def is_redirect(text):
    body = [l for l in text.strip().splitlines() if l.strip() and not l.startswith('<!--')]
    return len(body) <= 3 and bool(re.search(r'^@\S+\.md|→|redirect|see \S+\.md|pointer', text, re.I | re.M))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    repo = os.path.abspath(sys.argv[1])
    out_json = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    rels = sorted(files(repo))
    docs = {}
    for r in rels:
        base = os.path.basename(r)
        if base in AGENT_NAMES or EXTRA_DOCS.search(r) or (r.startswith('docs/prompts/') and r.endswith('.md')):
            t = read(os.path.join(repo, r))
            docs[r] = {'lines': t.count('\n') + 1, 'text': t}

    # ---- entry + canonical ---------------------------------------------------
    entry = {}
    for n in ('CLAUDE.md', 'AGENTS.md'):
        if n in docs:
            entry[n] = 'redirect' if is_redirect(docs[n]['text']) else 'content'
    canonical = next((n for n in ('AGENTS.md', 'CLAUDE.md') if entry.get(n) == 'content'), None)
    if entry.get('CLAUDE.md') == 'content' and entry.get('AGENTS.md') == 'content':
        canonical = 'CLAUDE.md'   # both hand-kept — flag as drift risk below

    # ---- floor maps ----------------------------------------------------------
    floors = collections.Counter()
    floor_files = []
    for r, d in docs.items():
        if '/' in r and os.path.basename(r) in AGENT_NAMES and not is_redirect(d['text']) and not r.startswith(('work/',)):
            floors[os.path.basename(r)] += 1
            floor_files.append(r)
    floor_name = floors.most_common(1)[0][0] if floors else 'CONTEXT.md'

    # ---- roles -----------------------------------------------------------------
    roles = {}
    for r, d in docs.items():
        t, b = d['text'], os.path.basename(r)
        if b in AGENT_NAMES and is_redirect(t):
            roles[r] = 'redirect'
        elif r in ('CLAUDE.md', 'AGENTS.md'):
            roles[r] = 'entry'
        elif b in AGENT_NAMES:
            roles[r] = 'floor-map'
        elif re.search(r'secret', b, re.I):
            roles[r] = 'secrets'
        elif re.search(r'runbook|security', b, re.I):
            roles[r] = 'runbook'
        elif r.startswith('docs/prompts/'):
            roles[r] = 'skill/playbook'
        elif re.search(r'brief|copilot|cursorrules', b, re.I):
            roles[r] = 'rules-for-a-tool'
        else:
            roles[r] = 'reference'
    shelf = next((d for d in ('_shared', 'docs', 'doc', 'documentation') if any(x.startswith(d + '/') for x in rels)), None)

    # ---- ICM conformance -------------------------------------------------------
    icm = []
    if canonical:
        t = docs[canonical]['text']
        n = docs[canonical]['lines']
        icm.append(('entry file ≤ 60 lines (routes, holds no payload)', n <= 60, f'{canonical} is {n} lines'))
        icm.append(('entry file has a routing table', bool(re.search(r'^\|.*\|.*\|', t, re.M)), ''))
    else:
        icm.append(('has an entry file', False, 'no CLAUDE.md / AGENTS.md with content'))
    if entry.get('CLAUDE.md') == entry.get('AGENTS.md') == 'content':
        icm.append(('one entry file (the other a pointer)', False, 'CLAUDE.md and AGENTS.md both hold content — they will drift'))
    back = [f for f in floor_files if not re.search(r'return to|back to|not a .* task', docs[f]['text'], re.I)]
    icm.append(('every floor map routes back to the entry', not back, ', '.join(back[:6])))
    payload = [f for f in floor_files if docs[f]['lines'] > 80]
    icm.append(('floor maps stay small (≤ 80 lines)', not payload, ', '.join(payload)))
    contract = re.compile(r'input|reads|output|writes|human check|read first', re.I)
    no_contract = [f for f in floor_files if not contract.search(docs[f]['text'])]
    icm.append(('floor maps say what to read / what they produce', not no_contract, ', '.join(no_contract[:6])))

    # ---- topics → where already covered ------------------------------------------
    cover = {}
    for topic, rx in TOPICS.items():
        hits = []
        for r, d in docs.items():
            if roles[r] in ('redirect',):
                continue
            for i, line in enumerate(d['text'].splitlines(), 1):
                if re.search(rx, line, re.I) and re.search(r'never|always|must|keep|only|law|rule|don.t|do not|stays', line, re.I):
                    hits.append(f'{r}:{i}')
        cover[topic] = hits

    # ---- likely duplicated facts (same rule line in 2+ files) -------------------
    seen = collections.defaultdict(set)
    for r, d in docs.items():
        for line in d['text'].splitlines():
            s = re.sub(r'[`*_>#|-]', '', line).strip().lower()
            if len(s) > 50 and re.search(r'never|always|must', s):
                seen[s].add(r)
    dupes = [{'text': k[:110], 'files': sorted(v)} for k, v in seen.items() if len(v) > 1][:12]

    # ---- automation + site type ---------------------------------------------------
    wfs = {}
    for r in rels:
        if r.startswith('.github/workflows/') and r.endswith(('.yml', '.yaml')):
            t = read(os.path.join(repo, r))
            kind = 'deploy:ssh/vps' if re.search(r'ssh|rsync|VPS', t) else 'deploy:pages' if 'deploy-pages' in t else \
                   'deploy:ftp' if 'lftp' in t or 'ftp' in r else 'ci'
            wfs[r] = kind
    pkg = [r for r in rels if r.endswith('package.json') and '/node_modules/' not in r]
    framework = ''
    for p in pkg:
        t = read(os.path.join(repo, p))
        m = re.search(r'"(next|vite|astro|@sveltejs/kit|nuxt|gatsby|react-scripts)"', t)
        if m:
            framework = f'{m.group(1)} ({p})'; break
    static = 'index.html' in rels and not framework
    has_dependabot = '.github/dependabot.yml' in rels or '.github/dependabot.yaml' in rels
    own_deploy = any(k.startswith('deploy:') for k in wfs.values())

    kit_names = {'deploy-staging.yml', 'promote.yml', 'deploy.yml', 'pages.yml', 'ftp.yml'}
    collisions = sorted(r for r in wfs if os.path.basename(r) in kit_names)

    proposal = {
        'paths': {
            'entry_file': canonical or 'CLAUDE.md',
            'pointer_file': ('CLAUDE.md' if (canonical or 'CLAUDE.md') == 'AGENTS.md' else 'AGENTS.md'),
            'floor_file': floor_name,
            'factory_dir': shelf or '_shared',
            'secrets_file': next((r for r in docs if roles[r] == 'secrets'), f'{shelf or "_shared"}/secrets.md'),
            'archive_dir': '_archive',
            'work_dir': 'work',
            'release_doc': next((r for r in ('DEPLOYMENT.md', 'deploy/README.md', 'docs/DEPLOYMENT.md', 'RELEASING.md') if r in rels), '') if own_deploy else '',
        },
        'modules': {
            'icm': True, 'rules': True, 'supply_chain': True, 'mirrors': True,
            'deploy': bool(static and not own_deploy),
            'checks_workflow': bool(own_deploy or not static),
        },
    }
    facts = {'docs': {r: {'lines': d['lines'], 'role': roles[r]} for r, d in docs.items()}, 'entry': entry,
             'canonical_entry': canonical, 'floor_file': floor_name, 'floor_maps': floor_files, 'knowledge_shelf': shelf,
             'icm_checks': [{'check': c, 'ok': ok, 'detail': det} for c, ok, det in icm], 'topic_coverage': cover,
             'duplicated_facts': dupes, 'workflows': wfs, 'workflow_name_collisions': collisions,
             'framework': framework, 'static_site': static, 'has_dependabot': has_dependabot, 'proposal': proposal}

    w = sys.stdout.write
    w(f"Existing setup in {repo}\n")
    w(f"  entry: {entry or '-'} → canonical: {canonical or 'none'}\n")
    w(f"  floor maps: {len(floor_files)} × {floor_name} · knowledge shelf: {shelf or '-'}\n")
    for r in sorted(docs):
        w(f"    {roles[r]:<16} {r} ({docs[r]['lines']} lines)\n")
    w("  ICM conformance:\n")
    for c, ok, det in icm:
        w(f"    {'✔' if ok else '✖'} {c}{' — ' + det if det and not ok else ''}\n")
    w("  onboarding topics already covered (rule-like lines):\n")
    for t, hits in cover.items():
        w(f"    {t:<14} {'MISSING' if not hits else str(len(hits)) + ' — ' + ', '.join(hits[:4]) + (' …' if len(hits) > 4 else '')}\n")
    if dupes:
        w(f"  facts stated in more than one file: {len(dupes)} (e.g. \"{dupes[0]['text'][:70]}…\" in {', '.join(dupes[0]['files'])})\n")
    w(f"  workflows: {wfs or '-'}\n")
    if collisions:
        w(f"  ⚠ name collisions with the kit's workflows: {', '.join(collisions)} — the kit will NOT replace them\n")
    w(f"  site: {'static' if static else framework or 'unknown'} · Dependabot: {has_dependabot}\n")
    w(f"  proposed paths: {json.dumps(proposal['paths'])}\n  proposed modules: {json.dumps(proposal['modules'])}\n")
    if out_json:
        json.dump(facts, open(out_json, 'w'), indent=2)
        w(f"facts → {out_json}\n")


if __name__ == '__main__':
    main()
