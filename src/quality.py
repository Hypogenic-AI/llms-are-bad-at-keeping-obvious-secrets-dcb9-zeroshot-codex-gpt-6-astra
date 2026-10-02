import asyncio,json,random,re,argparse
from pathlib import Path
from api import call,content
async def main(local):
    if local:
        rows=[json.loads(f.read_text()) for f in Path('results/mechanism/stories').glob('*.json')]
        for r in rows:r['id']=r['block']+'_'+r['condition']+'_'+str(r['side'])
        out=Path('results/mechanism/quality')
    else:
        design=json.loads(Path('results/design.json').read_text());rows=[]
        for dom in ['word','plot']:
            for cond in sorted({r['condition'] for r in design if r['domain']==dom}):
                candidates=[r for r in design if r['domain']==dom and r['condition']==cond]
                random.Random(417).shuffle(candidates)
                for r in candidates[:30]:
                    f=Path('results/stories')/(r['id']+'.json')
                    if f.exists():rows.append(json.loads(f.read_text()))
        out=Path('results/quality')
    out.mkdir(exist_ok=True)
    async def one(r):
        f=out/(r['id']+'.json')
        if f.exists():return
        prompt='Evaluate this fictional prose independently of your preferred genre. Rate each dimension from 1 (very poor) to 5 (excellent): coherence (events make sense together), fluency (grammatical readable prose), and nonrepetition (avoids repetitive wording or stalled progression). Do not penalize an opening for lacking a final resolution. Return only JSON with numeric fields coherence, fluency, nonrepetition.\n\n'+r['text']
        d=await call('openai/gpt-4.1-mini',[dict(role='user',content=prompt)],max_tokens=100)
        s=content(d);m=re.search(r'\{.*\}',s,re.S)
        try:score=json.loads(m.group(0))
        except Exception:score=None
        d.update(id=r['id'],condition=r['condition'],domain=r['domain'],scores=score)
        f.write_text(json.dumps(d,indent=2))
    await asyncio.gather(*(one(r) for r in rows));print('quality',len(rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--local',action='store_true');a=p.parse_args();asyncio.run(main(a.local))
