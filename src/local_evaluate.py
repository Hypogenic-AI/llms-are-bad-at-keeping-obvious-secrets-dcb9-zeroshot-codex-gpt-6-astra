import json,asyncio
from pathlib import Path
from judge import evaluate
from quality import main as quality
async def main():
    while True:
        files=list(Path('results/mechanism/stories').glob('*.json'));groups={}
        for f in files:
            r=json.loads(f.read_text());groups.setdefault((r['block'],r['condition']),[]).append(r)
        rows=[]
        for (b,c),rs in groups.items():
            if len(rs)!=2:continue
            rs.sort(key=lambda r:r['side']);r=rs[0]
            rows.append(dict(block=b,condition=c,domain='word',target=r['target'],item=r['item'],rep=r['rep'],texts=[x['text'] for x in rs]))
        await evaluate(rows,Path('results/mechanism/judgments'),['sonnet','mini'])
        await quality(True)
        print('local evaluated',len(rows),'pairs',flush=True)
        if len(files)==192:break
        await asyncio.sleep(30)
if __name__=='__main__':asyncio.run(main())
