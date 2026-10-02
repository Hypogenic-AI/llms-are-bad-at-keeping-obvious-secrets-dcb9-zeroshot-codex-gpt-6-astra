import json
from pathlib import Path
M=json.loads(Path('results/mechanism/analysis.json').read_text())
def get(k,c):return next(r for r in M[k] if r['condition']==c and (k!='summary' or r['reader']=='sonnet'))
base=get('summary','base');target=get('summary','target');random=get('summary','random');other=get('summary','other')
assert all(x['n']==24 for x in [base,target,random,other])
c=next(r for r in M['contrasts'] if r['reader']=='sonnet' and r['contrast']=='target-base')
bd=get('diagnostics','base');td=get('diagnostics','target');rd=get('diagnostics','random');od=get('diagnostics','other')
bq=get('quality','base');tq=get('quality','target');rq=get('quality','random');oq=get('quality','other')
clean=next(r for r in M['clean_literal_sensitivity'] if r['reader']=='sonnet');cor=next(r for r in M['correlations'] if r['reader']=='sonnet')
pct=lambda x:f'{100*x:.1f}'
text=fr'''Table~\ref{{tab:mechanism}} and Figure~\ref{{fig:ablation}} show the completed local generation experiment. Primary-reader discrimination is {pct(base['mean'])}\% at baseline, {pct(target['mean'])}\% after target projection removal, {pct(random['mean'])}\% under the random control, and {pct(other['mean'])}\% under the other-concept control. Target minus baseline is ${100*c['delta']:+.1f}$ points (95\% interval: $[{100*c['ci'][0]:.1f}, {100*c['ci'][1]:.1f}]$). The experiment provides no evidence of useful mitigation by the targeted removal. The high local baseline differs from the main study's inventory and generation setup and is not evidence of an API/local implementation effect.

Target removal produces {td['literal']} exact-word disclosures among {td['n']} stories, versus {bd['literal']} at baseline. Removing all baseline--target blocks with a literal disclosure leaves {clean['n']} pairs; the exploratory target--baseline contrast is ${100*clean['delta']:+.1f}$ points (95\% interval: $[{100*clean['ci'][0]:.1f}, {100*clean['ci'][1]:.1f}]$). This filtered comparison is descriptive because inclusion depends on outcomes. A component involved in secret-dependent behavior need not support concealment when removed.

The random arm's lower discrimination accompanies degraded writing. Mean coherence is {bq['coherence']:.2f} at baseline, {tq['coherence']:.2f} for target removal, {rq['coherence']:.2f} for random removal, and {oq['coherence']:.2f} for the other-concept arm. Mean fluency is {bq['fluency']:.2f}, {tq['fluency']:.2f}, {rq['fluency']:.2f}, and {oq['fluency']:.2f}, respectively; {rd['truncated']} random-arm outputs reach the token cap. Such a change is not clean evidence of selective leakage removal. Mean perturbation/residual norm ratios during active generation are {100*td['relative_norm']:.2f}\% (target), {100*rd['relative_norm']:.2f}\% (random), and {100*od['relative_norm']:.2f}\% (other). The controls match the per-state subtraction rule, but not the realized dose across diverging trajectories.

'''
if cor['rho'] is not None:text+=fr"Baseline pair-averaged activation strength has an exploratory Spearman correlation of $\rho={cor['rho']:.2f}$ with primary-reader discrimination ($n={cor['n']}$, $p={cor['p']:.3f}$). This small, high-accuracy sample does not establish a reliable activation--leakage relationship. "
else:text+='The baseline discrimination scores have insufficient variation for a defined activation--leakage rank correlation. '
text+='Taken together, the readouts and interventions show the limits of this particular estimator and ablation, rather than identifying a necessary secret-leakage circuit.\n'
Path('paper_draft/intervention_results.tex').write_text(text)
