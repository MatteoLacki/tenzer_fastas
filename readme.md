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


Dependencies:
The script runs in bash under linux.
We assume presence of the following tools:
`rm`, `git`, `shopt`, `mkdir`, `cp`, `mv`, `wget`.
