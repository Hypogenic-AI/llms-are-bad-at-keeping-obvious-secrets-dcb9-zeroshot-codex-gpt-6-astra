"""Render supplementary tables from saved analyses."""
import json
from pathlib import Path
import numpy as np,pandas as pd
P=Path('paper_draft');B=json.loads(Path('results/analysis/behavior.json').read_text());M=json.loads(Path('results/mechanism/analysis.json').read_text())
assert all(r['n']==24 for r in M['summary'] if r['reader']=='sonnet'), 'Local evaluation is incomplete'
def table(path,heads,rows,fmt=None):
    if fmt is None:fmt='l'+'r'*(len(heads)-1)
    lines=['\\begin{tabular}{'+fmt+'}',r'\toprule',' & '.join(heads)+r' \\',r'\midrule']
    lines+=[' & '.join(map(str,row))+r' \\' for row in rows];lines += [r'\bottomrule',r'\end{tabular}'];(P/path).write_text('\n'.join(lines))
rows=[]
for d in ['word','plot']:
 for c in ['plain','filler','outline','decoy' if d=='word' else 'no_secret']:
    s=next(r for r in B['summary'] if r['domain']==d and r['condition']==c and r['reader']=='sonnet');m=next(r for r in B['summary'] if r['domain']==d and r['condition']==c and r['reader']=='mini')
    rows.append([d.title(),c.replace('_',' ').title(),f"{s['order_agreement']*100:.1f}",f"{s['choose_A']*100:.1f}",f"{m['order_agreement']*100:.1f}",str(m['invalid']),f"{100*m['missing_bounds'][0]:.1f}--{100*m['missing_bounds'][1]:.1f}"])
table('order_table.tex',['Domain','Condition','Sonnet agreement','Sonnet A','Mini agreement','Mini missing','Mini bounds'],rows,'llrrrrr')
rows=[];q=pd.read_csv('results/analysis/quality.csv')
for d in ['word','plot']:
 for c in ['plain','filler','outline','decoy' if d=='word' else 'no_secret']:
    r=next(r for r in B['diagnostics'] if r['domain']==d and r['condition']==c);qr=q[(q.domain==d)&(q.condition==c)].iloc[0]
    rows.append([d.title(),c.replace('_',' ').title(),f"{r['mean_words']:.1f}",f"{r['mean_prompt_tokens']:.1f}",f"{qr.coherence:.2f}",f"{qr.fluency:.2f}",f"{qr.nonrepetition:.2f}"])
table('quality_table.tex',['Domain','Condition','Words','Prompt tokens','Coherence','Fluency','Nonrep.'],rows,'llrrrrr')
rows=[]
for c in ['base','target','random','other']:
    s=next(r for r in M['summary'] if r['condition']==c and r['reader']=='sonnet');m=next(r for r in M['summary'] if r['condition']==c and r['reader']=='mini');d=next(r for r in M['diagnostics'] if r['condition']==c);q=next(r for r in M['quality'] if r['condition']==c)
    rows.append([c.title(),str(s['n']),f"{s['mean']*100:.1f} [{s['ci'][0]*100:.1f}, {s['ci'][1]*100:.1f}]",f"{m['mean']*100:.1f} ({m['n']})",str(d['literal']),f"{q['coherence']:.2f}",f"{q['nonrepetition']:.2f}"])
table('mechanism_table.tex',['Arm','Pairs',r'Sonnet [95\% CI]','Mini (pairs)','Literal /48','Coherence','Nonrep.'],rows,'llrrrrr')
rows=[]
for r in M['contrasts']:
    if r['reader']=='sonnet':rows.append([r['contrast'],str(r['n']),f"{r['delta']*100:.1f}",f"[{r['ci'][0]*100:.1f}, {r['ci'][1]*100:.1f}]",f"{r['p']:.4f}"])
table('mechanism_contrasts.tex',['Contrast','Pairs','Difference',r'95\% interval','$p$'],rows,'lrrrr')
rows=[]
for mode in ['raw','neutral_paired','secret_centered']:
 for l in [12,24,36,48]:
    rr=[next(r for r in M['readouts'] if r['mode']==mode and r['layer']==l and r['position']==p) for p in [64,192,384,576]]
    rows.append([mode.replace('_',' '),str(l)]+[f"{r['accuracy']*100:.1f}" for r in rr])
table('readout_table.tex',['Centering','Layer','64','192','384','576'],rows,'llrrrr')
S=json.loads(Path('results/mechanism/supervised_probe.json').read_text());E=json.loads(Path('results/mechanism/supervised_equal_length.json').read_text())
rows=[]
for label,data in [('Four-way',S),('Three-way equal length',E)]:
 for l in [12,24,36,48]:
    rr=[next(r for r in data if r['layer']==l and r['position']==p and r.get('intervention','none')=='none') for p in [64,192,384,576]]
    rows.append([label,str(l)]+[f"{r['accuracy']*100:.1f}" for r in rr])
table('supervised_table.tex',['Probe','Layer','64','192','384','576'],rows,'llrrrr')
# Machine-readable snapshot for main-text number cross-checking.
(P/'numbers.json').write_text(json.dumps({'behavior':B,'mechanism':M,'supervised':S,'supervised_equal_length':E},indent=2))
print('Generated report tables')
