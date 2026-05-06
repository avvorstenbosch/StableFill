Inspect and Init
================

StableFill has two helper commands for project setup and debugging.

Initialize A Project
--------------------

Run this in a paper directory:

```bash
stablefill init
```

It creates a minimal layout:

```text
stablefill.toml
tables/
```

The generated `stablefill.toml` is intentionally small:

```toml
template = "paper_template.tex"
output = "paper_filled.tex"
input_dir = "tables"
no_header = true
```

StableFill does not create a manuscript template. Add your own TeX, LyX, or
Markdown template, then put one or more `.txt` result files in `tables/`.

You can initialize another directory:

```bash
stablefill init path/to/project
```

Use `--force` if you want to overwrite an existing `stablefill.toml`.

Inspect A Project
-----------------

Use inspect when you want to understand what StableFill will do before it
writes any output:

```bash
stablefill inspect
```

The command reads the same `stablefill.toml` file as normal filling. It also
accepts the usual input and template options:

```bash
stablefill inspect --input-dir tables paper_template.tex
stablefill inspect -i results.txt paper_template.tex
```

Inspect reports:

- which input files were read
- which `<Tab:...>` blocks and `<Val:...>` values were found
- which template tables contain StableFill placeholders
- how many values each table has and how many placeholders it will consume
- inline placeholders that are matched or missing
- already-filled tables that are ignored because they have no placeholders
- unused input tables and values

Inspect is a dry run. It does not create or modify the output file, and it is
meant to explain StableFill's interpretation rather than validate every
possible LaTeX compile issue.
