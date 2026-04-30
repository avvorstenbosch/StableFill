Matrix Shapes
=============

!!! info "Warning"
    This page is under construction

!!! note "Note"
    This section was adapted from the readme for the original tablefill.py

Input files must contain rows of numbers or characters preceded by
`<label>`. Rows may be tab-delimited or whitespace-delimited. Tabs are
still preferred when text cells contain spaces, but whitespace-delimited
rows are convenient for pasted regression output. The numbers can be
arbitrarily long, can be negative, and can also be in scientific
notation.

For economics regression output, a numeric estimate followed immediately by a
parenthesized numeric standard error is treated as one cell:

```text
0.125*** (0.031) -0.456 (0.100)
```

is parsed as two entries, `0.125*** (0.031)` and `-0.456 (0.100)`. A row that
starts with parenthesized standard errors, such as `(0.031) (0.100)`, is parsed
as separate entries because those standard errors usually occupy their own row.

```
<tab:Test>
1	2	3
2	3	1
3	1	2
```

The rows do not need to be of equal length.

```
<tab:FunnyMat>
1	2	3	23	2
2	3
3	1	2	2
1
```

Completely blank (no tab) lines are ignored. If a "cell" is merely ".",
"[space]", or "NA" then it is treated as missing. That is, in the program:

```
<tab:Test>
1	2	3
2	.	1	3
3	    1	2
```

is equivalent to:

```
<tab:Test>
1	2	3
2	1	3
3	1	2
```

This feature is useful as several languages outputs missing values as
NA, blank, or ".". Last, `tablefill` understands scientific notation of
the form: `[numbers].[numbers]e(+/-)[numbers]`

```
<tab:TestScientific>
23.2389e+23
-2.23e-2
-0.922e+3
```

Named Values
------------

Single statistics can be written as `<Val:...>` or `<Value:...>` blocks and referenced with
inline placeholders:

```text
<Val:sample_size>
5708
```

```latex
The sample includes {{val:sample_size|,.0f}} observations.
```
