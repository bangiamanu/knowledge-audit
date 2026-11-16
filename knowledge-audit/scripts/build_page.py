# Usage: python3 build_page.py <dump_dir> <out.html> "<date>"
# dump_dir holds:
#   memory/          verbatim copies of memory files, same paths as in memory (e.g. memory/profile.md, memory/projects/<id>/index.md)
#   flags/*.json     {memory path or skill name: [flag, ...]}
#   skills.json      {skill name: absolute path to its SKILL.md}  (the user's own skills only)
#   projects.json    {project id: project name}  (projects to audit only)
#   rules.txt        the rules the audit used, one per line
#   drive/inventory.json  optional, only when a Drive (or other file store) check was run
#   redact.json      optional, [exact secret strings] blanked on the page
# The page template (tpl.html) sits in ../assets/ next to this script's folder.
import json, os, re, glob, sys
from collections import Counter

D, OUT, DATE = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, '..', 'assets', 'tpl.html')

def load(p, default):
    return json.load(open(p)) if os.path.exists(p) else default

PN = load(D + '/projects.json', {})
SECRETS = load(D + '/redact.json', [])
SKP = load(D + '/skills.json', {})
flags = {}
for f in glob.glob(D + '/flags/*.json'):
    for k, v in json.load(open(f)).items():
        flags.setdefault(k, []).extend(v)

def red(t):
    for s in SECRETS:
        t = t.replace(s, '[removed from this page]')
    return t
def rd(p): return red(open(p, encoding='utf-8', errors='replace').read())
def desc(t):
    m = re.search(r'^description:\s*(.+)$', t, re.M)
    return m.group(1).strip().strip('"') if m else ''
def fl(k): return [{**x, 'line': red(x.get('line', ''))} for x in flags.get(k, [])]

N = [0]
def nid():
    N[0] += 1
    return f'n{N[0]}'
def item(title, kind, body, flg, d='', link=None): return {'id': nid(), 't': title, 'k': kind, 'b': body, 'f': flg, 'd': d, 'l': link}
def group(title, kids, note=''): return {'id': nid(), 't': title, 'g': kids, 'n': note}

mf = sorted(p[len(D + '/memory'):] for p in glob.glob(D + '/memory/**/*.md', recursive=True))
def mitem(p, title):
    b = rd(D + '/memory' + p)
    return item(title, 'memory file', b, fl(p), desc(b))

# Global memory
G = []
for k, lab in [('root', 'Profile and preferences'), ('areas', 'Areas'), ('topics', 'Topics')]:
    ps = [p for p in mf if not p.startswith('/projects') and ((p.count('/') == 1) if k == 'root' else p.startswith(f'/{k}/'))]
    G.append(group(lab, [mitem(p, p.split('/')[-1]) for p in ps]))

# Projects
inv = load(D + '/drive/inventory.json', {'projects': [], 'not_found_notes': {}})
dv = {p['name']: p for p in inv.get('projects', [])}
nn = inv.get('not_found_notes', {}) or {}
drive_checked = os.path.exists(D + '/drive/inventory.json')
P = []
for pid, name in sorted(PN.items(), key=lambda x: x[1]):
    ps = [p for p in mf if p.startswith(f'/projects/{pid}/') and '/people/' not in p]
    mem = group('Memory', [mitem(p, p.split(pid + '/')[1]) for p in ps])
    kids_out = [mem]
    if drive_checked:
        pr = dv.get(name)
        if pr:
            kids = [item(f['title'], 'Drive doc', rd(f['saved_path']) if f.get('saved_path') and os.path.exists(f['saved_path']) else None, f.get('flags', []), f.get('kind', ''), f.get('url')) for f in pr['files'] if f.get('kind') == 'context doc']
            oth = [f for f in pr['files'] if f.get('kind') != 'context doc']
            if oth:
                kids.append({**item('Other files', 'file list', None, [x for f in oth for x in f.get('flags', [])], ', '.join(f'{v} {k}' for k, v in Counter(f.get('kind') for f in oth).items())), 'rows': [[f['title'], f.get('kind', ''), (f.get('modified') or '')[:10], f.get('url') or ''] for f in oth]})
            drv = group('Drive folder', kids, pr.get('note', ''))
            drv['l'] = pr.get('folder_url')
        else:
            drv = group('Drive folder', [], 'No Drive folder found. ' + nn.get(name, ''))
        kids_out.append(drv)
    else:
        kids_out.append(group('Drive folder', [], 'Not checked in this run.'))
    g = group(name, kids_out)
    w = name.lower().replace(' ', '-')
    g['sk'] = sorted(n for n in SKP if n.startswith(w + '-'))
    g['skf'] = sum(len(flags.get(n, [])) for n in g['sk'])
    g['sky'] = sum(1 for n in g['sk'] for x in flags.get(n, []) if x.get('label', '').lower().startswith(('duplicate', 'no purpose')))
    g['skr'] = g['skf'] - g['sky']
    P.append(g)

# People
PE = [group('Global (every chat)', [mitem(p, p.split('/')[-1]) for p in mf if p.startswith('/people/')], 'Loaded in every chat.')]
for pid, name in sorted(PN.items(), key=lambda x: x[1]):
    pp = [p for p in mf if p.startswith(f'/projects/{pid}/people/')]
    if pp:
        PE.append(group(name + ' project', [mitem(p, p.split('/')[-1]) for p in pp], 'Only visible inside the ' + name + ' project.'))

# Skills, grouped by name prefix
S = {}
for n, p in SKP.items():
    if not os.path.exists(p):
        continue
    b = rd(p)
    for x in sorted(glob.glob(os.path.dirname(p) + '/**/*', recursive=True)):
        if os.path.isfile(x) and x.endswith(('.md', '.txt')) and not x.endswith(('SKILL.md', 'LICENSE.txt')):
            b += f'\n\n===== {os.path.relpath(x, os.path.dirname(p))} =====\n' + rd(x)
    S.setdefault(n.split('-')[0], []).append(item(n, 'skill', b, fl(n), desc(b)))
SK, other = [], []
for fam, its in sorted(S.items()):
    (SK.append(group(fam + '-*', its)) if len(its) > 1 else other.extend(its))
if other:
    SK.append(group('other', other))

ROOT = [
    group('Global memory', G, 'Loaded in every chat. Facts about you and how you want Claude to work.'),
    group('People', PE, 'One file per person under /people/: global ones load in every chat, project ones only inside that project.'),
    group('Projects', P, 'Each audited project: its own memory, plus its linked Drive folder if one was checked.'),
    group('Skills', SK, 'What a recurring task needs to run right.'),
]
RULES = [l.strip()[2:] if l.strip().startswith('- ') else l.strip() for l in open(D + '/rules.txt') if l.strip()]
data = {'date': DATE, 'rules': RULES, 'secrets': len(SECRETS), 'root': ROOT}
js = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
body = open(TPL).read().replace('%%DATA%%', js)
head, rest = body.split('</style>', 1)
out = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1">'
       + head + '</style></head><body>' + rest + '</body></html>')
open(OUT, 'w').write(out)
print(N[0], 'nodes', len(out), 'bytes')
