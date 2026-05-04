"""Placeholder grammar and formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re

try:
    from .errors import DiagnosticContext, PlaceholderError
except ImportError:
    from errors import DiagnosticContext, PlaceholderError


@dataclass
class PlaceholderPatterns:
    """Regular-expression grammar for sequential table placeholders."""

    escape: str = r'(?<!\\)(%|&)'
    any_placeholder: str = r'\\?#\|?((\d+)(,?|\\?%|\\?\.)?|\\?(#|\*)|{0?(:.*?)?}(date|time)?)\|?\\?#'
    annotation: str = r'\[\[SF:.*?\]\]'
    raw_or_stars: str = r'\\?#\\?(#|\*)\\?#'
    numeric: str = r'\\?#\|?(\d+)(,?|\\?%|\\?\.)\|?\\?#'
    integer_decimal: str = r'(-?\d+)(\.?\d*)'
    absolute: str = r'\\?#\|.{1,4}\|\\?#'
    python_format: str = r'\\?#({0?(:.*?)?})(date|time)?\\?#'
    imaginary: str = r'([+-]?[\d.]+)([+-][\d.]+)i$'

    def active_patterns(self):
        return (self.raw_or_stars, self.numeric, self.python_format)


class PlaceholderFormatter:
    """Format sequential and inline StableFill placeholders."""

    def __init__(self, patterns, renderer, pvals, stars):
        self.patterns = patterns
        self.renderer = renderer
        self.pvals = pvals
        self.stars = stars

    def has_placeholder(self, line):
        return any(re.search(pattern, line) for pattern in self.patterns.active_patterns())

    def annotate_value(self, value):
        return '[[SF: %s]]' % value.replace(']]', '] ]')

    def strip_annotations(self, text):
        return re.sub(self.patterns.annotation, '', text)

    def escape_entry(self, entry):
        return self.renderer.escape_text(entry)

    def format_inline_value(self, entry, format_spec=None):
        entry = self.escape_entry(entry)
        if format_spec is None or format_spec == '':
            return entry

        spec = format_spec.strip()
        if spec in ['*', '#*#', r'\#*\#']:
            return self.parse_pval_to_stars('#*#', entry)

        if re.search(self.patterns.numeric, spec):
            return self.round_and_format(spec, entry)

        if re.search(self.patterns.raw_or_stars, spec):
            return re.sub(self.patterns.raw_or_stars, entry, spec, count=1)

        if re.search(self.patterns.python_format, spec):
            return self.format_python_placeholder(spec, entry)

        try:
            return self.escape_entry(format(float(entry), spec))
        except Exception:
            try:
                return self.escape_entry(format(entry, spec))
            except Exception as exc:
                msg = "Unable to apply inline format %r to value %r." % (spec, entry)
                context = DiagnosticContext(placeholder="{{value|%s}}" % spec)
                raise PlaceholderError(msg, context=context, cause=exc)

    def replace_line(
        self,
        line,
        table,
        tablen,
        template=None,
        line_number=None,
        table_tag=None,
        annotate=False,
    ):
        """Replace all placeholders in a template line in source order."""

        i = 0
        force_stop = False
        starts = tablen
        position = 0
        match0 = re.search(self.patterns.any_placeholder, line[position:])
        while match0 and not force_stop:
            relative_s, relative_e = match0.span()
            s = position + relative_s
            e = position + relative_e
            cell = line[s:e]
            matcha = re.search(self.patterns.raw_or_stars, cell)
            matchb = re.search(self.patterns.numeric, cell)
            matchf = re.search(self.patterns.python_format, cell)
            annotation = re.match(self.patterns.annotation, line[e:])
            replacement_end = e + (annotation.end() if annotation else 0)

            if len(table) > tablen:
                context = DiagnosticContext(
                    file=template,
                    line=line_number,
                    column=s + 1,
                    table=table_tag,
                    entry_index=tablen + 1,
                    placeholder=cell,
                    context=line.rstrip('\r\n'),
                )
                try:
                    if matcha:
                        entry = self.escape_entry(table[tablen])
                        if '*' in matcha.groups():
                            replacement = self.parse_pval_to_stars(cell, entry)
                        else:
                            replacement = re.sub(self.patterns.raw_or_stars, entry, cell, count=1)

                        tablen += 1

                    if matchb:
                        entry = self.escape_entry(table[tablen])
                        replacement = self.round_and_format(cell, entry, context=context)
                        tablen += 1

                    if matchf:
                        entry = self.escape_entry(table[tablen])
                        fmt = self.format_python_placeholder(cell, entry, context=context)
                        replacement = re.sub(self.patterns.python_format, fmt, cell, count=1)
                        tablen += 1

                    if annotate:
                        replacement = cell + self.annotate_value(replacement)

                    line = line[:s] + replacement + line[replacement_end:]
                    position = s + len(replacement)
                except PlaceholderError:
                    raise
                except Exception as exc:
                    raise PlaceholderError("Could not replace placeholder.", context=context, cause=exc)
            else:
                if matcha or matchb or matchf:
                    starts = tablen if tablen - starts == i + 1 else starts
                    tablen += 1

                force_stop = True

            match0 = re.search(self.patterns.any_placeholder, line[position:])
            i += 1

        return line, tablen, starts

    def format_python_placeholder(self, cell, entry, context=None):
        matchf = re.search(self.patterns.python_format, cell)
        if matchf.group(3) in ['date', 'time']:
            try:
                d = datetime(1960, 1, 1)
                if matchf.group(3) == 'date':
                    d += timedelta(days=int(float(entry)))
                else:
                    d += timedelta(seconds=int(float(entry)))

                return matchf.group(1).replace('\\', '').format(d)
            except Exception as exc:
                msg = "Unable to apply datetime format %r to entry %r." % (
                    matchf.group(1).replace('\\', ''),
                    entry,
                )
                raise PlaceholderError(msg, context=context, cause=exc)
        else:
            try:
                try:
                    return matchf.group(1).format(entry)
                except Exception:
                    return self.escape_entry(matchf.group(1).format(float(entry)))
            except Exception as exc:
                msg = "Unable to apply python format %r to entry %r." % (matchf.group(1), entry)
                raise PlaceholderError(msg, context=context, cause=exc)

    def round_and_format(self, cell, entry, context=None):
        try:
            precision, comma = re.findall(self.patterns.numeric, cell)[0]
            precision = int(precision)
            roundas = 0 if precision == 0 else pow(10, -precision)
            roundas = Decimal(str(roundas))
            complex_match = re.match(self.patterns.imaginary, entry.replace(" ", ""))
            if complex_match:
                real_part, i_part = complex_match.groups()
                real_rounded = self.round_and_format_helper(real_part, cell, roundas, comma)
                i_rounded = self.round_and_format_helper(i_part, cell, roundas, comma)
                i_sign = "+" if not i_rounded.startswith('-') else ""
                rounded = real_rounded + i_sign + i_rounded
            else:
                rounded = self.round_and_format_helper(entry, cell, roundas, comma)
            return re.sub(self.patterns.numeric, rounded, cell, count=1)
        except Exception as exc:
            msg = (
                "Unable to apply numeric placeholder %r to entry %r. "
                "This usually means a text or parenthesized value was sent "
                "to a numeric placeholder; use ### or {{name}} for literal text."
            )
            raise PlaceholderError(msg % (cell.strip(), entry), context=context, cause=exc)

    def round_and_format_helper(self, entry, cell, roundas, comma):
        if '%' in comma:
            dentry = 100 * Decimal(entry)
        elif '.' in comma:
            dentry = Decimal(entry) / 100
        else:
            dentry = Decimal(entry)
        dentry = abs(dentry) if re.search(self.patterns.absolute, cell) else dentry
        rounded = str(dentry.quantize(roundas, rounding=ROUND_HALF_UP))
        if ',' in comma:
            integer_part, decimal_part = re.findall(self.patterns.integer_decimal, rounded)[0]
            neg = '-' if re.match('^-0', integer_part) else ''
            rounded = neg + format(int(integer_part), ',d') + decimal_part
        return rounded

    def parse_pval_to_stars(self, cell, entry):
        pos = sum([float(entry) < p for p in self.pvals]) - 1
        star = '' if pos < 0 else self.stars[pos]
        return re.sub(self.patterns.raw_or_stars, star, cell, count=1)
