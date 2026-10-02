# Do outlines help language models keep secrets?

This project tests whether an external outline reduces unintended secret leakage in fiction beyond adding irrelevant context. It includes a controlled behavioral study and an exploratory local residual-stream study of Gemma 3 12B IT.

The finished paper is [`paper_draft/main.pdf`](paper_draft/main.pdf), with LaTeX entry point [`paper_draft/main.tex`](paper_draft/main.tex).

## Main behavioral findings

We generated **1,440 stories**: 120 independent secret-word pairs per condition and 60 same-premise plot-secret pairs per condition. Claude Sonnet 4.6 and GPT-4.1 mini evaluated both presentation orders. Reversed-order judgments were averaged within a pair before inference.

- **Secret words:** primary-reader discrimination was **81.2%** with ordinary prompting, **79.6%** with matched-word-count filler, **54.6%** with a concrete outline, and **72.1%** with a decoy. The outline–filler reduction was **25.0 percentage points**, with a paired 95% interval of **19.2–30.8 points**. The secondary reader corroborated the large reduction even under worst-case bounds for its refused requests.
- **Future plot facts:** discrimination was **55.8%** for ordinary prompting, **57.5%** for filler, and **48.3%** for a generic opening outline. The outline–filler contrast survived the planned correction; outline–ordinary prompting did not. This is weaker evidence than the word experiment.
- **Measurement caveats:** reader position bias was substantial. The secondary reader returned 86 content-filter refusals on word comparisons; these are preserved and reported. No behavioral word story literally contained its secret, and no behavioral story hit the output cap.
- **Interpretation:** specific outlines constrain content choices. This experiment does not establish that they separate internal planning from prose generation, nor that near-chance discrimination guarantees secrecy.

The local study uses matched continuations, four secret words, residual readouts, and **192 locally generated stories** with baseline, target-direction removal, random-direction control, and other-concept control. Its exact results and caveats are in the paper and `results/mechanism/analysis.json`. Targeted removal scored **95.8%** discrimination versus **91.7%** at baseline (difference **+4.2 points**, 95% interval **−6.2 to +16.7**) and produced **6 literal disclosures out of 48 stories**, versus zero at baseline. Random removal degraded writing quality. The experiment does not validate successful single-direction secret erasure. Post hoc supervised and equal-token-length readouts are explicitly distinguished from the original centroid readout.

## Workspace

- `src/design.py`: fixed prompts, 15 secret words, 12 concrete outlines, 20 paired plot-fact scenarios.
- `src/behavior.py`, `src/judge.py`, `src/quality.py`: resumable API experiments, blinded two-order readers, and quality ratings.
- `src/mechanism.py`: local teacher forcing, frozen source continuations, direction estimation, interventions, and generation traces.
- `src/probe.py`: explicitly post hoc supervised readout and equal-token-length controls.
- `src/analyze.py`, `src/analyze_mechanism.py`, `src/diagnostics.py`, `src/report_tables.py`: statistics, figures, and tables from raw results.
- `src/audit.py`: completeness, prompt/response integrity, and label/order checks; records SHA-256 checksums.
- `results/protocol.md`: design recorded before behavioral outcome inspection, with dated-session technical amendments and post hoc analyses identified.
- `results/stories/`, `results/judgments/`, `results/quality/`: complete API requests (without credentials), responses, usage, and extracted data.
- `results/mechanism/`: local source texts, float32 residual snapshots, directions, raw generations, judgments, quality scores, and analyses.
- `paper_draft/`: manuscript source, generated tables/figures, bibliography, and compiled PDF.
- `data/`, `models/`, `.cache/`, `.venv/`: ignored downloads and environment files.

No results are simulated. Historical numerical findings are not imported into the experiment tables. The literature search also found earlier public autonomous outline studies, which the paper cites rather than claiming this is the first outline experiment.

## Reproduce the analysis from saved data

Use Linux, Python 3.12, `uv`, and a LaTeX installation with `pdflatex` and `bibtex`:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
make analysis
make paper
make audit
```

`analyze.py` recomputes statistics offline and uses the saved token-length diagnostics when the model tokenizer is absent. If the tokenizer is present, it recomputes those lengths too. To download the tokenizer and weights for local inference, run `.venv/bin/python src/download.py`. The download script pins the official model revision used here; access requires an authorized `HF_TOKEN`. It can fall back to the ungated `unsloth/gemma-3-12b-it` repository if necessary, but that fallback is **not** the checkpoint used for the reported local results. The stored analysis JSON, tables, and figures are available without downloading weights. `src/probe.py` can refit the supervised probes directly from saved residuals without a GPU or API calls.

The lock file records the actual isolated environment. Local inference used PyTorch 2.6.0, Transformers 4.51.3, bfloat16, and an initially idle NVIDIA RTX A6000 with 48 GB. The initial hardware check found 32 CPU cores. Setup failures and the short-continuation filtering amendment are retained in the logs.

## Rerun generation and evaluation

Set `OPENROUTER_KEY` and, for the official local checkpoint, `HF_TOKEN` in the environment. Scripts never record authentication headers. API calls incur usage charges; provider-returned costs are summarized in `results/analysis/extra.json`. Hosted model behavior and requested seeds are not guaranteed to be stable across reruns.

```bash
.venv/bin/python src/design.py
.venv/bin/python src/behavior.py
.venv/bin/python src/judge.py
.venv/bin/python src/quality.py
OMP_NUM_THREADS=8 .venv/bin/python src/mechanism.py
.venv/bin/python src/local_evaluate.py
OPENBLAS_NUM_THREADS=8 .venv/bin/python src/probe.py
make analysis
make paper
make audit
```

Scripts resume from existing files, so these commands preserve completed outputs. To generate a new independent replication, use a separate workspace or archive the relevant output directories first. Preserve `results/mechanism/neutral_sources.json` to use the exact frozen teacher-forced continuations from this run. Creating a new source manifest from a fresh behavioral run changes that part of the experiment.

The local generation cap is 900 tokens versus 1100 through the API, and the local inventory has only four concrete words. Do not compare their absolute leakage rates as an API-versus-local model effect. All intervention comparisons are within the local experiment. The filler is matched in words, not exact tokens; the paper reports the small remaining token-count differences.
