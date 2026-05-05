Configuration Files
===================

StableFill can read settings from `stablefill.toml`. This is useful when a
paper is rebuilt many times with the same template, output path, input
directory, and formatting settings.

Basic Config
------------

Create `stablefill.toml` in the directory where you run StableFill:

```toml
template = "paper_template.tex"
output = "paper_filled.tex"
input_dir = "tables"
no_header = true
```

Then run:

```bash
stablefill
```

Command-line options override config values:

```bash
stablefill --annotate -o paper_annotated.tex
```

Supported Fields
----------------

StableFill accepts the main CLI option names in TOML form:

```toml
template = "paper_template.tex"
output = "paper_filled.tex"
input = ["tables/main.txt", "tables/appendix.txt"]
input_dir = "tables"
filetype = "tex"
no_header = true
annotate = false
remove_annotations = false
ignore_xml = true
silent = false
verbose = false
```

Formatting settings can be top-level or under `[formatting]`:

```toml
[formatting]
pvals = [0.1, 0.05, 0.01]
stars = ["*", "**", "***"]
nafilters = [".", "", "NA", "nan", "NaN", "None", "Inf", "INF"]
```

Explicit Config Path
--------------------

Use `--config` to load a differently named file:

```bash
stablefill --config stablefill-appendix.toml
```

Notes
-----

Use either `input` or `input_dir`, not both. If neither is set, StableFill
still looks for a `tables` directory next to the template.
