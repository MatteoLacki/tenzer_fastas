To use the repo:

0. clone it
1. run
```
make all
```

That will run `python get_fastas.py default_fastas_wishlist.csv fastas`.
The first file contains entries to download.
It is a csv file with obligatory columns TAG, URL, and NAME (these also must be the first 3 columns).

TAG: should contain a unique short name of the entry, no whitespaces, e.g. `human`.
URL: the http(s) address of the entry to download. There link should not point to a zipped file.
NAME: a template of the name, e.g. `Human_{yyyymmdd}_UniProt_Taxon9606_Reviewed_{cnt}entries.fasta`.
Each should include wildcards `{yyyymmdd}` and `{cnt}` which will be filled with the current date and the number of downloaded fastas.

The outputs will be stored by default in the `fastas` location.
If you want to change it, make sure it exists.

The outputs contain all the up-to-date fastas and the latest contaminants from Hao's group.
Also, the repo contains the latest list of contaminants used by the Tenzer group.

Download throttling (HTTP 429) and transient server errors are retried up to
three times. Failed downloads make the command exit with an error instead of
silently producing an incomplete build.

Dependencies:
The script needs Python 3 (standard library only) and `git`.
The Makefile additionally uses `rm` and `mkdir`.

Tenzer contaminants follow Hao's accession convention: `sp|Cont_P02538|K2C6A_HUMAN`.
The `Cont_` prefix marks the accession; the protein name has no `_CONTA` suffix.
The redundant second P38507 record was removed from the Tenzer source.

Merging preserves all records by default, including identical sequences under
human and contaminant accessions. Distinct labels do not distinguish endogenous
protein from contamination; downstream grouping and filtering must handle this
ambiguity explicitly. Downloaded databases and contaminant source files are not
modified by the merge.

Warnings on stderr report duplicate accessions, duplicate sequences (including
different headers), and underlying protein names containing `_CONTA`. Warnings
include counts and the first ten example pairs per category and source; ID
collisions with different sequences are explicitly labelled.

To remove duplicate accessions and identical sequences instead, pass
`--deduplicate-contaminants`. Contaminant records take priority; within each
source, the first retained record wins. Sequence comparison ignores whitespace
and wrapping but preserves residue letters (including I/L distinctions).
Accessions use the middle field of UniProt headers (`sp|ACCESSION|NAME`), otherwise
the first whitespace-delimited header token. `--no-deduplicate-contaminants`
explicitly selects the default preservation behavior.

Filename entry counts describe the underlying download; the final merged record
count is printed on stderr.

TSV audit reports are local artifacts and are excluded from version control.
