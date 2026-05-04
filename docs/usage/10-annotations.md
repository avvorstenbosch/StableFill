Annotation Mode
===============

Annotation mode helps while drafting a paper. It leaves placeholders in the
template and writes a compact `[[SF: ...]]` preview containing the value that
StableFill would insert during a normal fill.

Annotate A Template
-------------------

```bash
stablefill --annotate -i results.txt -o paper_annotated.tex paper_template.tex
```

For example, this template:

```latex
The sample includes {{val:sample_size|,.0f}} observations.

\begin{table}
\label{tab:regression}
\begin{tabular}{lcc}
Treatment & ### & ### \\
N         & #0,# & #0,# \\
\end{tabular}
\end{table}
```

can become:

```latex
The sample includes {{val:sample_size|,.0f}}[[SF: 48,210]] observations.

\begin{table}
\label{tab:regression}
\begin{tabular}{lcc}
Treatment & ###[[SF: 0.125*** (0.031)]] & ###[[SF: -0.456 (0.100)]] \\
N         & #0,#[[SF: 48,210]] & #0,#[[SF: 48,210]] \\
\end{tabular}
\end{table}
```

The annotation prefix is intentionally short: `SF` stands for StableFill.

Refresh Existing Annotations
----------------------------

Running annotation mode on an already annotated file updates the existing
`[[SF: ...]]` text instead of appending another annotation:

```bash
stablefill --annotate -i updated_results.txt -o paper_annotated_new.tex paper_annotated.tex
```

Fill An Annotated Template
--------------------------

Normal filling consumes the placeholder and any adjacent annotation:

```bash
stablefill -i results.txt -o paper_filled.tex paper_annotated.tex
```

This produces normal output such as:

```latex
The sample includes 48,210 observations.
Treatment & 0.125*** (0.031) & -0.456 (0.100) \\
N         & 48,210 & 48,210 \\
```

Remove Annotations Only
-----------------------

Use `--remove-annotations` when you want to clean a template without filling
the placeholders. This mode does not require an input file:

```bash
stablefill --remove-annotations -o paper_clean.tex paper_annotated.tex
```

Notes
-----

Annotated LaTeX files are review files and may not compile because the
`[[SF: ...]]` text is inserted directly into the source. Files produced by
normal filling do not keep annotations and should compile when the template and
filled values are valid LaTeX.
