# Mechanical pre-check. Usage: python3 mech.py <file-or-dir> [...]
# Run it from the dump folder copy (it reads paths.txt, projects.json and skills.json beside it).
# Prints candidate lines by test. Every hit must be judged (flag it or dismiss it); the tests are the same on every run.
import re,sys,os,glob,json
D=os.path.dirname(os.path.abspath(__file__))
PATHS=[l.strip() for l in open(D+'/paths.txt') if l.strip()]
STEMS={os.path.basename(p)[:-3] for p in PATHS}
SKILLS=set(json.load(open(D+'/skills.json'))) if os.path.exists(D+'/skills.json') else set()
MON=r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*'
DATED=re.compile(r'20\d\d|\b'+MON+r'\.? \d{1,2}\b|\bAs of\b')
T_SKILL=[('money',re.compile(r'[$£€]\s?\d[\d,.]*')),
 ('row/column/cell',re.compile(r'\b(row|rows|column|col)\s+[A-Z]{1,2}\b|\b(row|rows)\s+\d+\b|\b[A-Z]{1,2}\d{1,3}:[A-Z]{1,2}\d{0,3}\b|![A-Z]{1,2}\d{1,3}\b')),
 ('real date in a link or template',re.compile(r'(https?://|q=|%20)\S*20\d\d-\d\d-\d\d')),
 ('size or count from a run',re.compile(r'\b\d[\d,.]*\s?(MB|KB|GB)\b|\b\d[\d,]+\s+(photos|images|emails|rows|columns|files|pages|groups|slides|items)\b|\b\d+-(page|slide)\b',re.I)),
 ('balance/credits on a date',re.compile(r'(balance|credits?)[^.\n]{0,60}(zero|none|\d)',re.I)),
 ('long digit run (account-like)',re.compile(r'(?<![\w/=-])\d{9,12}(?![\w-])'))]
T_MEM=[('status wording',re.compile(r"\b(planning|plans to|working toward|waiting|weighing|considering|looking at|thinking about|still (wanted|deciding|to)|next step|follow-up|in progress|pending|may (visit|be|take)|going with|brought|will send|open intros?)\b",re.I)),
 ('how-to wording',re.compile(r'\b(Method:|Procedure:|STANDING RULE|step \d|first,? .* then|append after|always (run|check|add)|whenever .* (add|update|put))',re.I)),
 ('money',re.compile(r'[$£€]\s?\d[\d,.]*')),
 ('long digit run (account-like)',re.compile(r'(?<![\w/=-])\d{9,12}(?![\w-])'))]
LINK=re.compile(r'\[\[([^\]]+)\]\]'); MP=re.compile(r'(?<![\w.])/(?:topics|areas|people)/[\w-]+\.md')
PRE=['global']+[n.lower().replace(' ','-') for n in json.load(open(D+'/projects.json')).values()]
SKREF=re.compile(r'\b((?:'+'|'.join(PRE)+r')-[a-z][a-z-]+[a-z])\b')
def files(a):
    if os.path.isdir(a): return sorted(p for p in glob.glob(a+'/**/*',recursive=True) if p.endswith(('.md','.txt')) and not p.endswith('LICENSE.txt'))
    return [a]
for a in sys.argv[1:]:
    for f in files(a):
        is_skill='/skills/' in f; is_global=('/memory/' in f and '/projects/' not in f)
        out=[]
        for i,l in enumerate(open(f,encoding='utf-8',errors='replace').read().split('\n'),1):
            if l.startswith(('description:','name:','aliases:','sources:','---')) and not is_skill and not l.startswith('description:'): continue
            for name,rx in (T_SKILL if is_skill else T_MEM):
                if rx.search(l):
                    if name=='status wording' and not is_global and DATED.search(l): continue  # dated project status is allowed
                    out.append((i,name,l.strip()[:170]))
            for m in LINK.findall(l):
                if m not in STEMS: out.append((i,'BROKEN [[link]]: '+m,l.strip()[:120]))
            for m in MP.findall(l):
                if m not in PATHS: out.append((i,'BROKEN memory path: '+m,l.strip()[:120]))
            if not l.startswith('name:'):
                for m in SKREF.findall(l):
                    if m not in SKILLS and not m.endswith('-') and len(m.split('-'))>=3: out.append((i,'skill name not found: '+m,l.strip()[:120]))
        if out:
            print('=====',f)
            for i,n,l in out: print(f'  L{i} [{n}] {l}')
