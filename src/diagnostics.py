import json,re
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np,pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from analyze import ci,signflip,load_judgments
rows=[json.loads(f.read_text()) for f in Path('results/stories').glob('*.json')];groups=defaultdict(list)
for r in rows:groups[(r['domain'],r['condition'],r['block'])].append(r)
o=[]
for (d,c,b),rs in groups.items():
    sets=[set(re.findall(r'\b[a-z]+\b',r['text'].lower()))-ENGLISH_STOP_WORDS for r in rs]
    o.append(dict(domain=d,condition=c,block=b,jaccard=len(sets[0]&sets[1])/len(sets[0]|sets[1])))
pd.DataFrame(o).to_csv('results/analysis/pair_overlap.csv',index=False)
s=[]
for (d,c),g in pd.DataFrame(o).groupby(['domain','condition']):s.append(dict(domain=d,condition=c,mean=g.jaccard.mean(),ci=ci(g.jaccard)))
_,av=load_judgments('results/judgments');null=[]
for reader in ['sonnet','mini']:
    a=av[(av.domain=='plot')&(av.condition=='no_secret')&(av.reader==reader)].score
    null.append(dict(reader=reader,n=len(a),mean=a.mean(),distribution={str(k):int(v) for k,v in a.value_counts().items()},p_signflip=signflip(a-.5)))
# Totals use provider-returned usage, not price-based estimates.
cost=defaultdict(float);counts=Counter()
for path in [Path('results/stories'),Path('results/judgments'),Path('results/quality'),Path('results/mechanism/judgments'),Path('results/mechanism/quality')]:
    for f in path.glob('*.json'):
        r=json.loads(f.read_text());resp=r.get('response',{});model=r.get('request',{}).get('model','unknown');counts[model]+=1
        cost[model]+=resp.get('usage',{}).get('cost',0) or 0
Path('results/analysis/extra.json').write_text(json.dumps(dict(overlap=s,negative_control=null,api_reported_cost=cost,api_call_counts=counts),indent=2))
print(json.dumps(dict(overlap=s,negative_control=null,api_reported_cost=cost,api_call_counts=counts),indent=2))
