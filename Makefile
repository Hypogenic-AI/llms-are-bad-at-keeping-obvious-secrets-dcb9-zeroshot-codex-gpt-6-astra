PYTHON := .venv/bin/python
.PHONY: analysis paper audit
analysis:
	$(PYTHON) src/analyze.py > results/analysis.log
	$(PYTHON) src/analyze_mechanism.py > results/mechanism_analysis.log
	$(PYTHON) src/diagnostics.py > results/diagnostics.log
	$(PYTHON) src/report_tables.py
	$(PYTHON) src/intervention_text.py
paper:
	cd paper_draft && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper_draft && bibtex main
	cd paper_draft && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper_draft && pdflatex -interaction=nonstopmode -halt-on-error main.tex
audit:
	$(PYTHON) src/audit.py
