import json,re,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
RNG=np.random.default_rng(1492);OUT=Path('results/analysis');OUT.mkdir(exist_ok=True);FIG=Path('paper_draft/figures');FIG.mkdir(exist_ok=True)
def ci(x,n=20000):
    x=np.asarray(x,dtype=float);b=x[RNG.integers(len(x),size=(n,len(x)))].mean(1)
    return np.quantile(b,[.025,.975]).tolist()
def signflip(x):
    x=np.asarray(x);null=(RNG.choice([-1,1],size=(100000,len(x)))*x).mean(1)
    return float((1+(np.abs(null)>=abs(x.mean())-1e-12).sum())/100001)
def load_judgments(folder):
    rows=[json.loads(f.read_text()) for f in Path(folder).glob('*.json')]
    df=pd.DataFrame([{k:r.get(k) for k in ['block','domain','condition','reader','order','correct','choice','item','rep']} for r in rows])
    if len(df)==0:return df,df
    good=df.dropna(subset=['correct']).copy()
    # Only complete both-order judgments enter pair averages.
    av=good.groupby(['block','domain','condition','reader','item','rep']).agg(score=('correct','mean'),n=('correct','size')).reset_index()
    av=av[av.n==2]
    return df,av

def main():
    df,av=load_judgments('results/judgments');assert len(df)==2880, 'Wait for all reader requests';av.to_csv(OUT/'pair_scores.csv',index=False)
    sums=[]
    for (d,c,r),g in av.groupby(['domain','condition','reader']):
        raw=df[(df.domain==d)&(df.condition==c)&(df.reader==r)]
        pivot=raw.pivot(index='block',columns='order',values='correct').dropna()
        sums.append(dict(domain=d,condition=c,reader=r,n=len(g),mean=g.score.mean(),ci=ci(g.score),cluster_ci=ci(g.groupby('item').score.mean()),order_agreement=float((pivot[0]==pivot[1]).mean()),choose_A=float((raw.choice=='A').mean()),invalid=int(raw.correct.isna().sum()),missing_bounds=[float(raw.correct.fillna(0).mean()),float(raw.correct.fillna(1).mean())]))
    contrasts=[]
    for d in ['word','plot']:
        for reader in ['sonnet','mini']:
            sub=av[(av.domain==d)&(av.reader==reader)]
            p=sub.pivot(index=['block','item'],columns='condition',values='score').dropna()
            for base in ['plain','filler']:
                delta=p['outline']-p[base]
                contrasts.append(dict(domain=d,reader=reader,contrast='outline-'+base,n=len(delta),delta=delta.mean(),ci=ci(delta),cluster_ci=ci(delta.groupby('item').mean()),p=signflip(delta)))
    primary=[r for r in contrasts if r['reader']=='sonnet'];order=sorted(primary,key=lambda r:r['p']);prev=0
    for i,r in enumerate(order):r['p_holm']=max(prev,min(1,r['p']*(len(order)-i)));prev=r['p_holm']
    diag=[];details=[]
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained('models/gemma-3-12b-it') if Path('models/gemma-3-12b-it/tokenizer.json').exists() else None
    cached=pd.read_csv(OUT/'story_diagnostics.csv').set_index('id') if tok is None else None
    for f in Path('results/stories').glob('*.json'):
        r=json.loads(f.read_text());words=re.findall(r"\b[\w']+\b",r['text'].lower());grams=list(zip(words,words[1:],words[2:],words[3:]));
        details.append(dict(id=r['id'],domain=r['domain'],condition=r['condition'],words=len(r['text'].split()),tokens=len(tok.encode(r['text'],add_special_tokens=False)) if tok is not None else int(cached.loc[r['id'],'tokens']),prompt_tokens=len(tok.encode(r['prompt'],add_special_tokens=False)) if tok is not None else int(cached.loc[r['id'],'prompt_tokens']),literal=bool(re.search(r'\b'+re.escape(r['secret'])+r'\b',r['text'],re.I)) if r['domain']=='word' else False,truncated=r['response']['choices'][0]['finish_reason']=='length',distinct4=len(set(grams))/max(1,len(grams))))
    st=pd.DataFrame(details);st.to_csv(OUT/'story_diagnostics.csv',index=False)
    for (d,c),g in st.groupby(['domain','condition']):diag.append(dict(domain=d,condition=c,n=len(g),mean_words=g.words.mean(),mean_tokens=g.tokens.mean(),mean_prompt_tokens=g.prompt_tokens.mean(),literal=int(g.literal.sum()),truncated=int(g.truncated.sum()),distinct4=g.distinct4.mean()))
    quality=[]
    for f in Path('results/quality').glob('*.json'):
        r=json.loads(f.read_text())
        if r['scores']:quality.append(dict(domain=r['domain'],condition=r['condition'],**r['scores']))
    q=pd.DataFrame(quality)
    if len(q):q.groupby(['domain','condition']).mean().to_csv(OUT/'quality.csv')
    # Sensitivity excluding any pair with literal mention or truncation.
    bad=set(st[st.literal|st.truncated].id.str.replace(r'_[01]$','',regex=True))
    clean=av[~(av.block+'_'+av.condition).isin(bad)]
    sens=clean.groupby(['domain','condition','reader']).score.agg(['mean','count']).reset_index().to_dict('records')
    result=dict(summary=sums,contrasts=contrasts,diagnostics=diag,clean_sensitivity=sens)
    (OUT/'behavior.json').write_text(json.dumps(result,indent=2))
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.4),sharey=True)
    for ax,domain in zip(axes,['word','plot']):
        cs=['plain','filler','outline','decoy'] if domain=='word' else ['plain','filler','outline','no_secret']
        for shift,reader,color,label in [(-.09,'sonnet','#225ea8','Sonnet 4.6'),(.09,'mini','#d95f0e','GPT-4.1 mini')]:
            vals=[next(r for r in sums if r['domain']==domain and r['condition']==c and r['reader']==reader) for c in cs]
            means=np.array([r['mean'] for r in vals]);bounds=np.array([r['ci'] for r in vals]).T
            ax.errorbar(np.arange(4)+shift,means*100,yerr=np.stack([means-bounds[0],bounds[1]-means])*100,fmt='o',capsize=3,label=label,color=color)
        ax.axhline(50,color='gray',ls='--',lw=1);ax.set_xticks(range(4),[c.replace('_',' ').title() for c in cs]);ax.set_title('Secret words' if domain=='word' else 'Future plot facts');ax.set_ylim(25,100);ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Order-averaged discrimination (%)');axes[1].legend(fontsize=8,loc='lower right');fig.tight_layout();fig.savefig(FIG/'behavior.pdf');plt.close(fig)
    # Tables are generated, not hand-transcribed.
    lines=[r'\begin{tabular}{llrrr}',r'\toprule Domain & Condition & Pairs & Sonnet (95\% CI) & Mini (pairs) \\',r'\midrule']
    for d in ['word','plot']:
        for c in (['plain','filler','outline','decoy'] if d=='word' else ['plain','filler','outline','no_secret']):
            s=next(r for r in sums if r['domain']==d and r['condition']==c and r['reader']=='sonnet');m=next(r for r in sums if r['domain']==d and r['condition']==c and r['reader']=='mini')
            lines.append(f"{d.title()} & {c.replace('_',' ').title()} & {s['n']} & {100*s['mean']:.1f} [{100*s['ci'][0]:.1f}, {100*s['ci'][1]:.1f}] & {100*m['mean']:.1f} ({m['n']}) \\")
    lines += [r'\bottomrule',r'\end{tabular}'];Path('paper_draft/behavior_table.tex').write_text('\n'.join(lines).replace(' \\\n',' \\\\\n'))
    lines=[r'\begin{tabular}{llrrr}',r'\toprule Domain & Contrast & Difference [95\% CI] & Item CI & $p_{\mathrm{Holm}}$ \\',r'\midrule']
    for r in primary:
        lines.append(f"{r['domain'].title()} & {r['contrast']} & {100*r['delta']:.1f} [{100*r['ci'][0]:.1f}, {100*r['ci'][1]:.1f}] & [{100*r['cluster_ci'][0]:.1f}, {100*r['cluster_ci'][1]:.1f}] & {'$<0.0001$' if r['p_holm']<0.0001 else format(r['p_holm'],'.4f')} \\")
    lines += [r'\bottomrule',r'\end{tabular}'];Path('paper_draft/contrast_table.tex').write_text('\n'.join(lines).replace(' \\\n',' \\\\\n'))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
