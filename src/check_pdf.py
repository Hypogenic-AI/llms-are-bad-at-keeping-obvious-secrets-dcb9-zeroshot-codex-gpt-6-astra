from pathlib import Path
import json
import pymupdf
pdf=Path('paper_draft/main.pdf');doc=pymupdf.open(pdf)
texts=[p.get_text() for p in doc];full='\n'.join(texts)
assert len(doc)>=6
for required in ['Abstract','Introduction','Related work','Conclusion','References','81.2','54.6','95.8','91.7']:
    assert required in full,required
assert not any(x in full for x in ['TODO','TBD','??'])
log=Path('paper_draft/main.log').read_text()
assert 'undefined' not in log.lower()
assert 'Overfull' not in log
# Check all text stays on the physical page.
for p in doc:
    for b in p.get_text('blocks'):
        assert b[0]>=0 and b[1]>=0 and b[2]<=p.rect.width+1 and b[3]<=p.rect.height+1
info={'pages':len(doc),'bytes':pdf.stat().st_size,'checks':'passed','page_text_characters':[len(t) for t in texts]}
Path('results/pdf_inspection.json').write_text(json.dumps(info,indent=2));print(info)
Path('data/pdf_preview').mkdir(exist_ok=True)
for i in [0,4,5,len(doc)-1]:doc[i].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(f'data/pdf_preview/final_page{i+1}.png')
