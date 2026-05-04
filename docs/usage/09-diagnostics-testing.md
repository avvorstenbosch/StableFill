Diagnostics and Testing
=======================

StableFill tries to keep legacy warning behavior for ordinary fills, but
expected failures now include structured diagnostic context. When available,
errors report:

- the input or template file
- the line and column
- the table tag
- the input entry index
- the placeholder text
- the nearby source line

This is useful when a table has too few values, a numeric placeholder receives
text, or an input row appears before any `<Tab:...>` or `<Val:...>` label.

Example
-------

If this input is used:

```text
<Tab:broken_numeric>
not-a-number
```

with this template:

```latex
\begin{table}
\label{tab:broken_numeric}
\begin{tabular}{lr}
Bad value & #0,# \\
\end{tabular}
\end{table}
```

StableFill returns an error that includes the placeholder and table context:

```text
[PLACEHOLDER_ERROR] Could not fill template placeholder.
Details: location=.../template.tex:6; table=broken_numeric; entry=1;
placeholder='#0,#'; context='Bad value & #0,# \\'
```

The full traceback is still returned by the Python API and command-line
wrapper, so advanced users can inspect the original exception as well.

What Gets Filled
----------------

The template scanner uses an explicit grammar for each supported file type.
For LaTeX, a fillable table is:

- a `\begin{table}` or `\begin{subtable}` region
- with a `\label{tab:name}` inside it
- where `name` matches an input `<Tab:name>` block
- containing sequential placeholders such as `###`, `#0,#`, or `#*#`

Sequential table placeholders are ignored in comments unless
`--fill-comments` is used. Tables with `tab:` labels but no placeholders are
treated as already-filled content: they are left unchanged and do not produce
missing-input warnings.

Inline placeholders such as `{{val:sample_size}}` are independent of table
regions and can appear in prose, captions, notes, or table text.

Complex LaTeX Fixture
---------------------

The repository contains a long integration fixture in
`test/input/complex_latex/`. It includes:

- multiple ragged tables
- economics regression tables with standard errors below estimates
- economics regression tables with standard errors beside estimates
- inline values in prose
- already-filled tables that should remain unchanged
- comments containing placeholder-looking text
- ampersands and percent signs in replacement values
- false-positive guards such as `AT\&T`, `R\&D`, `Price \#1`, and escaped braces

Run the full suite with:

```bash
uv run --extra test python -m pytest -q
```

When `xelatex` is installed, the complex fixture is filled from the command
line and compiled to PDF. When `pdfinfo` is also installed, the test verifies
that the rendered PDF is four or five pages.
