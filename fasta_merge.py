"""Merge FASTA databases with duplicate diagnostics and optional deduplication."""

import sys
from pathlib import Path
from typing import NamedTuple


class Record(NamedTuple):
    header: str
    sequence: str
    text: str

    @property
    def accession(self):
        token = self.header.split()[0]
        fields = token.split("|")
        return fields[1] if len(fields) >= 3 else token


def records(path):
    """Read records without changing headers, sequence wrapping, or residues."""
    header = None
    lines = []
    with open(path) as stream:
        for line in stream:
            if line.startswith(">"):
                if header is not None:
                    yield Record(header, "".join("".join(lines[1:]).split()), "".join(lines))
                header = line[1:].strip()
                lines = [line]
            elif header is not None:
                lines.append(line)
            elif line.strip():
                raise ValueError(f"{path}: sequence data before first FASTA header")
    if header is not None:
        yield Record(header, "".join("".join(lines[1:]).split()), "".join(lines))


class Audit:
    """Count every duplicate; retain only ten example pairs per warning."""

    def __init__(self, label):
        self.label = label
        self.ids = {}
        self.sequences = {}
        self.counts = {}
        self.examples = {}

    def issue(self, kind, example):
        self.counts[kind] = self.counts.get(kind, 0) + 1
        examples = self.examples.setdefault(kind, [])
        if len(examples) < 10:
            examples.append(example)

    def add(self, record, underlying=False):
        if record.accession in self.ids:
            old_header, old_sequence = self.ids[record.accession]
            equality = "same sequence" if old_sequence == record.sequence else "DIFFERENT SEQUENCES"
            self.issue("duplicate accessions", f"{old_header}\n    {record.header} [{equality}]")
        else:
            self.ids[record.accession] = (record.header, record.sequence)
        if record.sequence in self.sequences:
            self.issue("duplicate sequences (including different headers)",
                       f"{self.sequences[record.sequence]}\n    {record.header}")
        else:
            self.sequences[record.sequence] = record.header
        if underlying and "_CONTA" in record.header.split()[0]:
            self.issue("underlying names containing _CONTA", record.header)

    def warn(self):
        for kind, count in self.counts.items():
            print(f"\n{'!' * 78}\nWARNING: {self.label}: {count} {kind}.\n"
                  f"First {len(self.examples[kind])} examples:", file=sys.stderr)
            for example in self.examples[kind]:
                print(f"  {example}", file=sys.stderr)
            print("!" * 78, file=sys.stderr)


def add_contaminants(fasta, contaminants, destination, deduplicate=False):
    """Preserve all records by default, including identical sequences.

    Optional deduplication keeps contaminant records on ID or sequence matches;
    within each source, the first retained record wins. Diagnostics cover all
    input records, including records removed by deduplication.
    """
    fasta, contaminants, destination = map(Path, (fasta, contaminants, destination))
    if destination.resolve() in (fasta.resolve(), contaminants.resolve()):
        raise ValueError("Merge destination must differ from both input files")
    contaminant_records = list(records(contaminants))
    contaminant_audit = Audit(f"contaminants {contaminants}")
    kept_contaminants = []
    ids, sequences = set(), set()
    for record in contaminant_records:
        contaminant_audit.add(record)
        if not deduplicate or (record.accession not in ids and record.sequence not in sequences):
            kept_contaminants.append(record)
            ids.add(record.accession)
            sequences.add(record.sequence)
    contaminant_audit.warn()

    underlying_audit = Audit(f"underlying FASTA {fasta}")
    cross_audit = Audit(f"overlap between {fasta} and {contaminants}"
                        + ("; contaminants take priority" if deduplicate else "; all records retained"))
    written = removed = 0
    # Include all contaminant records in collision diagnostics, even discarded ones.
    contaminant_ids = contaminant_audit.ids
    contaminant_sequences = contaminant_audit.sequences
    with destination.open("w") as out:
        for record in records(fasta):
            underlying_audit.add(record, underlying=True)
            if record.accession in contaminant_ids:
                header, sequence = contaminant_ids[record.accession]
                equality = "same sequence" if sequence == record.sequence else "DIFFERENT SEQUENCES"
                cross_audit.issue("duplicate accessions", f"{header}\n    {record.header} [{equality}]")
            if record.sequence in contaminant_sequences:
                cross_audit.issue("duplicate sequences (including different headers)",
                                  f"{contaminant_sequences[record.sequence]}\n    {record.header}")
            if deduplicate and (record.accession in ids or record.sequence in sequences):
                removed += 1
                continue
            out.write(record.text if record.text.endswith("\n") else record.text + "\n")
            ids.add(record.accession)
            sequences.add(record.sequence)
            written += 1
        for record in kept_contaminants:
            out.write(record.text if record.text.endswith("\n") else record.text + "\n")
            written += 1
    underlying_audit.warn()
    cross_audit.warn()
    removed += len(contaminant_records) - len(kept_contaminants)
    print(f"{destination}: wrote {written:,} records; removed {removed:,} duplicates", file=sys.stderr)
    return written, removed
