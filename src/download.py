import os,json
os.environ['HF_HOME']=os.path.abspath('.cache/huggingface')
from huggingface_hub import snapshot_download,HfApi
from pathlib import Path
for repo in ['google/gemma-3-12b-it','unsloth/gemma-3-12b-it']:
    try:
        revision='96b6f1eccf38110c56df3a15bffe176da04bfd80' if repo=='google/gemma-3-12b-it' else None
        info=HfApi().model_info(repo,revision=revision)
        p=snapshot_download(repo,revision=info.sha,allow_patterns=['*.json','*.safetensors','tokenizer*','*.model','*.jinja'],local_dir='models/gemma-3-12b-it')
        Path('results/model_download.json').write_text(json.dumps({'repo':repo,'revision':info.sha,'path':p},indent=2))
        print('Downloaded',repo,info.sha,flush=True)
        break
    except Exception as e:
        print('Download failed',repo,type(e).__name__,flush=True)
else: raise RuntimeError('No model available')
