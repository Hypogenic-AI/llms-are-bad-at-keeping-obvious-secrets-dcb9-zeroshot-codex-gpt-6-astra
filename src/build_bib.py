import json,html
from pathlib import Path
entries=[]
for r in json.loads(Path('results/literature_metadata.json').read_text()):
    title=html.unescape(r['tags']['citation_title']);authors=' and '.join(r['authors']).replace('Cywiński',r"Cywi{\'n}ski")
    entries.append('@misc{p'+r['id'].replace('.','')+',\n  title={'+title+'},\n  author={'+authors+'},\n  year={20'+r['id'][:2]+'},\n  eprint={'+r['id']+'},\n  archivePrefix={arXiv},\n  url={'+r['url']+'}\n}')
for name in ['llms-keep-secrets-claude','llms-keep-secrets-codex','llm-keeping-secrets-gemini']:
    entries.append('@misc{'+name+',\n title={LLMs Are Bad at Keeping Obvious Secrets: '+name+'},\n author={{Hypogenic AI}},\n year={2026},\n note={Public autonomous-research project; accessed October 2, 2026},\n url={https://github.com/Hypogenic-AI/'+name+'}\n}')
entries.append('@misc{gemma3,\n title={Gemma 3 Technical Report},\n author={{Gemma Team}},\n year={2025},\n eprint={2503.19786},\n archivePrefix={arXiv},\n url={https://arxiv.org/abs/2503.19786}\n}')
Path('paper_draft/references.bib').write_text('\n\n'.join(entries))
