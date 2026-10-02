# Historical failed smoke test for Transformers 5.18 / PyTorch 2.14; not part of reproduction.
import os,time,json
os.environ['HF_HOME']=os.path.abspath('.cache/huggingface')
import torch,transformers
from transformers import AutoTokenizer,AutoModelForImageTextToText
print(torch.__version__,transformers.__version__,flush=True)
t=time.time();tok=AutoTokenizer.from_pretrained('models/gemma-3-12b-it');model=AutoModelForImageTextToText.from_pretrained('models/gemma-3-12b-it',dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa').eval()
print('load',time.time()-t,flush=True)
print(type(model.model),type(model.model.language_model),len(model.model.language_model.layers),flush=True)
x=tok.apply_chat_template([{'role':'user','content':'Write a sentence about lunch.'}],add_generation_prompt=True,return_tensors='pt',return_dict=True).to('cuda')
with torch.inference_mode():y=model.generate(**x,max_new_tokens=25,do_sample=False)
print(tok.decode(y[0]),flush=True)
