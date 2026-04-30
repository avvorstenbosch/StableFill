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
uv tool install "git+https://github.com/avvorstenbosch/tablefill"
```

Or install with pip:

```bash
python -m pip install "git+https://github.com/avvorstenbosch/tablefill"
```

Run StableFill:

```bash
stablefill -i results.txt -o paper_filled.tex paper_template.tex
```

The historical command name is still available:

```bash
tablefill -i results.txt -o paper_filled.tex paper_template.tex
```

Development
-----------

Clone the repository and run the tests with `uv`:

```bash
git clone https://github.com/avvorstenbosch/tablefill
cd tablefill
uv run --extra test python -m pytest -q
```

Normal table filling has no required runtime dependencies. Install the optional
NumPy extra only if you use XML tables with NumPy syntax:

```bash
python -m pip install "git+https://github.com/avvorstenbosch/tablefill[numpy]"
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

Tables
------

Tables are matched by label. A LaTeX table with `\label{tab:regression}` uses
the `<Tab:regression>` block from the input file. Placeholders are filled in
document order: top to bottom, left to right.

Common placeholders:

Placeholder      | Meaning
---------------- | -------
`###`            | Insert the value as written.
`#0,#`           | Round to zero decimals and add thousands separators.
`#2#`            | Round to two decimals.
`#*#`            | Convert a p-value to significance stars.
`#{:.2f}#`       | Use Python format syntax.
`{{val:name}}`   | Insert a named inline value.
`{{val:name|,.0f}}` | Insert a formatted named inline value.

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

Documentation
-------------

- [Getting Started](https://avvorstenbosch.github.io/tablefill/getting-started.html)
- [Matrix Input](https://avvorstenbosch.github.io/tablefill/usage/02matrix-input.html)
- [Placeholders](https://avvorstenbosch.github.io/tablefill/usage/03placeholders.html)
- [Inline Values](https://avvorstenbosch.github.io/tablefill/usage/07-inline-values.html)
- [LaTeX Economics Tables](https://avvorstenbosch.github.io/tablefill/usage/08-latex-economics.html)

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
