import asyncio,json,random,argparse
from pathlib import Path
from api import call,content
async def main(limit):
    rows=json.loads(Path('results/design.json').read_text());random.Random(110).shuffle(rows)
    if limit: rows=rows[:limit]
    folder=Path('results/stories');folder.mkdir(exist_ok=True)
    done=0
    async def one(row):
        nonlocal done
        f=folder/(row['id']+'.json')
        if not f.exists():
            d=await call('google/gemma-3-12b-it',[{'role':'user','content':row['prompt']}],temperature=.9,max_tokens=1100,seed=row['seed'])
            d.update(row);d['text']=content(d);f.write_text(json.dumps(d,indent=2))
        done+=1
        if done%40==0:print('stories',done,'/',len(rows),flush=True)
    await asyncio.gather(*(one(r) for r in rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=0);args=p.parse_args();asyncio.run(main(args.limit))
