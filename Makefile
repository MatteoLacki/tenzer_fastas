PYTHON ?= $(shell command -v python3 || command -v python)

all: clean_output
	mkdir fastas
	$(PYTHON) get_fastas.py default_fastas_wishlist.csv fastas

clean_output:
	rm -rf fastas contaminants/hao.fasta
