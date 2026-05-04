import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stablefill import stablefill
from tablefill import tablefill
from tablefill.placeholders import PlaceholderPatterns
from tablefill.template_scanner import TemplateScanner, grammar_for_filetype

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class TestModernFeatures(unittest.TestCase):

    def write_file(self, directory, name, contents):
        filename = os.path.join(directory, name)
        with open(filename, 'w') as handle:
            handle.write(textwrap.dedent(contents).lstrip())
        return filename

    def test_stablefill_import_and_legacy_alias_match(self):
        self.assertIs(stablefill, tablefill)

    def test_inline_value_placeholders_fill_anywhere(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'values.txt', """
                <Val:population>
                5708
                <Value:mean_age>
                42.35
                <Value:p_value>
                0.024
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                The sample includes {{val:population|,.0f}} people.
                Mean age is {{mean_age|.1f}}.
                The key coefficient is significant{{p_value|*}}.
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('5,708 people', filled)
            self.assertIn('Mean age is 42.4.', filled)
            self.assertIn('significant**.', filled)

    def test_whitespace_regression_rows_with_standard_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:regression>
                0.125*** 0.456
                (0.031) (0.100)
                Yes No
                1200 1300
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \caption{Regression output}
                \label{tab:regression}
                \begin{tabular}{lcc}
                Treatment & ### & ### \\
                          & ### & ### \\
                Controls  & ### & ### \\
                N         & #0,# & #0,# \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('Treatment & 0.125*** & 0.456', filled)
            self.assertIn('& (0.031) & (0.100)', filled)
            self.assertIn('Controls  & Yes & No', filled)
            self.assertIn('N         & 1,200 & 1,300', filled)

    def test_adjacent_standard_errors_fill_as_one_cell(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:inline_se>
                0.125*** (0.031) -0.456 (0.100) 0.789 (0.222)
                Yes No Yes
                1200 1300 1400
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \caption{Inline standard errors}
                \label{tab:inline_se}
                \begin{tabular}{lccc}
                Treatment & ### & ### & ### \\
                Controls  & ### & ### & ### \\
                N         & #0,# & #0,# & #0,# \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('Treatment & 0.125*** (0.031) & -0.456 (0.100) & 0.789 (0.222)', filled)
            self.assertIn('Controls  & Yes & No & Yes', filled)
            self.assertIn('N         & 1,200 & 1,300 & 1,400', filled)

    def test_ragged_placeholder_layouts_fill_in_document_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:ragged>
                101 202
                A1 A2 A3 A4
                B1 B2 B3 B4
                C1 C2 C3 C4
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \caption{Ragged placeholder layout}
                \label{tab:ragged}
                \begin{tabular}{lcccc}
                \multicolumn{3}{l}{Header A: #0,#} & \multicolumn{2}{r}{Header B: #0,#} \\
                Row A & ### & ### & ### & ### \\
                Row B & ### & ### & ### & ### \\
                Row C & ### & ### & ### & ### \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('Header A: 101', filled)
            self.assertIn('Header B: 202', filled)
            self.assertIn('Row A & A1 & A2 & A3 & A4', filled)
            self.assertIn('Row B & B1 & B2 & B3 & B4', filled)
            self.assertIn('Row C & C1 & C2 & C3 & C4', filled)

    def test_cli_complicated_economics_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Value:sample_size>
                48210

                <Value:mean_income>
                57890.25

                <Tab:se_below>
                0.125*** -0.456 0.789**
                (0.031) (0.100) (0.222)
                Yes No Yes
                48210 48210 48210

                <Tab:inline_se>
                0.125*** (0.031) -0.456 (0.100) 0.789** (0.222)
                Yes No Yes
                48210 48210 48210

                <Tab:ragged>
                101 202
                A1 A2 A3 A4
                B1 B2 B3 B4
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                The analysis uses {{sample_size|,.0f}} observations.
                Mean income is {{mean_income|,.1f}}.

                \begin{table}
                \caption{Standard errors below estimates}
                \label{tab:se_below}
                \begin{tabular}{lccc}
                Treatment & ### & ### & ### \\
                          & ### & ### & ### \\
                Controls  & ### & ### & ### \\
                N         & #0,# & #0,# & #0,# \\
                \end{tabular}
                \end{table}

                \begin{table}
                \caption{Standard errors beside estimates}
                \label{tab:inline_se}
                \begin{tabular}{lccc}
                Treatment & ### & ### & ### \\
                Controls  & ### & ### & ### \\
                N         & #0,# & #0,# & #0,# \\
                \end{tabular}
                \end{table}

                \begin{table}
                \caption{Ragged multicolumn header}
                \label{tab:ragged}
                \begin{tabular}{lcccc}
                \multicolumn{3}{l}{Header A: #0,#} & \multicolumn{2}{r}{Header B: #0,#} \\
                Row A & ### & ### & ### & ### \\
                Row B & ### & ### & ### & ### \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            result = subprocess.run([sys.executable,
                                     '-m',
                                     'stablefill',
                                     '--silent',
                                     '--no-header',
                                     '-i',
                                     input_file,
                                     '-o',
                                     output,
                                     template],
                                    cwd=ROOT_DIR,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('48,210 observations', filled)
            self.assertIn('Mean income is 57,890.2', filled)
            self.assertIn('Treatment & 0.125*** & -0.456 & 0.789**', filled)
            self.assertIn('& (0.031) & (0.100) & (0.222)', filled)
            self.assertIn('Treatment & 0.125*** (0.031) & -0.456 (0.100) & 0.789** (0.222)', filled)
            self.assertIn('Header A: 101', filled)
            self.assertIn('Row B & B1 & B2 & B3 & B4', filled)

            if shutil.which('xelatex'):
                subprocess.run([shutil.which('xelatex'),
                                '-interaction=nonstopmode',
                                '-halt-on-error',
                                os.path.basename(output)],
                               cwd=tmpdir,
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
                self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'filled.pdf')))

    def test_input_rows_before_a_label_report_file_and_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'broken.txt', """
                1 2 3
                <Tab:example>
                4 5 6
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                Nothing to fill.
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('ERROR', status)
            self.assertIn('InputParseError', msg)
            self.assertIn('broken.txt', msg)
            self.assertIn(':1', msg)
            self.assertIn('location=', msg)
            self.assertIn("context='1 2 3'", msg)

    def test_template_scanner_classifies_tex_grammar(self):
        scanner = TemplateScanner(grammar_for_filetype('tex'))
        patterns = PlaceholderPatterns()

        self.assertTrue(scanner.is_table_start(r'\begin{table}'))
        self.assertTrue(scanner.is_table_end(r'\end{table}'))
        self.assertTrue(scanner.is_comment('% ### remains a comment'))
        self.assertEqual('summary', scanner.extract_label(r'\label{tab:summary}'))
        self.assertTrue(scanner.has_placeholder('Value & #0,# \\', patterns.active_patterns()))
        self.assertFalse(scanner.has_placeholder(r'Price \#1 is ordinary text', patterns.active_patterns()))

    def test_numeric_placeholder_error_reports_structured_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:broken_numeric>
                not-a-number
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \label{tab:broken_numeric}
                \begin{tabular}{lr}
                Bad value & #0,# \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('ERROR', status)
            self.assertIn('PLACEHOLDER_ERROR', msg)
            self.assertIn('template.tex', msg)
            self.assertIn('table=broken_numeric', msg)
            self.assertIn('entry=1', msg)
            self.assertIn("placeholder='#0,#'", msg)
            self.assertIn('not-a-number', msg)

    def test_unmatched_already_filled_table_does_not_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:other_table>
                1 2 3
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \caption{Already final}
                \label{tab:already_final}
                \begin{tabular}{lr}
                Group & Estimate \\
                A & 1.25 \\
                B & 2.50 \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            self.assertNotIn('NO MATCHES', msg)
            with open(output, 'r') as handle:
                filled = handle.read()
            self.assertIn('A & 1.25', filled)
            self.assertIn(r'\label{tab:already_final}', filled)

    def test_unmatched_table_with_placeholders_still_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Tab:other_table>
                1 2 3
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                \begin{table}
                \caption{Needs input}
                \label{tab:missing_input}
                \begin{tabular}{lr}
                Value & #0,# \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('WARNING', status)
            self.assertIn('missing_input', msg)
            self.assertIn("not in 'input' file", msg)

    @unittest.skipUnless(shutil.which('xelatex'), 'xelatex is not installed')
    def test_latex_economics_example_compiles_to_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = self.write_file(tmpdir, 'tables.txt', """
                <Value:sample_size>
                2600

                <Tab:regression>
                0.125*** 0.456
                (0.031) (0.100)
                Yes No
                1200 1300
            """)
            template = self.write_file(tmpdir, 'template.tex', r"""
                \documentclass{article}
                \begin{document}
                This specification uses {{sample_size|,.0f}} observations.

                \begin{table}
                \caption{Regression output}
                \label{tab:regression}
                \begin{tabular}{lcc}
                Treatment & ### & ### \\
                          & ### & ### \\
                Controls  & ### & ### \\
                N         & #0,# & #0,# \\
                \end{tabular}
                \end{table}
                \end{document}
            """)
            output = os.path.join(tmpdir, 'filled.tex')

            status, msg = tablefill(input=input_file,
                                    template=template,
                                    output=output,
                                    filetype='tex',
                                    nohead=True,
                                    silent=True)

            self.assertEqual('SUCCESS', status, msg)
            subprocess.run([shutil.which('xelatex'),
                            '-interaction=nonstopmode',
                            '-halt-on-error',
                            os.path.basename(output)],
                           cwd=tmpdir,
                           check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'filled.pdf')))


if __name__ == '__main__':
    unittest.main()
