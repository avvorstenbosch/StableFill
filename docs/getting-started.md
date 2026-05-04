Getting Started
===============

StableFill updates LaTeX, LyX, and Markdown documents from plain text result
files. Put tables in labeled `<Tab:...>` blocks, put one-off values in
`<Val:...>` or `<Value:...>` blocks, and run one command to create the filled
document.

Installation
------------

Recommended for command-line use:

```bash
uv tool install "git+https://github.com/avvorstenbosch/StableFill"
```

Alternative with pip:

```bash
python -m pip install "git+https://github.com/avvorstenbosch/StableFill"
```

Run StableFill with either command name:

```bash
stablefill -i results.txt -o paper_filled.tex paper_template.tex
tablefill  -i results.txt -o paper_filled.tex paper_template.tex
```

The Python distribution is named `stablefill`. The old `tablefill` command and
`from tablefill import tablefill` import remain as compatibility aliases.

For development:

```bash
git clone https://github.com/avvorstenbosch/StableFill
cd StableFill
uv run --extra test python -m pytest -q
uv run --extra docs mkdocs build --strict
```

The Basic Workflow
------------------

Create an input file called `results.txt`:

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

Create a LaTeX template called `paper_template.tex`:

```latex
\documentclass{article}
\begin{document}
The final sample contains {{val:sample_size|,.0f}} observations.
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

Fill the template:

```bash
stablefill -i results.txt -o paper_filled.tex paper_template.tex
```

The relevant filled content is:

```latex
The final sample contains 48,210 observations.
Mean income is 57,890.2.

Treatment & 0.125*** & -0.456 & 0.789** \\
          & (0.031) & (0.100) & (0.222) \\
Controls  & Yes & No & Yes \\
N         & 48,210 & 48,210 & 48,210 \\
```

Inline Values For Paragraphs
----------------------------

Paragraph values do not need start/end markers. Add a named value to your input
file:

```text
<Val:population>
5708

<Value:p_value>
0.024
```

Then reference it anywhere in your TeX, LyX, or Markdown template:

```latex
The study population contains {{val:population|,.0f}} people.
The result is significant{{val:p_value|*}}.
```

`val:` is an optional prefix inside the placeholder. These are equivalent:

```latex
{{val:population|,.0f}}
{{population|,.0f}}
```

Use `val:` when you want prose placeholders to stand out clearly from normal
text.

Preview Values While Drafting
-----------------------------

When you want to see the values without replacing the placeholders yet, create
an annotated copy:

```bash
stablefill --annotate -i results.txt -o paper_annotated.tex paper_template.tex
```

StableFill keeps each placeholder and writes a compact `[[SF: ...]]` preview
beside it:

```latex
The final sample contains {{val:sample_size|,.0f}}[[SF: 48,210]] observations.
N         & #0,#[[SF: 48,210]] & #0,#[[SF: 48,210]] & #0,#[[SF: 48,210]] \\
```

Run the annotation command again to refresh existing previews after the input
file changes. A normal fill removes adjacent annotations while replacing the
placeholders:

```bash
stablefill -i results.txt -o paper_filled.tex paper_annotated.tex
```

To clean annotations from a template without filling anything, use:

```bash
stablefill --remove-annotations -o paper_clean.tex paper_annotated.tex
```

Annotated LaTeX files are intended for review and may not compile. Filled files
do not keep `[[SF: ...]]` annotations.

Placeholder Formats
-------------------

Placeholder        | Meaning
------------------ | -------
`###`              | Insert the next table value as written.
`#0,#`             | Round to zero decimals and add thousands separators.
`#2#`              | Round to two decimals.
`#*#`              | Convert a p-value to significance stars.
`#{:.2f}#`         | Use Python format syntax.
`{{val:name}}`     | Insert a named inline value.
`{{val:name\|,.0f}}` | Insert a formatted named inline value.

Tables
------

Tables are matched by label. This template:

```latex
\begin{table}
\caption{Regression output}
\label{tab:regression}
...
\end{table}
```

uses this input block:

```text
<Tab:regression>
...
```

Within a table, StableFill fills placeholders in document order: top to bottom,
then left to right within each line. It does not require every table row to have
the same number of placeholders.

In LaTeX, a fillable table is a `\begin{table}` or `\begin{subtable}` region
with a `\label{tab:name}` inside it. StableFill only fills sequential table
placeholders inside matched table regions. A table that already contains final
values and no placeholders is left unchanged and does not produce a
missing-input warning.

Economics Regression Tables
---------------------------

StableFill supports both common standard-error layouts.

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

Standard errors beside estimates:

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

Ragged Tables
-------------

Uneven placeholder layouts are valid. For example:

```text
<Tab:ragged>
101 202
A1 A2 A3 A4
B1 B2 B3 B4
```

```latex
\label{tab:ragged}
\multicolumn{3}{l}{Header A: #0,#} & \multicolumn{2}{r}{Header B: #0,#} \\
Row A & ### & ### & ### & ### \\
Row B & ### & ### & ### & ### \\
```

fills as:

```latex
\multicolumn{3}{l}{Header A: 101} & \multicolumn{2}{r}{Header B: 202} \\
Row A & A1 & A2 & A3 & A4 \\
Row B & B1 & B2 & B3 & B4 \\
```

Python API
----------

You can also call StableFill from Python:

```python
from stablefill import stablefill

status, message = stablefill(
    input="results.txt",
    template="paper_template.tex",
    output="paper_filled.tex",
)
```

The historical `from tablefill import tablefill` import remains available as a
compatibility alias.

More Examples
-------------

- [Matrix Input](usage/02matrix-input.md)
- [Placeholders](usage/03placeholders.md)
- [Inline Values](usage/07-inline-values.md)
- [LaTeX Economics Tables](usage/08-latex-economics.md)
- [Diagnostics and Testing](usage/09-diagnostics-testing.md)
- [Annotation Mode](usage/10-annotations.md)
