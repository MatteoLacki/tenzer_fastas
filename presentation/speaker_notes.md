# Identical sequences, different labels

## 1. Identical sequences. Different labels.

Purpose: agree on a database merge policy and a reproducible filtering policy. This deck advocates removing exact sequence redundancy while keeping biological identity and explicit project exceptions. It does not assert a measured FDR effect.

## 2. The reported 117 drops are fully explained

Original input contained 20,430 human records and 169 Tenzer records. There were 117 extra records by accession: 116 cross-source collisions and one repeated P38507 within Tenzer. Every accession collision had an identical sequence. Header strings alone concealed most collisions.

## 3. A different name does not create a different ID

These are actual P02538 header tokens. The middle pipe-delimited field is the accession, and remains P02538 in both records. The CONTA suffix changes the protein name. Default DIA-NN behavior keeps the first record for a repeated ID. Renaming the accession would avoid an ID collision but would still leave sequence redundancy.

## 4. Two labels cannot distinguish biological origin

This is a statement about identifiability from sequence evidence, not about whether contamination is likely. The measured abundance can be a mixture of endogenous and exogenous molecules. Origin requires contextual evidence such as controls; a second database label cannot supply it.

## 5. The disagreement contains two separate questions

Both concerns are valid. Removing an exact sequence copy is a database representation decision. Excluding an identified sequence from downstream analysis is a project interpretation decision. Keeping two labels is not a substitute for specifying a filtering rule.

## 6. One search result can support different project policies

These are hypothetical examples, not a claim that every keratin should be excluded in a standard project or retained in an epithelial project. Both projects see the same identified sequence and contaminant-candidate annotation. Their saved policy differs. Retaining a candidate does not prove it is endogenous.

## 7. Contaminant groups can make exceptions manageable

This grouping scheme is a proposal for the group to review, not an implemented or universal standard. A sequence may be a member of multiple groups. Accession overrides should take precedence over group exclusions, and the effective policy should be exported with results.

## 8. A merge policy must distinguish three cases

The first rule is the requested example: drop the human copy and retain the contaminant representative of an identical sequence. Alias mapping preserves all original identities, including identical sequences from different genes or loci. Same accession with different sequences requires distinct record identifiers or explicit review; choosing the longest is not generally justified.

## 9. Make the policy reproducible from FASTA to results

This is a proposed end state. Keep downloaded source databases intact. Canonicalize identifiers for comparison without erasing their source labels. Save sequence-to-alias mapping and decisions. Apply a versioned project policy to retained identifications. The unmodified results should remain available for reanalysis.

## 10. FDR is a caveat, not the central argument

No before/after search experiment in this work measured a change in protein FDR or identification sensitivity. Duplicate accessions and identical sequences are distinct issues. Inference software can select representatives or group redundant records; two entries need not be counted as two independent protein discoveries. Avoid asserting an inevitable or quantified FDR penalty.

## 11. Current build: verified cleanup, remaining policy choices

The current code removes duplicate accessions and sequences with contaminant priority and emits diagnostics. All 84 generated outputs were checked for unique IDs and sequences. Human reviewed plus Tenzer has 20,404 records after removing 195 records by combined deduplication. Warning categories overlap and must not be summed. Remaining work is explicitly proposed, not implemented by this deck.

## 12. Evidence and discussion references

Local audit files: duplicate_protein_ids_tenzer.tsv and warnings_summary_20261112.tsv in the repository root. Original 6 Nov accession-collision audit and 12 Nov rerun agree on the reviewed-human/Tenzer case. Source databases contain additional sequence duplicates unrelated to contaminants. The final policy in this deck is a proposal, not a claim of a universal standard.