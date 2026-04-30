Placeholders
============

!!! info "Warning"
    This page is under construction

!!! note "Note"
    This section was adapted from the readme for the original tablefill.py

The template placeholders determine where the numbers from the input
files are and how they will be displayed. Every table in the template
file (if it is to be filled) must appear within a table environment.
There can be several tabular environments within the table environment,
but only ONE label per table environment.

While label names may appear more than once in both the template and
input files, only the last instance of the label in the input files will
be used. This because of the way the system is set up: The last label in
the input file should be the most up to date version of that table. In
the template file, repeated labels are filled with the same data.

By design, labels are NOT case-sensitive.

Placeholders
------------

The values in the template file are parsed as follows:

Placeholder  | Format
------------ | ------
`###`        | Replace as is; input can be text (all other placeholders require numbers).
`#\d+#`      | Round to `\d+` digits.
`#\d+,#`     | Round to `\d+` digits; add thousands comma separator.
`#*#`        | Interpret input as p-value and replce with a star corresponding so significance. Detault is `* 0.1, **0.05, ***0.01`.
`#\d+%#`     | Round to `\d+` digits; interpret as percentage.
`#|#|#`      | Get the absolute value of the number.
`#{.*}#`     | Arbitrary python format. Anything that `string.format()` will accept is allowed.

For named one-off statistics outside a sequential table, use the inline
syntax documented in [Inline Values](07-inline-values.md), for example
`{{val:sample_size|,.0f}}`.

Consider the following examples

```
abc       +  ###     = abc
2309.2093 +  ###     = 2309.2093
2309.2093 +  #4#     = 2309.2093
2309.2093 +  #5#     = 2309.20930
2309.2093 +  #20#    = 2309.20930000000000000000
2309.2093 +  #3#     = 2309.209
2309.2093 +  #2#     = 2309.21
2309.2093 +  #0#     = 2309
2309.2093 +  #0,#    = 2,309
-2.23e-2  +  #2#     = -0.0223      +  #2#   = -0.02
-2.23e+10 +  #7,#    = -22300000000 +  #7,#  = -22,300,000,000.000000
2309.2093 +  (#2#)   = (2309.21)
2309.2093 +  #2#**   = 2309.21**
2309.2093 +  ab#2#cd = ab2309.21cd
    .2093 +  #1%#    = 20.9
-2.23e-2  + |#7#|    = -0.0223      + |#7#|  =  0.0223000
    .1309 +  #*#     =
    .0639 +  #*#     = *
    .0139 +  #*#     = **
    .0013 +  #*#     = ***
```

Note that there can be ANYTHING around the pattern and the engine will
only match the pattern. Further, in LaTeX, the # character must be
escaped, so the engine also matches \#. Consider:

```
3234.43241 +   \\beta Hi \$(\#\#\#)\%*  = \\beta Hi \$(3234.43241)\%*
3234.43241 + & \\beta Hi \$(\##\#)\%*   = \\beta Hi \$(3234.43241)\%*
3234.43241 + & \\beta Hi \$(\#\##)\%*   = \\beta Hi \$(3234.43241)\%*
3234.43241 + & \\beta Hi \$(#\#\#)\%    = \\beta Hi \$(3234.43241)\%
3234.43241 + & \\beta Hi \$(\###)*\%    = \\beta Hi \$(3234.43241)*\%
3234.43241 + & \\beta Hi \$(\#0,\#)\%*  = \\beta Hi \$(3,234)\%*
3234.43241 + & \\beta Hi \$(\#0,\#)\%*  = \\beta Hi \$(3,234)\%*
3234.43241 + & \\beta Hi \$(\#0,#*      = \\beta Hi \$(3,234*
3234.43241 + & \\beta Hi \$(#0,\#*      = \\beta Hi \$(3,234*
3234.43241 + & \\beta Hi \$(\#0,#*      = \\beta Hi \$(3,234*
```

Matrices
--------

### Fill Order and Ragged Layouts

Tablefill fills placeholders in document order: top to bottom by template
line, and left to right within each line. It does not require every LaTeX row
to contain the same number of placeholders, and it does not infer a rectangular
shape from `&` column separators.

This means a header with two placeholders followed by body rows with four
placeholders each is valid as long as the input values are written in the same
order:

Input:

```
<tab:Ragged>
101 202
A1 A2 A3 A4
B1 B2 B3 B4
C1 C2 C3 C4
```

Template:

```latex
\label{tab:ragged}
\multicolumn{3}{l}{Header A: #0,#} & \multicolumn{2}{r}{Header B: #0,#} \\
Row A & ### & ### & ### & ### \\
Row B & ### & ### & ### & ### \\
Row C & ### & ### & ### & ### \\
```

Output:

```latex
\label{tab:ragged}
\multicolumn{3}{l}{Header A: 101} & \multicolumn{2}{r}{Header B: 202} \\
Row A & A1 & A2 & A3 & A4 \\
Row B & B1 & B2 & B3 & B4 \\
Row C & C1 & C2 & C3 & C4 \\
```

The main ambiguous case is intentional blank cells in the input. By default,
blank values, `.`, `NA`, and similar missing tokens are skipped. If a literal
blank should occupy a placeholder, use a quoted string or customize
`--na-filters`.

### Simple Example

Input:

```
<tab:Test>
1	2	3
2	1	3
3	1	2
```

Template:

```
\label{tab:test}
\#\#\# & \#\#\# & \#\#\# \\\\
\#\#\# & \#\#\# & \#\#\# \\\\
\#\#\# & \#\#\# & \#\#\# \\\\
```

Output:

```
\label{tab:test}
1	2	3
2	1	3
3	1	2
```

### Missing Values

!!! note "Note"
    Missing values are entries ignored by the parser. This is customized
    via `--na-filters` (CLI) or `nafilters` (function). Default values
    ignored are `--na-filters "." "" "NA" "nan" "NaN" "None"`.

Input:

```
<tab:Test>
1	.	3
2e-5	1	3.023
.	-1	2	3
```

Template:

```
\label{tab:test}
(\#\#\#) & 2      & \#\#\# & \\\\
\#3\#    & \#\#\# & \#1\#  & \\\\
NA       & \#\#\# & \#\#\# & \#\#\# \\\\
```

Output:

```
\label{tab:test}
(1)	2	3
0.000	1	3.0
NA	-1	2	3
```

_**Important**_: Missing values in input and template need not line up.

Input:

```
<tab:Test>
1	.	3
2e-5	.	3.023
.	-1	2
```

Template:

```
\label{tab:test}
\#\#\# & \#\#\# & abc    \\\\
abc    & \#2\#  & \#3\#  \\\\
NA     & \#\#\# & \#\#\# \\\\
```

Output:

```
\label{tab:test}
1	3	abc
abc	0.00	3.023
NA	-1	2
```

### Text

Input:

```
<tab:Test>
1	1	2
1	1	3
2	-1	2
```

Template:

```
\label{tab:test}
\#\#\# & \#\#\# & \#\#\# \\\\
abc    & abc    & abc    \\\\
\#\#\# & \#2\#  & \#3\#  \\\\
\#\#\# & \#\#\# & \#\#\# \\\\
```

Output:

```
\label{tab:test}
1	1	2
abc	abc	abc
1	1.00	3.000
2	-1	2
```
