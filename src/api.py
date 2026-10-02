import os, asyncio, json, time, hashlib
from pathlib import Path
import httpx
BASE='https://openrouter.ai/api/v1'
SEM=asyncio.Semaphore(12)
async def call(model,messages,temperature=0,max_tokens=1000,seed=None):
    payload=dict(model=model,messages=messages,temperature=temperature,max_tokens=max_tokens)
    if seed is not None: payload['seed']=seed
    async with SEM:
        async with httpx.AsyncClient(timeout=180) as client:
            for attempt in range(6):
                try:
                    r=await client.post(BASE+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['OPENROUTER_KEY']},json=payload)
                    r.raise_for_status(); d=r.json()
                    if 'choices' not in d: raise ValueError('No choices')
                    return {'request':payload,'response':d,'timestamp':time.time()}
                except Exception as e:
                    if attempt==5: raise RuntimeError(type(e).__name__) from None
                    await asyncio.sleep(2**attempt)
def content(d): return d['response']['choices'][0]['message']['content']
async def smoke():
    for m in ['google/gemma-3-12b-it','openai/gpt-4.1-mini']:
        d=await call(m,[{'role':'user','content':'Reply with OK.'}],max_tokens=10)
        print(m,content(d))
        Path('results/smoke_'+m.split('/')[-1]+'.json').write_text(json.dumps(d,indent=2))
if __name__=='__main__': asyncio.run(smoke())
