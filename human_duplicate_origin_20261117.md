# Human_all duplicate sequence origin audit

Audited `fastas/Human_all_20261113_327154entries.fasta` on 2026-11-17.
Exact full-record amino-acid sequence equality; whitespace ignored, residue letters preserved.

## Download origin

`default_fastas_wishlist.csv` requests all UniProtKB entries with `taxonomy_id:9606`.
It does not restrict reviewed status or proteome and does not request expanded isoforms.
`fetch` writes the downloaded response directly. This source FASTA has no appended
contaminants. Separate UniProt entries can encode the same sequence even without
`includeIsoform=true`.

## Local measurements

| Measurement | Count |
|---|---:|
| FASTA records / distinct accessions | 327,154 |
| Reviewed records (`sp`) | 20,430 |
| Unreviewed records (`tr`) | 306,724 |
| Distinct full-record sequences | 286,050 |
| Extra sequence copies beyond one per sequence | 41,104 |
| Identical-sequence groups with at least two entries | 22,402 |
| Records belonging to those groups | 63,506 |
| Repeated accessions | 0 |
| Cont_ accessions | 0 |

| Duplicate group composition | Groups | Extra copies |
|---|---:|---:|
| Unreviewed only | 20,329 | 38,991 |
| Reviewed and unreviewed | 2,026 | 2,042 |
| Reviewed only | 47 | 71 |

21,466 groups have one distinct nonempty gene label, 916 have multiple labels,
and 20 have none. Header gene names are annotations, not definitive locus mappings.

48,443 duplicate-group records have accessions beginning A0ACP2. Within this
prefix alone, 30,320 copies are redundant: 73.8% of all extra copies in the file.
The prefix is a cohort indicator; provenance was fetched for two example entries,
not every member of this cohort.

## Traced examples

1. **MSX1: 94 identical records, 146 aa.** E9KXS6 links to genomic nucleotide
   HM213907 / protein ADR64840.1; E9KXS7 links to HM213908 / ADR64841.1. Both
   reference the dental agenesis study PMID 21111400 and entered UniProt in 2011.
   These are separate source nucleotide submissions yielding the same translated
   fragment. Only these two members were checked against source metadata.
   Source: https://rest.uniprot.org/uniprotkb/E9KXS6.json and
   https://rest.uniprot.org/uniprotkb/E9KXS7.json

2. **CYP3A5: 80 identical records, 39 aa.** A0ACP2A733 links to transcript
   ENST00000976535.1 / protein ENSP00000646352.1; A0ACP2A738 links to
   ENST00000976537.1 / ENSP00000646354.1. Both belong to ENSG00000106258.18,
   reference an Ensembl JUL-2026 submission, and first appeared in UniProt on
   2026-11-04. Distinct annotated transcripts yield identical translations.
   Only these two members were checked against source metadata.
   Source: https://rest.uniprot.org/uniprotkb/A0ACP2A733.json and
   https://rest.uniprot.org/uniprotkb/A0ACP2A738.json

3. **HLA-DQA1: 53 identical records, 14 aa.** Q8MH00 links to mRNA AF533940 /
   AAM94854.1; Q8MH01 to AF533939 / AAM94853.1. Both cite work on alternative
   splicing/polyadenylation of the DQA1 3-prime untranslated region (PMID 15900489).
   Different nucleotide/transcript records need not imply different peptide
   sequences. Only these two members were checked against source metadata.
   Source: https://rest.uniprot.org/uniprotkb/Q8MH00.json and
   https://rest.uniprot.org/uniprotkb/Q8MH01.json

4. **Calmodulin: four identical records, 149 aa.** Local records P0DP23 (CALM1),
   P0DP24 (CALM2), P0DP25 (CALM3), and B4DJ51 (HEL-S-72 label) share the same
   sequence. Identical sequences can represent distinct genes; blindly discarding
   the other accessions loses identity information.

All six fetched example UniProt sequences were compared with their local FASTA
records and match exactly. Live metadata is saved in
`human_duplicate_provenance_20261117.json`. Every duplicate group member is
listed in `duplicate_sequences_human_all_20261113.tsv`.

## Interpretation

The redundancy is already present in the selected upstream UniProtKB dataset.
The large all-human download combines distinct unreviewed transcript/submission
records and reviewed proteins, including genuine distinct-gene sequence matches.
The observed duplicates are not repeated download blocks or contaminant appends.
FASTA files and merge policy were not changed during this audit.

UniProt documentation explains that identical sequences may be retained for
multiple genes: https://www.uniprot.org/help/checksum
