import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from fasta_merge import add_contaminants, records


class MergeTests(unittest.TestCase):
    def merge(self, base, contaminants, deduplicate=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fasta, conta, output = [root / name for name in ('base.fa', 'conta.fa', 'out.fa')]
            fasta.write_text(base)
            conta.write_text(contaminants)
            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                counts = add_contaminants(fasta, conta, output, deduplicate)
            return list(records(output)), warning.getvalue(), counts

    def test_contaminants_win_by_accession_and_sequence(self):
        result, warning, counts = self.merge(
            '>sp|A|HUMAN\nAAA\n>sp|B|OTHER\nCCC\n>sp|C|KEEP\nDDD',
            '>sp|A|HUMAN_CONTA\nBBB\n>sp|D|OTHER_CONTA\nC\nCC')
        self.assertEqual([r.accession for r in result], ['C', 'A', 'D'])
        self.assertEqual(counts, (3, 2))
        self.assertIn('DIFFERENT SEQUENCES', warning)
        self.assertIn('duplicate sequences (including different headers)', warning)
        self.assertIn('sp|B|OTHER', warning)
        self.assertIn('sp|D|OTHER_CONTA', warning)

    def test_internal_duplicates_and_existing_contaminant_names(self):
        result, warning, counts = self.merge(
            '>sp|A|OLD_CONTA\nAAA\n>sp|A|OTHER\nBBB\n>sp|B|ALIAS\nAAA\n',
            '>sp|C|NEW_CONTA\nCCC\n>sp|C|NEW_CONTA\nCCC\n>sp|D|ALIAS_CONTA\nCCC\n')
        self.assertEqual([r.accession for r in result], ['A', 'C'])
        self.assertEqual(counts, (2, 4))
        self.assertIn('underlying names containing _CONTA', warning)
        self.assertIn('underlying FASTA', warning)
        self.assertIn('contaminants', warning)
        self.assertIn('duplicate accessions', warning)

    def test_opt_out_retains_records_and_warnings(self):
        result, warning, counts = self.merge('>A\nAAA\n>A\nAAA\n', '>A\nAAA\n', False)
        self.assertEqual(len(result), 3)
        self.assertEqual(counts, (3, 0))
        self.assertIn('WARNING:', warning)

    def test_warning_examples_limited_to_ten(self):
        base = ''.join(f'>sp|A|H{i}\nAAA\n' for i in range(16))
        result, warning, counts = self.merge(base, '>C\nCCC\n')
        self.assertIn('15 duplicate accessions', warning)
        self.assertIn('First 10 examples:', warning)
        self.assertIn('sp|A|H10', warning)
        self.assertNotIn('sp|A|H11', warning)
        self.assertEqual(counts, (2, 15))

    def test_different_residues_preserved(self):
        result, warning, counts = self.merge('>A\nILI\n', '>C\nLLL\n')
        self.assertEqual(counts, (2, 0))
        self.assertNotIn('WARNING:', warning)

    def test_default_retains_human_and_prefixed_contaminant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base, conta, output = [root / name for name in ('base.fa', 'conta.fa', 'out.fa')]
            base.write_text('>sp|P02538|K2C6A_HUMAN\nAAA\n')
            conta.write_text('>sp|Cont_P02538|K2C6A_HUMAN\nAAA\n')
            with contextlib.redirect_stderr(io.StringIO()):
                counts = add_contaminants(base, conta, output)
            self.assertEqual(counts, (2, 0))
            self.assertEqual([r.accession for r in records(output)], ['P02538', 'Cont_P02538'])

    def test_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'base.fa'
            source.write_text('>A\nAAA\n')
            with self.assertRaises(ValueError):
                add_contaminants(source, source, source)
            self.assertEqual(source.read_text(), '>A\nAAA\n')


if __name__ == '__main__':
    unittest.main()
