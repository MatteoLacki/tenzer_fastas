rule get_human_swissprot_trembl:
    output:
        "fastas/human_sp_tr.fasta"
    threads:
        1
    shell:
        """
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?compressed=false&format=fasta&query=%28%28proteome%3AUP000005640%29%29"
        """


rule get_human_swissprot:
    output:
        "fastas/human.fasta"
    threads:
        1
    shell:
        """
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A9606%29%29%20AND%20%28reviewed%3Atrue%29"
        """


rule get_mouse_swissprot:
    output:
        "fastas/mouse.fasta"
    threads:
        1
    shell:
        """ 
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A10090%29%29%20AND%20%28reviewed%3Atrue%29"
        """


rule get_wheat_swissprot:
    output:
        "fastas/wheat.fasta"
    threads:
        1
    shell:
        """
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A4565%29%29"
        """


rule get_ecoli_swissprot:
    output:
        "fastas/ecoli.fasta"
    threads:
        1
    shell:
        """
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A83333%29%29%20AND%20%28reviewed%3Atrue%29"
        """


rule get_yeast_swissprot:
    output:
        "fastas/yeast.fasta"
    threads:
        1
    shell:
        """
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A83333%29%29%20AND%20%28reviewed%3Atrue%29"
        """

rule get_hye:
    output:
        "fastas/hye.fasta"
    input:
        "fastas/human.fasta",
        "fastas/yeast.fasta",
        "fastas/ecoli.fasta",
    shell:
        "cat {input} > {output}"



rule download_all:
    threads:
        1_000
    output:
        "fastas/all.done",
    input:
        "fastas/human.fasta",
        "fastas/yeast.fasta",
        "fastas/ecoli.fasta",
        "fastas/mouse.fasta",
        "fastas/hye.fasta",
        "fastas/human_sp_tr.fasta",


rule append_contaminants:
    input:
        "fastas/{organism}.fasta",
        "contaminants/{contaminats}.fasta",
    output:
        "fastas/{organism}_contaminated_with_{contaminats}.fasta"
    threads:
        1
    shell:
        "cat {input} > {output}"
