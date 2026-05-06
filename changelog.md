# Changelog

## Unreleased

No unreleased changes yet.

## StableFill 0.14.0 (2026-05-06)

### Features

- Add `--input-dir` / `input_dir` support for reading all `.txt` result files from a directory in sorted order.
- Automatically use a `tables` directory next to the template when no explicit input file or input directory is provided.
- Add `stablefill.toml` support for running the CLI with saved template, input, output, and formatting settings.
- Add `stablefill inspect` as a dry-run command that reports detected inputs, template placeholders, ignored already-filled tables, missing values, and unused blocks.
- Add `stablefill init` to create a minimal `stablefill.toml` and `tables/` directory for new projects.

### Deprecations

- Deprecate custom XML/Python table generation. Existing XML blocks still run, but now emit a `FutureWarning`.

### Documentation

- Document input directories, automatic `tables/` discovery, `stablefill.toml`, `stablefill inspect`, and `stablefill init` in the README and documentation site.

## StableFill 0.12.0 (2026-05-04)

### Packaging

- Rename the distribution metadata to `stablefill` while preserving the legacy `tablefill` command and import path as aliases.
- Add `from stablefill import stablefill` and `python -m stablefill` as the preferred Python API and module entry point.
- Move implementation modules into the `stablefill` package while keeping `tablefill` as a compatibility shim.
- Make `pyproject.toml` the single packaging metadata source, add bounded `test`, `docs`, and `dev` extras, and remove the duplicate `setup.py`.

### Bug fixes

- Preserve the character before unescaped `&` and `%` when escaping LaTeX replacement text.
- Escape percent signs produced by inline Python format strings such as `{{rate|.1%}}`.
- Avoid missing-input warnings for already-filled tables that have `tab:` labels but no StableFill placeholders.
- Recover the common CLI order `stablefill -i results.txt template.tex -o filled.tex`, which previously let `--input` swallow the template argument.

### Improvements

- Split template grammar/scanning, placeholder formatting, rendering, and structured diagnostics into focused modules.
- Attach file, line, table tag, entry index, placeholder, and source-line context to expected parse and placeholder failures.
- Add annotation mode with compact `[[SF: ...]]` previews, plus a cleanup mode that removes annotations without filling placeholders.

### Tests

- Add a long complex LaTeX integration fixture with ragged tables, economics regression outputs, inline values, already-filled tables, comments, and false-positive guards.
- Cover annotation updates, normal fills from annotated templates, and CLI annotation cleanup without an input file.

## tablefill-0.11.0 (2026-04-30)

### Features

- Add inline named value placeholders such as `{{sample_size|,.0f}}`.
- Add `<Val:...>`, `<Value:...>`, `<Scalar:...>`, and `<Stat:...>` input blocks.
- Add `{{val:name}}` as the recommended inline placeholder style for prose.
- Accept whitespace-delimited input rows for regression tables with coefficient and standard-error rows.
- Treat adjacent `estimate (standard error)` pairs as one logical table cell.
- Document and test ragged placeholder layouts that fill in top-to-bottom, left-to-right source order.
- Add `stablefill` and `python -m tablefill` command entry points.

### Improvements

- Move input parsing, inline replacement, and domain exceptions into focused modules.
- Avoid eager NumPy matrix coercion when no custom XML tables are present, so ragged table rows remain safe in normal fills.
- Improve numeric placeholder errors with template line, table tag, entry index, placeholder, and original exception details.
- Make `numpy` optional for normal installations and update package metadata for Python 3.8+.

## tablefill-0.10.1 (2026-01-20)

### Improvements

- Allow imaginary matrices (tested from Matlab with `writematrix`)

## tablefill-0.9.16 (2024-10-17)

### Improvements

- Allow `.` modifier to divide by 100.

## tablefill-0.9.15 (2024-09-14)

### Bug fixes

- Bump version because `exec_info` isn't updated

## tablefill-0.9.14 (2023-09-04)

### Improvements

- Improved debugging messages
- Allow numpy evaluation

## tablefill-0.9.13 (2023-05-09)

### Bug fixes

- Fixed 'rU' reading mode (change to 'r' in Python3)

## tablefill-0.9.12 (2022-05-19)

### Bug fixes

- Fixed numpy concatenation of individual elements

## tablefill-0.9.11 (2022-02-15)

### Bug fixes

- Fixed collections.Iterabble import

## tablefill-0.9.10 (2021-10-27)

### Features

- Default NaN filders include Inf and INF
- Datetime format

## tablefill-0.9.9 (2021-02-20)

### Features

- Support subtable environment

## tablefill-0.9.8 (2021-02-08)

### Bug fixes

- Fixed log typos

## tablefill-0.9.7 (2021-02-02)

### Features

- `--no-header` option to supress header.
- `--log-file` and `--log-only` options to redirect logging info.

## tablefill-0.9.6 (2020-09-07)

### Features

- Allow `--na-filters` (`nafilters`) to customize missing value filters.

## tablefill-0.9.5 (2019-02-27)

### Features

- Allow commented-out tablefill delimiters in LaTeX

### Enhancements

- Make it clear you can update anything with placeholders, not just tables.

## tablefill-0.9.4 (2019-02-26)

### Features

- New placeholder #{}# allows arbitrary python-style formatting.
- Added `sampleTable` as a stata-installable package to the repo.
- Merged in sample workflow and Kyle's guide with 'getting started' section.
- Added markdown example.

## tablefill-0.9.3 (2019-02-26)

### Features

- Raw LaTeX support in markdown

## tablefill-0.9.2 (2019-02-26)

### Features

- Markdown support:

    <!-- tablefill:start tab:label -->

    Table with placeholders

    <!-- tablefill:end -->

## tablefill-0.9.1 (2018-07-17)

### Features

- Pip-installable by [@kylebarron](https://github.com/kylebarron).

## tablefill-0.9.0 (2018-07-17)

### Bug Fixes

- Python 3 support. Fixes https://github.com/mcaceresb/tablefill/issues/2
- Encloses all filters in `list`
- File concatenation replaces deprecated `U` flag for `newline = None`
- `nested_convert` avoids iterating over strings.
- output file is opened as `w` instead of `wb`

## tablefill-0.8.1 (2017-06-13)

### Features

- Old XML parsing available via `--legacy-parsing`
- Basic XML error checks
- Numpy syntax can do string and numeric numpy matrices.
- XML engine parses all entries to numeric and string
  dictionaries and parses strings and floats sepparately.

## tablefill-0.8.0 (2017-04-11)

### Features

- `<tablefill-custom>` has been moved to `<tablefill-python>`
    - The engine now evaluates whatever is in the tag.
    - All the tables are available as python lists of lists
    - The resulting object is read into the specified tag
    - Can pass `syntax = 'numpy'` to use `numpy` matrix syntax instead of
      python list slicing.
    - Can pass `type = 'float'` so all entries in each table
      are available as floats instead of strings.
    - WARNING: When using `type = float` the conversion is NOT
      necessarily lossless, as with the normal tablefill you can also
      have placeholders be replaced with strings. But if you try to
      convert everything to floats then you will replace those with
      missing. This would only affect tables created this way.
- When tablefill call is empty, nothing is parsed. In previous
  versions the entire table was added.
- The default syntax can be changed to `numpy` via `--use-numpy`
- The default conversion can be changed to `float` via `--use-floats`

An example:
```xml
<tablefill-python tag = 'output_table' type = 'float'>
    input_table0[1][2], input_table0[2][1],
    input_table0[1][2] / input_table0[2][1],
</tablefill-python>

<tablefill-python tag = 'output_table' type = 'float' syntax = 'numpy'>
    input_table0[:2, :2] / input_table1[:2, :2]
</tablefill-python>
```

### Planned

- Error checking for XML parsing: Currently very minimal
  error checks are in place as this functionality is beta.
  - If XMl file is provided, note if parsing failed in that file
  - If multiple XML files provided, give file name as well
  - Whether error was due to regex parsing
  - Whether an opened tag was closed
  - Closing a tag and opening the next tag on the same line
  - Etc.
- Replace tablefill-python with a more limited tablefill-math
  so that I don't have to worry about executing arbitrary python
  code. It's bad practice, no?
- Replace engine with eval using the table dictionary as the context to
  simplify syntax. This would result in, for instance
```xml
<tablefill-custom tag = 'newtagname'>
    tagname[rows1][subentries1],
    tagname[rows2][subentries2],
    tagname[rows3][subentries3],
    othertagname[rows3][subentries3]
</tablefill-custom>
```
This would also simplify the function call for math... Have a float
dictionary and a normal one. Use the float dictionary for `type =
'float'` and the string otherwise. Always update both. Then for

## tablefill-0.7.0 (2016-10-24)

### Features

* Added placeholder #|\d+|# to take absolute value of input
* Added backwards-compatible list flattening
* Added option to fill in the comments.
* Now parses commented XML code to combine tables

```xml
<tablefill-custom tag = 'newtagname'>
    <combine tag = 'tagname'>
        [rows1][subentries1];
        [rows2][subentries2];
    </combine>
    <combine tag = 'othertagname'>
        [rows3][subentries3]
    </combine>
</tablefill-custom>
```

is parsed to combine `[rows1][subentries1]` and `[rows2][subentries2]`
from `tagname` with `[rows3][subentries3]` of `othertagname`. The
syntax for `[rows][sub]` is python syntax for nested lists: See
[here](http://stackoverflow.com/questions/509211#509295). Note that
python uses 0-based indexing and that the combine engine uses the raw
matrices (i.e. before missing entries are stripped). Each matrix is
parsed as a list of lists, so

```html
1  2  3    [[1,  2,  3],
. -1 -2 --> [., -1, -2],
.  0  .     [.,  0,  .]]

[0]  or [-1]  --> [.,  0,  .]
[1]  or [-2]  --> [., -1, -2]
[2]  or [-3]  --> [1,  2,  3]
[1:] or [-2:] --> [.,  0,  .]
[1][1:3] or [-2][-2:] --> [-1, -2]
```

## tablefill-0.6.0 (2016-10-16)

### Features

* Can now parse entry as p-value (i.e. replace with stars)
* Backwards-compatible comma formatting
* Can now have multiple matches per cell
* Tolerates "NA" as missing value (for R compatibility)

### Bug fixes

* Can correctly compile bibtex (cd into dir, etc.)
* Can correctly parse too many/too few matches.
* Regexps now only tolerate one escape character.
* Regexps now accept comments with leading blanks.
