"""Validate artifact completeness and label/order invariants without network calls."""
import json,hashlib,os
from pathlib import Path
from collections import Counter
rows=json.loads(Path('results/design.json').read_text())
assert len(rows)==1440 and len({r['id'] for r in rows})==1440
assert len({r['seed'] for r in rows})==1440
assert Counter(r['domain'] for r in rows)=={'word':960,'plot':480}
for r in rows:
    f=Path('results/stories')/(r['id']+'.json');assert f.exists(),str(f)
    d=json.loads(f.read_text());assert d['prompt']==r['prompt']
    assert d['request']['messages'][0]['content']==r['prompt']
    assert d['text']==d['response']['choices'][0]['message']['content']
    assert d['text'].strip()
for root,n in [(Path('results/judgments'),2880),(Path('results/mechanism/judgments'),384)]:
    fs=list(root.glob('*.json'));assert len(fs)==n,(str(root),len(fs))
    for f in fs:
        r=json.loads(f.read_text())
        if r['choice'] is None:
            assert r['correct'] is None and r['response']['choices'][0]['finish_reason']=='content_filter',str(f)
        else:
            assert r['choice'] in ['A','B'],str(f)
            assert r['correct']==int(r['choice']==('A' if r['order']==0 else 'B'))
assert len(list(Path('results/mechanism/stories').glob('*.json')))==192
assert len(list(Path('results/quality').glob('*.json')))==240
assert len(list(Path('results/mechanism/quality').glob('*.json')))==192
for folder in ['results/quality','results/mechanism/quality']:
    for f in Path(folder).glob('*.json'):
        q=json.loads(f.read_text())['scores'];assert q and all(1<=q[k]<=5 for k in ['coherence','fluency','nonrepetition']),str(f)
assert Path('paper_draft/main.pdf').exists() and Path('paper_draft/main.pdf').stat().st_size>10000
assert Path('README.md').exists()
manifest={}
for root in ['src','results','paper_draft']:
    for f in sorted(Path(root).rglob('*')):
        if f.is_file() and '__pycache__' not in str(f) and f.name!='audit.json' and f.suffix not in ['.aux','.log','.out','.blg']:
            blob=f.read_bytes()
            for key in ['OPENROUTER_KEY','OPENAI_API_KEY','HF_TOKEN']:
                secret=os.environ.get(key)
                assert not secret or secret.encode() not in blob, 'Credential detected in artifact'
            manifest[str(f)]=hashlib.sha256(blob).hexdigest()
Path('results/audit.json').write_text(json.dumps({'status':'passed','files_sha256':manifest},indent=2))
print('Audit passed:',len(manifest),'files')
