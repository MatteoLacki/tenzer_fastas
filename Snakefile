rule all:
    input:
        "fastas/human.fasta",
        "fastas/yeast.fasta",
        "fastas/ecoli.fasta",
        "fastas/mouse.fasta",
        "fastas/wheat.fasta",
        "fastas/hye.fasta",
        "contaminants/universal.fasta",

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
        wget -O {output} "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=%28%28taxonomy_id%3A4932%29%29+AND+%28reviewed%3Atrue%29"
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

rule get_Hao_group_contaminants:
    output:
        "contaminants/universal.fasta"
    shell:
        """
        rm -rf Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics || True
        git clone https://github.com/HaoGroup-ProtContLib/Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics.git
        shopt -s globstar
        mkdir -p contaminants
        cp Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics/**/*.fasta contaminants
        cp Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics/Universal\ protein\ contaminant\ FASTA/0602_Universal\ Contaminants.fasta {output}
        """




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
