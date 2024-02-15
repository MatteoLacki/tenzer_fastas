all: clean_output
	mkdir fastas
	python get_fastas.py default_fastas_wishlist.csv fastas

clean_output:
	rm -rf fastas contaminats/hao.fasta
