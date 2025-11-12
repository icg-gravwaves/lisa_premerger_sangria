MAIN = lisa_premerger_sangria_paper
TEXFILES = *.tex 
FIGURES = images/*.png
BIB = bibliography

.PHONY: all pdf clean

all: clean pdf pdf clean

pdf: $(TEXFILES) $(FIGURES)
	latexmk -pdf -bibtex -g -interaction=nonstopmode -synctex=1 -file-line-error $(MAIN).tex
	latexmk -pdf -bibtex -g -interaction=nonstopmode -synctex=1 -file-line-error $(MAIN).tex

clean:
	latexmk -c $(MAIN).tex
	# cleanup fallback
	rm -f *.fdb_latexmk *.fls lisa_premerger_sangria_paperNotes.bib lisa_premerger_sangria_paper.synctex.gz