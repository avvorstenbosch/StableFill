Inline Values
=============

Use inline values for statistics that appear in prose, captions, notes, or any
other non-table text. Inline values do not need `tablefill:start` or
`tablefill:end` markers.

Input
-----

Add named value blocks to the same input text file you already pass to
StableFill:

```text
<Val:population>
5708

<Value:mean_age>
42.35

<Value:p_value>
0.024
```

`<Val:name>` and `<Value:name>` are equivalent.

Template
--------

Reference those values anywhere in LaTeX, LyX, or Markdown with
`{{val:name}}`:

```latex
The sample includes {{val:population|,.0f}} people.
Mean age is {{val:mean_age|.1f}}.
The key coefficient is significant{{val:p_value|*}}.
```

The `val:` prefix is optional, so `{{population|,.0f}}` also works. The prefix
is recommended in prose because it makes named values easy to spot.

Output
------

```latex
The sample includes 5,708 people.
Mean age is 42.4.
The key coefficient is significant**.
```

Formats
-------

Inline values support compact formats:

Placeholder          | Meaning
-------------------- | -------
`{{val:name}}`       | Insert the value as written.
`{{val:name\|,.0f}}`  | Use Python's format mini-language.
`{{val:p_value\|*}}`  | Convert a p-value to significance stars.
`{{val:name\|#0,#}}`  | Use an existing tablefill numeric placeholder fragment.

`<Tab:...>` blocks are also available as inline values. When a table tag is
referenced with `{{val:tag}}`, StableFill inserts the first non-missing entry
from that table. If a `<Value:...>` block and `<Tab:...>` block share a name,
the explicit value block wins.
