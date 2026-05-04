StableFill
==========

StableFill updates LaTeX, LyX, and Markdown documents from plain text result
files. It fills labeled tables and named inline values, so papers can be
regenerated after analysis changes without manually editing reported numbers.

Status
------

This is a fork of the original `tablefill` project. The package has recently
been modernized and partially refactored with help from OpenAI Codex, but it
has not been thoroughly verified in production workflows. Use with caution,
review filled documents carefully, and keep template/input files under version
control.

Quickstart
----------

Install from the repository into an isolated command-line tool environment:

```bash
uv tool install "git+https://github.com/avvorstenbosch/StableFill"
```

Or install with pip:

```bash
python -m pip install "git+https://github.com/avvorstenbosch/StableFill"
```

Run StableFill:

```bash
stablefill -i results.txt -o paper_filled.tex paper_template.tex
```

The historical command name is still available:

```bash
tablefill -i results.txt -o paper_filled.tex paper_template.tex
```

The Python distribution is named `stablefill`. The old `tablefill` command and
`from tablefill import tablefill` import remain as compatibility aliases.

Development
-----------

Clone the repository and run the tests with `uv`:

```bash
git clone https://github.com/avvorstenbosch/StableFill
cd StableFill
uv run --extra test python -m pytest -q
```

Build the documentation locally:

```bash
uv run --extra docs mkdocs build --strict
```

Build the distribution artifacts:

```bash
uv run --extra dev python -m build
```

Normal StableFill table filling has no required runtime dependencies. Install the optional
NumPy extra only if you use XML tables with NumPy syntax:

```bash
python -m pip install "git+https://github.com/avvorstenbosch/StableFill[numpy]"
```

Basic Usage
-----------

Create an input file:

```text
<Val:sample_size>
48210

<Value:mean_income>
57890.25

<Tab:regression>
0.125*** -0.456 0.789**
(0.031) (0.100) (0.222)
Yes No Yes
48210 48210 48210
```

Create a template:

```latex
\documentclass{article}
\begin{document}
The sample includes {{val:sample_size|,.0f}} observations.
Mean income is {{mean_income|,.1f}}.

\begin{table}
\caption{Regression output}
\label{tab:regression}
\begin{tabular}{lccc}
Treatment & ### & ### & ### \\
          & ### & ### & ### \\
Controls  & ### & ### & ### \\
N         & #0,# & #0,# & #0,# \\
\end{tabular}
\end{table}
\end{document}
```

Fill it:

```bash
stablefill -i results.txt -o paper_filled.tex paper_template.tex
```

Input Directories
-----------------

Instead of maintaining one large input file, you can point StableFill at a
directory of result files:

```bash
stablefill --input-dir results/tables -o paper_filled.tex paper_template.tex
```

StableFill reads all `.txt` files in that directory in sorted filename order.
Files with other extensions are ignored, and parsing errors still report the
original file and line number.

If you do not pass `--input` or `--input-dir`, StableFill looks for a `tables`
directory next to the template:

```text
paper_template.tex
tables/
  01-values.txt
  02-regressions.txt
```

With that layout, this is enough:

```bash
stablefill -o paper_filled.tex paper_template.tex
```

Inline Values
-------------

For prose, captions, notes, and other non-table text, use named inline
placeholders anywhere in the file:

```latex
The final sample contains {{val:sample_size|,.0f}} observations.
The mean income is {{mean_income|,.1f}}.
```

Those placeholders match `<Val:...>` or `<Value:...>` blocks in the input file.
The `val:` prefix in the template is optional, but it is useful because it makes
inline values visibly different from ordinary prose.

Annotation Mode
---------------

When drafting, you can ask StableFill to keep placeholders in place and add a
compact preview annotation with the value that would be filled:

```bash
stablefill --annotate -i results.txt -o paper_annotated.tex paper_template.tex
```

This writes annotations such as `[[SF: 48,210]]` immediately after inline and
table placeholders:

```latex
The sample includes {{val:sample_size|,.0f}}[[SF: 48,210]] observations.
N & #0,#[[SF: 48,210]] \\
```

Running `--annotate` again updates existing `[[SF: ...]]` annotations instead
of adding duplicates. A normal fill consumes the placeholder and any adjacent
annotation, so the filled document remains clean and should compile when the
template itself is valid:

```bash
stablefill -i results.txt -o paper_filled.tex paper_annotated.tex
```

To remove annotations without filling anything, use:

```bash
stablefill --remove-annotations -o paper_clean.tex paper_annotated.tex
```

Annotated LaTeX files are meant for review and may not compile because
`[[SF: ...]]` is visible text inserted inside placeholders.

Tables
------

Tables are matched by label. A LaTeX table with `\label{tab:regression}` uses
the `<Tab:regression>` block from the input file. Placeholders are filled in
document order: top to bottom, left to right.

For LaTeX, a fillable table is a `\begin{table}` or `\begin{subtable}` region
with a `\label{tab:name}` inside it. StableFill only fills sequential table
placeholders inside matched table regions. Tables with no placeholders are left
unchanged and do not produce missing-input warnings, even if their label looks
like `tab:name`.

Common placeholders:

Placeholder      | Meaning
---------------- | -------
`###`            | Insert the value as written.
`#0,#`           | Round to zero decimals and add thousands separators.
`#2#`            | Round to two decimals.
`#*#`            | Convert a p-value to significance stars.
`#{:.2f}#`       | Use Python format syntax.
`{{val:name}}`   | Insert a named inline value.
`{{val:name\|,.0f}}` | Insert a formatted named inline value.

Economics Tables
----------------

StableFill supports the two common regression-table layouts.

Standard errors below estimates:

```text
<Tab:se_below>
0.125*** -0.456 0.789**
(0.031) (0.100) (0.222)
```

```latex
Treatment & ### & ### & ### \\
          & ### & ### & ### \\
```

Standard errors beside estimates are treated as one logical cell:

```text
<Tab:inline_se>
0.125*** (0.031) -0.456 (0.100) 0.789** (0.222)
```

```latex
Treatment & ### & ### & ### \\
```

This fills as:

```latex
Treatment & 0.125*** (0.031) & -0.456 (0.100) & 0.789** (0.222) \\
```

Uneven table layouts are also supported. A header row can contain two
placeholders while the body contains four placeholders per row; values are read
in the order the placeholders appear.

Diagnostics
-----------

StableFill now reports expected parse and placeholder failures with structured
context. Error messages include the template or input file, line number, table
tag, entry index, placeholder text, and nearby source line when those details
are available. This is especially useful when a numeric placeholder receives
text, a row appears before any `<Tab:...>` label, or a table has too few input
values.

The test suite includes a complex LaTeX integration fixture with ragged tables,
economics outputs, inline values, already-filled tables, comments, ampersands,
and false-positive guards. When `xelatex` and `pdfinfo` are installed, the test
also compiles the filled document and checks that the PDF is four or five pages.

Documentation
-------------

- [Getting Started](https://avvorstenbosch.github.io/StableFill/getting-started.html)
- [Matrix Input](https://avvorstenbosch.github.io/StableFill/usage/02matrix-input.html)
- [Placeholders](https://avvorstenbosch.github.io/StableFill/usage/03placeholders.html)
- [Inline Values](https://avvorstenbosch.github.io/StableFill/usage/07-inline-values.html)
- [LaTeX Economics Tables](https://avvorstenbosch.github.io/StableFill/usage/08-latex-economics.html)
- [Diagnostics and Testing](https://avvorstenbosch.github.io/StableFill/usage/09-diagnostics-testing.html)
- [Annotation Mode](https://avvorstenbosch.github.io/StableFill/usage/10-annotations.html)

Background
----------

This repository is a fork of Mauricio Caceres Bravo's
[`mcaceresb/tablefill`](https://github.com/mcaceresb/tablefill), which itself
builds on the original tablefill idea from
[GSLab](https://github.com/gslab-econ/gslab_python). Credit for the original
project, workflow, and much of the existing implementation belongs to those
authors and contributors.

This fork keeps the original table-oriented workflow while adding modern
Python packaging, clearer errors, robust whitespace parsing, inline values for
prose, and economics-focused regression table handling. The modernization work
was performed with assistance from OpenAI Codex.

License
-------

MIT
