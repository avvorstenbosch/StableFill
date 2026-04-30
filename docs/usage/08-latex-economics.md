LaTeX Economics Tables
======================

Regression tables often alternate coefficients and standard errors. StableFill
supports both common layouts:

- Standard errors below estimates, where `0.125` and `(0.031)` occupy separate
  placeholders on separate rows.
- Standard errors beside estimates, where `0.125*** (0.031)` is treated as one
  logical cell and fills one placeholder/model column.

The input parser accepts whitespace-delimited rows in addition to tab-delimited
rows, so this runnable example is valid:

```text
<Val:sample_size>
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
```

The same files are available as
[`input.txt`](08economics/input.txt),
[`template.tex`](08economics/template.tex), and
[`filled.tex`](08economics/filled.tex).

The LaTeX template can be filled directly:

```latex
\documentclass{article}
\begin{document}
This specification uses {{val:sample_size|,.0f}} observations.
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
```

Running:

```bash
tablefill -i tables.txt -o filled.tex template.tex
```

produces:

- `Treatment & 0.125*** & -0.456 & 0.789**` with standard errors on the next row.
- `Treatment & 0.125*** (0.031) & -0.456 (0.100) & 0.789** (0.222)` when the standard error is beside the estimate.
- Ragged headers where two header placeholders are followed by body rows with four placeholders.
