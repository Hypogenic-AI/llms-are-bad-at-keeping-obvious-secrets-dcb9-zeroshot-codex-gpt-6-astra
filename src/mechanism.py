"""Exploratory teacher-forced readout and norm-matched causal interventions."""
import os,json,time,random
from pathlib import Path
os.environ['HF_HOME']=os.path.abspath('.cache/huggingface')
os.environ['TOKENIZERS_PARALLELISM']='false'
import numpy as np
import torch
from transformers import AutoTokenizer,Gemma3ForConditionalGeneration
from design import word_prompt
WORDS=['lighthouse','violin','cactus','telescope'];LAYERS=[11,23,35,47];POSITIONS=[64,192,384,576]
ROOT=Path('results/mechanism');ROOT.mkdir(exist_ok=True)
def load():
    torch.set_num_threads(8)
    tok=AutoTokenizer.from_pretrained('models/gemma-3-12b-it',padding_side='left')
    m=Gemma3ForConditionalGeneration.from_pretrained('models/gemma-3-12b-it',torch_dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa').eval()
    return tok,m,m.language_model.model.layers

def main():
    tok,m,layers=load();print('loaded',flush=True)
    def prefix(w):
        p=word_prompt(w,'plain','','') if w else 'You are a creative writer. Write a complete short story of about 450 words in 5 to 8 paragraphs. Output only the story.\n'
        return tok.apply_chat_template([dict(role='user',content=p)],tokenize=False,add_generation_prompt=True)
    sf=ROOT/'neutral_sources.json'
    if not sf.exists():
        rows=sorted([json.loads(f.read_text()) for f in Path('results/stories').glob('*no_secret*.json')],key=lambda r:r['id'])
        rows=[r for r in rows if len(tok.encode(r['text'],add_special_tokens=False))>=576]
        if len(rows)<24:raise RuntimeError('Need 24 independent no-secret stories')
        sf.write_text(json.dumps([dict(id=r['id'],text=r['text']) for r in rows[:24]],indent=2))
    sources=json.loads(sf.read_text())
    arrfile=ROOT/'teacher_states.npz'
    if not arrfile.exists():
        allstates=[]
        for j,row in enumerate(sources):
            suffix=tok.encode(row['text'],add_special_tokens=False)
            if len(suffix)<576:raise RuntimeError('Neutral continuation too short')
            ws=[]
            for w in [None]+WORDS:
                p=tok.encode(prefix(w),add_special_tokens=False);ids=torch.tensor([p+suffix[:576]],device='cuda');states={}
                def make_hook(li):
                    def hook(module,args,out):
                        h=out[0] if isinstance(out,tuple) else out
                        states[li]=h[0,[len(p)+x-1 for x in POSITIONS]].detach().float().cpu().numpy()
                    return hook
                hs=[layers[li].register_forward_hook(make_hook(li)) for li in LAYERS]
                with torch.inference_mode():m(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False,logits_to_keep=1)
                for h in hs:h.remove()
                ws.append(np.stack([states[li] for li in LAYERS]))
            allstates.append(np.stack(ws));print('teacher',j+1,'/24',flush=True)
        X=np.stack(allstates);np.savez_compressed(arrfile,states=X,words=np.array(WORDS),layers=np.array(LAYERS),positions=np.array(POSITIONS))
    X=np.load(arrfile)['states'] # text, secret/no-secret, layer, position, feature
    # Secret-specific contrast removes shared effects of the secrecy instruction.
    means=X[:12,1:].mean(axis=(0,3)) # secret, layer, hidden
    D=means-means.mean(axis=0,keepdims=True)
    norms=np.linalg.norm(D,axis=-1);D/=norms[...,None]
    mu=X[:12,0].mean(axis=(0,2)) # layer, hidden
    np.savez_compressed(ROOT/'directions.npz',directions=D,reference=mu,norms=norms)
    test=[]
    for j in range(12,24):
        for s in range(4):
            for li in range(4):
                for pi,pos in enumerate(POSITIONS):
                    h=X[j,s+1,li,pi]-mu[li]
                    scores=D[:,li]@h
                    test.append(dict(source=j,secret=WORDS[s],layer=LAYERS[li]+1,position=pos,predicted=WORDS[int(scores.argmax())],correct=int(scores.argmax()==s),scores=scores.tolist()))
    (ROOT/'readout.json').write_text(json.dumps(test,indent=2))
    # Layer 24 chosen a priori, not optimized using readout or leakage outcomes.
    dt=torch.tensor(D[:,1],device='cuda');mt=torch.tensor(mu[1],device='cuda')
    rg=torch.Generator(device='cuda').manual_seed(77)
    rand=torch.randn((4,dt.shape[-1]),device='cuda',generator=rg)
    rand-=torch.sum(rand*dt,dim=-1,keepdim=True)*dt;rand/=rand.norm(dim=-1,keepdim=True)
    other=dt.roll(-1,0).clone();other-=torch.sum(other*dt,dim=-1,keepdim=True)*dt;other/=other.norm(dim=-1,keepdim=True)
    outdir=ROOT/'stories';outdir.mkdir(exist_ok=True)
    for rep in range(6):
        specs=[]
        for si,w in enumerate(WORDS):
            for side,idx in enumerate([si,(si+1+(rep%3))%4]):
                specs.append(dict(block=f'm{rep:02d}_{si}',item=si,rep=rep,side=side,secret=WORDS[idx],secret_index=idx,target=w,domain='word'))
        for cond in ['base','target','random','other']:
            files=[outdir/f"{r['block']}_{cond}_{r['side']}.json" for r in specs]
            if all(f.exists() for f in files):continue
            texts=[prefix(r['secret']) for r in specs];inputs=tok(texts,return_tensors='pt',padding=True).to('cuda')
            idx=torch.tensor([r['secret_index'] for r in specs],device='cuda');dirs=dt[idx]
            intervention=dirs if cond=='target' else rand[idx] if cond=='random' else other[idx]
            steps=[0];trace=[];normtrace=[]
            def hook(module,args,out):
                h=out[0] if isinstance(out,tuple) else out
                last=h[:,-1,:].float();co=torch.sum((last-mt)*dirs,dim=-1)
                if steps[0]%32==0:
                    trace.append(dict(step=steps[0],scores=((last-mt)@dt.T).detach().cpu().tolist()))
                    normtrace.append((co.abs()/last.norm(dim=-1)).detach().cpu().tolist())
                steps[0]+=1
                if cond!='base':
                    new=h.clone();new[:,-1,:]=(last-co[:,None]*intervention).to(h.dtype)
                    return (new,)+out[1:] if isinstance(out,tuple) else new
            handle=layers[23].register_forward_hook(hook)
            torch.manual_seed(82000+rep)
            t=time.time()
            with torch.inference_mode():
                y=m.generate(**inputs,do_sample=True,temperature=.9,top_p=1.,top_k=0,max_new_tokens=900,pad_token_id=tok.pad_token_id,eos_token_id=m.generation_config.eos_token_id,disable_compile=True)
            handle.remove()
            for k,(r,f) in enumerate(zip(specs,files)):
                tokens=y[k,inputs['input_ids'].shape[1]:].tolist()
                r=dict(r,condition=cond,prompt=word_prompt(r['secret'],'plain','',''),text=tok.decode(tokens,skip_special_tokens=True),token_ids=tokens,seed=82000+rep,trace=[dict(step=x['step'],scores=x['scores'][k]) for x in trace],relative_intervention_norm=[x[k] for x in normtrace])
                f.write_text(json.dumps(r,indent=2))
            print('generation',rep,cond,round(time.time()-t,1),'seconds',flush=True)
    print('complete',flush=True)
if __name__=='__main__':main()
