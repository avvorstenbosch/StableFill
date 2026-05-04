import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FIXTURE_DIR = os.path.join(ROOT_DIR, 'test', 'input', 'complex_latex')


class TestComplexLatexDocument(unittest.TestCase):

    def fill_fixture(self, tmpdir):
        template = os.path.join(FIXTURE_DIR, 'template.tex')
        tables = os.path.join(FIXTURE_DIR, 'tables.txt')
        output = os.path.join(tmpdir, 'stablefill_complex_filled.tex')
        result = subprocess.run([sys.executable,
                                 '-m',
                                 'tablefill',
                                 '--silent',
                                 '--no-header',
                                 '-i',
                                 tables,
                                 '-o',
                                 output,
                                 template],
                                cwd=ROOT_DIR,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return output

    def test_complex_latex_fixture_fills_from_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self.fill_fixture(tmpdir)
            with open(output, 'r') as handle:
                filled = handle.read()

            self.assertIn('48,210 observations', filled)
            self.assertIn('represents 1,250,000 people', filled)
            self.assertIn('73.4\\%, and the headline p-value', filled)
            self.assertIn('headline p-value is significant**', filled)
            self.assertIn('All workers & 48,210 & 73.4\\% & 57,890 & A\\&B cohorts', filled)
            self.assertIn('Urban & 31,250 & 68.1\\% & 62,500 & Metro \\& suburban', filled)
            self.assertIn('Treatment & 0.1254*** & -0.0456 & 0.2100** & -0.3333***', filled)
            self.assertIn('Treatment & 0.125*** (0.031) & -0.046 (0.100) & 0.210** (0.080)', filled)
            self.assertIn('Manufacturing & East \\& coastal & 1.23 & West corridor & 2.35 & 1,200', filled)
            self.assertIn('Year -1 & \\multicolumn{5}{l}{Reference period: omitted}', filled)
            self.assertIn('Year 1 & 0.14 & 0.04 & 3.25 & *** & Robust \\& persistent', filled)
            self.assertIn('North & 11.2 & 1.4', filled)
            self.assertNotIn('unused tokens should not appear', filled)
            self.assertIn('AT\\&T, R\\&D, A \\& B Markets', filled)
            self.assertIn('% This comment contains ### and #0,# but should not be filled.', filled)
            self.assertIn('Escaping & R\\&D Unit & 80\\% Complete', filled)
            self.assertIn('Ampersand escaping & A\\&B & OK', filled)

    @unittest.skipUnless(shutil.which('xelatex'), 'xelatex is not installed')
    def test_complex_latex_fixture_compiles_to_four_or_five_pages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self.fill_fixture(tmpdir)
            xelatex = shutil.which('xelatex')
            compile_result = subprocess.run([xelatex,
                                             '-interaction=nonstopmode',
                                             '-halt-on-error',
                                             os.path.basename(output)],
                                            cwd=tmpdir,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
            self.assertEqual(0, compile_result.returncode,
                             compile_result.stdout + compile_result.stderr)

            pdf = os.path.join(tmpdir, 'stablefill_complex_filled.pdf')
            self.assertTrue(os.path.isfile(pdf))

            pdfinfo = shutil.which('pdfinfo')
            if pdfinfo:
                page_result = subprocess.run([pdfinfo, pdf],
                                             cwd=tmpdir,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             text=True)
                self.assertEqual(0, page_result.returncode,
                                 page_result.stdout + page_result.stderr)
                match = re.search(r'^Pages:\s+(\d+)$', page_result.stdout, re.MULTILINE)
                self.assertIsNotNone(match, page_result.stdout)
                pages = int(match.group(1))
                self.assertGreaterEqual(pages, 4)
                self.assertLessEqual(pages, 5)


if __name__ == '__main__':
    unittest.main()
