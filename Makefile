venv: clean_venv
	python3 -m venv venv
	venv/bin/pip install snakemake
clean_venv:
	rm -rf venv || True
all: venv
	venv/bin/snakemake -call fastas/{human,yeast,ecoli,mouse,hye}.fasta contaminats/universal.fasta
