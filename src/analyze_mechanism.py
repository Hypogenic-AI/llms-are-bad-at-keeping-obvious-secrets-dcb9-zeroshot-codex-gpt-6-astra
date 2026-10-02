import json,re
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import ci,signflip,load_judgments
ROOT=Path('results/mechanism');FIG=Path('paper_draft/figures')
def main():
    raw=pd.read_json(ROOT/'readout.json');X=np.load(ROOT/'teacher_states.npz')['states'];f=np.load(ROOT/'directions.npz');D=f['directions'];mu=f['reference'];words=['lighthouse','violin','cactus','telescope'];layers=[12,24,36,48];positions=[64,192,384,576]
    readouts=[]
    for mode in ['raw','neutral_paired','secret_centered']:
        for li,l in enumerate(layers):
            z=X[12:,1:,li].copy()
            if mode=='raw':z-=mu[li]
            elif mode=='neutral_paired':z-=X[12:,0:1,li]
            else:z-=z.mean(1,keepdims=True)
            scores=np.einsum('nsph,kh->nspk',z,D[:,li]);correct=(scores.argmax(-1)==np.arange(4)[None,:,None])
            for pi,p in enumerate(positions):
                a=correct[:,:,pi].mean(1)
                readouts.append(dict(mode=mode,layer=l,position=p,accuracy=float(a.mean()),ci=ci(a),n_contexts=12,n_states=48))
    # Three equally tokenized secrets exclude telescope's extra token.
    equal_length=[]
    for li,l in enumerate(layers):
        means=X[:12,1:4,li].mean(axis=(0,2));dirs=means-means.mean(0);dirs/=np.linalg.norm(dirs,axis=-1,keepdims=True)
        z=X[12:,1:4,li].copy();z-=z.mean(1,keepdims=True)
        scores=np.einsum('nsph,kh->nspk',z,dirs);correct=(scores.argmax(-1)==np.arange(3)[None,:,None])
        for pi,p in enumerate(positions):
            a=correct[:,:,pi].mean(1);equal_length.append(dict(layer=l,position=p,accuracy=float(a.mean()),ci=ci(a),chance=1/3))
    # A reproducible nuisance-removal diagnostic, not an independently deployed decoder.
    (ROOT/'readout_sensitivity.json').write_text(json.dumps(readouts,indent=2))
    df,av=load_judgments(ROOT/'judgments');av.to_csv(ROOT/'pair_scores.csv',index=False)
    sums=[];contrasts=[]
    if len(av):
        for (r,c),g in av.groupby(['reader','condition']):sums.append(dict(reader=r,condition=c,n=len(g),mean=g.score.mean(),ci=ci(g.score)))
        for reader in ['sonnet','mini']:
            p=av[av.reader==reader].pivot(index='block',columns='condition',values='score').dropna()
            if len(p):
                for c in ['target','random','other']:
                    x=p[c]-p['base'];contrasts.append(dict(reader=reader,contrast=c+'-base',n=len(x),delta=float(x.mean()),ci=ci(x),p=signflip(x)))
                for c in ['random','other']:
                    x=p['target']-p[c];contrasts.append(dict(reader=reader,contrast='target-'+c,n=len(x),delta=float(x.mean()),ci=ci(x),p=signflip(x)))
    quality=[]
    for p in (ROOT/'quality').glob('*.json'):
        r=json.loads(p.read_text())
        if r['scores']:quality.append(dict(id=r['id'],condition=r['condition'],**r['scores']))
    q=pd.DataFrame(quality)
    summaries=q.groupby('condition')[['coherence','fluency','nonrepetition']].mean().reset_index().to_dict('records') if len(q) else []
    stories=[];traces=[]
    for p in (ROOT/'stories').glob('*.json'):
        r=json.loads(p.read_text());tokens=r['token_ids'];eos=next((i for i,t in enumerate(tokens) if t in [1,106]),len(tokens));ws=re.findall(r'\b\w+\b',r['text'].lower());grams=list(zip(ws,ws[1:],ws[2:],ws[3:]))
        stories.append(dict(block=r['block'],condition=r['condition'],side=r['side'],words=len(r['text'].split()),tokens=eos,truncated=eos==len(tokens),literal=bool(re.search(r'\b'+r['secret']+r'\b',r['text'],re.I)),relative_norm=float(np.mean([v for v,t in zip(r['relative_intervention_norm'],r['trace']) if t['step']<eos])),distinct4=len(set(grams))/max(1,len(grams))))
        valid=[t for t in r['trace'] if t['step']<eos]
        if r['condition']=='base':
            # Normalize by training direction magnitude and summarize before intervention.
            score=float(np.mean([t['scores'][r['secret_index']]/f['norms'][r['secret_index'],1] for t in valid]))
            traces.append(dict(block=r['block'],side=r['side'],activation=score))
    st=pd.DataFrame(stories);st.to_csv(ROOT/'story_diagnostics.csv',index=False)
    diagnostics=st.groupby('condition').agg(n=('words','size'),mean_words=('words','mean'),mean_tokens=('tokens','mean'),truncated=('truncated','sum'),literal=('literal','sum'),relative_norm=('relative_norm','mean'),distinct4=('distinct4','mean')).reset_index().to_dict('records') if len(st) else []
    correlations=[]
    if traces:
        ta=pd.DataFrame(traces).groupby('block').activation.mean()
        for reader in ['sonnet','mini']:
            g=av[(av.reader==reader)&(av.condition=='base')].set_index('block').join(ta).dropna()
            if len(g)>3:
                rho,p=spearmanr(g.score,g.activation);correlations.append(dict(reader=reader,n=len(g),rho=float(rho) if np.isfinite(rho) else None,p=float(p) if np.isfinite(p) else None))
    clean=[]
    if len(st):
        contaminated=set(st[st.condition.isin(['base','target']) & st.literal].block)
        for reader in ['sonnet','mini']:
            p=av[(av.reader==reader)&av.condition.isin(['base','target'])&~av.block.isin(contaminated)].pivot(index='block',columns='condition',values='score').dropna()
            if len(p):
                delta=p['target']-p['base'];clean.append(dict(reader=reader,n=len(p),base=float(p['base'].mean()),target=float(p['target'].mean()),delta=float(delta.mean()),ci=ci(delta)))
    result=dict(readouts=readouts,equal_length=equal_length,clean_literal_sensitivity=clean,summary=sums,contrasts=contrasts,quality=summaries,diagnostics=diagnostics,correlations=correlations)
    (ROOT/'analysis.json').write_text(json.dumps(result,indent=2))
    fig,axes=plt.subplots(1,3,figsize=(10,3.1),sharey=True)
    for ax,mode,title in zip(axes,['raw','neutral_paired','secret_centered'],['Raw states','Subtract no-secret state','Center across secrets (oracle)']):
        for l in layers:
            rr=[r for r in readouts if r['mode']==mode and r['layer']==l];ax.plot(positions,[100*r['accuracy'] for r in rr],'-o',label=f'Layer {l}',ms=3)
        ax.axhline(25,color='gray',ls='--');ax.set_ylim(0,100);ax.set_title(title,fontsize=10);ax.set_xlabel('Continuation token');ax.grid(alpha=.15)
    axes[0].set_ylabel('Four-way readout accuracy (%)');axes[-1].legend(fontsize=7);fig.tight_layout();fig.savefig(FIG/'readout.pdf');plt.close(fig)
    if len(sums)==8:
        fig,ax=plt.subplots(figsize=(5,3));conds=['base','target','random','other']
        for off,reader,col in [(-.08,'sonnet','#225ea8'),(.08,'mini','#d95f0e')]:
            rr=[next(r for r in sums if r['reader']==reader and r['condition']==c) for c in conds];y=np.array([r['mean'] for r in rr]);b=np.array([r['ci'] for r in rr]).T
            ax.errorbar(np.arange(4)+off,y*100,yerr=np.array([y-b[0],b[1]-y])*100,fmt='o',capsize=3,label=reader,color=col)
        ax.axhline(50,ls='--',color='gray');ax.set_xticks(range(4),['Baseline','Target','Random','Other concept']);ax.set_ylabel('Discrimination (%)');ax.set_ylim(0,100);ax.legend();fig.tight_layout();fig.savefig(FIG/'ablation.pdf');plt.close(fig)
    print(json.dumps({k:v for k,v in result.items() if k!='readouts'},indent=2))
if __name__=='__main__':main()
