import httpx,re,json
from pathlib import Path
ids=['2605.10794','2505.14352','2502.06258','2404.00859','2402.17119','2511.12381','2601.06973','2310.17884']
rows=[]
for id in ids:
    t=httpx.get('https://arxiv.org/abs/'+id,follow_redirects=True).text
    Path('data/'+id+'.html').write_text(t)
    tags=dict(re.findall(r'<meta name="(citation_[^"]+)" content="([^"]+)"',t))
    authors=re.findall(r'<meta name="citation_author" content="([^"]+)"',t)
    rows.append(dict(id=id,tags=tags,authors=authors,url='https://arxiv.org/abs/'+id))
Path('results/literature_metadata.json').write_text(json.dumps(rows,indent=2))
u='https://cichicago.substack.com/p/week-of-122925-010426-first-competition'
t=httpx.get(u,follow_redirects=True).text;Path('data/prior_newsletter.html').write_text(t)
print('related links', [x for x in re.findall('href="([^"]+)"',t) if any(z in x.lower() for z in ['secret','github'])][:30])
