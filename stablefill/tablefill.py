#!/usr/bin/env python
# encoding: utf-8

"""Fill LaTeX template files with external inputs

Description
-----------

StableFill is a Python module designed to fill LaTeX, LyX, and Markdown
tables and inline values with output from text files. It is based on the
original tablefill project, and keeps the historical ``tablefill`` command and
import path as compatibility aliases. Both of the following are valid:

>>> from tablefill import tablefill
>>> from stablefill import stablefill

$ stablefill --help

Usage
-----

stablefill [-h] [-v] [FLAGS] [-i [INPUT [INPUT ...]]] [-o OUTPUT]
          [--pvals [PVALS [PVALS ...]]] [--stars [STARS [STARS ...]]]
          [--na-filters [FILTER [FILTER ...]]] [-t {auto,lyx,tex,md}]
          [--xml-tables [INPUT [INPUT ...]]]
          TEMPLATE

Fill tagged tables and inline values in LaTeX, LyX, and Markdown files.

positional arguments:
  TEMPLATE              Code template

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Show current version
  -i [INPUT [INPUT ...]], --input [INPUT [INPUT ...]]
                        Input files with tables (default: TEMPLATE_table)
  -o OUTPUT, --output OUTPUT
                        Processed template file (default: TEMPLATE_filled)
  -t {auto,lyx,tex,md}, --type {auto,lyx,tex,md}
                        Template file type (default: auto)
  --pvals [PVALS [PVALS ...]]
                        Significance thresholds
  --stars [STARS [STARS ...]]
                        Stars for sig thresholds (enclose each entry in quotes)
  --na-filters [FILTER [FILTER ...]]
                        Filters for missing values (enclose each entry in quotes)
  --xml-tables [INPUT [INPUT ...]]
                        Files with custom xml combinations.

flags:
  -f, --force           Name input/output automatically
  -c, --compile         Compile output
  -b, --bibtex          Run bibtex on .aux file and re-compile
  -fc, --fill-comments  Fill in commented out placeholders.
  -nc, --no-header      Supress header for filled template.
  --log-only            Print results to log file only.
  --log-file            Print results to log file.
  --numpy-syntax        Numpy syntax for custom XML tables.
  --use-floats          Force floats when passing objects to custom XML python.
  --ignore-xml          Ignore XML in template comments.
  --verbose             Verbose printing (for debugging)
  --silent              Try to say nothing

For details on the files and the replacement engine, see the documentation.

    https://avvorstenbosch.github.io/StableFill/getting-started.html

WARNING
-------

The program currently does not handle trailing comments. If a line
doesn't start with a comment, it will replace everything in that line,
even if there is a comment halfway through.

Examples
--------

If you installed the program, then simply run

$ ls
test.tex
test_table.txt
$ stablefill test.tex --force --silent

The historical command name remains available:

$ ls
test.tex
test_table.txt
test_filled.txt
$ tablefill test.tex -i test_table.txt -o output.tex --verbose

Notes
-----

Several legacy try-catch pairs and error checks remain because StableFill may
be run from Python as well as from the command line. Current releases target
Python 3.8 and newer.
"""

# NOTE: For all my personal projects I import the print function from
# the future. You should do that also. Seriously (:

from __future__ import division, print_function
from os import linesep, path, access, W_OK, system, chdir, listdir, remove, makedirs
from traceback import format_exc
from operator import itemgetter
from sys import exit as sysexit
from sys import version_info
from tempfile import mktemp

import xml.etree.ElementTree as xml
import argparse
import sys
import re
import warnings

try:
    from .config import CONFIG_BASENAME, as_list, flatten_config, load_config_file
    from .errors import DiagnosticContext, PlaceholderError
    from .inline import INLINE_RE, replace_inline_placeholders, strip_annotations
    from .parsers import normalize_key, parse_input_files
    from .placeholders import PlaceholderFormatter, PlaceholderPatterns
    from .renderers import renderer_for_filetype
    from .template_scanner import TemplateScanner, grammar_for_filetype
except ImportError:
    from config import CONFIG_BASENAME, as_list, flatten_config, load_config_file
    from errors import DiagnosticContext, PlaceholderError
    from inline import INLINE_RE, replace_inline_placeholders, strip_annotations
    from parsers import normalize_key, parse_input_files
    from placeholders import PlaceholderFormatter, PlaceholderPatterns
    from renderers import renderer_for_filetype
    from template_scanner import TemplateScanner, grammar_for_filetype

try:
    # Python <= 3.9
    from collections import Iterable as Iter
except ImportError:
    # Python > 3.9
    from collections.abc import Iterable as Iter

try:
    import numpy
    numpyok = True
except:
    numpyok = False

__program__   = "stablefill"
__usage__     = """[-h] [-v] [FLAGS] [-i [INPUT [INPUT ...]]] [-o OUTPUT]
                    [--pvals [PVALS [PVALS ...]]] [--stars [STARS [STARS ...]]]
                    [--na-filters [FILTER [FILTER ...]]] [-t {auto,lyx,tex,md}]
                    [--xml-tables [INPUT [INPUT ...]]]
                    TEMPLATE"""
__purpose__   = "Fill tagged tables and inline values in LaTeX, LyX, and Markdown files"
__author__    = "Mauricio Caceres <caceres@nber.org>"
__created__   = "Thu Jun 18, 2015"
__updated__   = "Wed May 06, 2026"
__version__   = "StableFill version 0.14.0 updated " + __updated__

# Define basestring in a backwards-compatible way
try:
    basestring
except NameError:
    basestring = str

try:
    execfile
except NameError:
    def execfile(filename, globals = None, locals = None):
        if globals is None:
            globals = {}
        if locals is None:
            locals = globals
        with open(filename, "rb") as handle:
            code = compile(handle.read(), filename, "exec")
        exec(code, globals, locals)


def main():
    """
    WARNING: This function expects command-line inputs to exist.
    """

    if len(sys.argv) > 1 and sys.argv[1] == 'inspect':
        sysexit(run_inspect_command(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        sysexit(run_init_command(sys.argv[2:]))

    fill = StableFillCLIParser()
    fill.get_input_parser()
    fill.get_parsed_arguments()
    fill.get_argument_strings()
    fill.get_file_type()

    exit, exit_msg = stablefill(template       = fill.template,
                                input          = fill.input,
                                input_dir      = fill.input_dir,
                                output         = fill.output,
                                filetype       = fill.ext,
                                verbose        = fill.verbose,
                                silent         = fill.silent,
                                pvals          = fill.pvals,
                                stars          = fill.stars,
                                nafilters      = fill.nafilters,
                                fillc          = fill.fillc,
                                nohead         = fill.nohead,
                                log_file       = fill.log_file,
                                log_only       = fill.log_only,
                                legacy_parsing = fill.legacy_parsing,
                                numpy_syntax   = fill.numpy_syntax,
                                use_floats     = fill.use_floats,
                                ignore_xml     = fill.ignore_xml,
                                xml_tables     = fill.xml_tables,
                                annotate       = fill.annotate,
                                remove_annotations = fill.remove_annotations)

    if exit == 'SUCCESS':
        fill.get_compiled()
        sysexit(0)
    elif exit == 'WARNING':
        print_silent(fill.silent, "Exit status came with a warning")
        print_silent(fill.silent, "Output might not be as expected!")
        print_silent(fill.silent, "Rerun program with --verbose option.")
        fill.get_compiled()
        sysexit(1)
    elif exit == 'ERROR':
        fillerror_msg  = 'ERROR while filling table.'
        fillerror_msg += ' Check function call.' + linesep
        print_silent(fill.silent, fillerror_msg)
        fill.parser.print_usage()
        sysexit(1)


# Backwards-compatible file concatenation
def concat_files(flist):
    if version_info >= (3, 0):
        readlist = [open(fn, 'r', newline = None).readlines() for fn in flist]
    else:
        readlist = [open(fn, 'rU').readlines() for fn in flist]

    return sum(readlist, [])


# Backwards-compatible string formatting
# Backwards-compatible list flattening
# http://stackoverflow.com/questions/2158395/
def flatten(l):
    if version_info >= (3, 0):
        for el in l:
            if isinstance(el, Iter) and not isinstance(el, (str, bytes)):
                for sub in flatten(el):
                    yield sub
            else:
                yield el
    else:
        for el in l:
            if isinstance(el, Iter) and not isinstance(el, basestring):
                for sub in flatten(el):
                    yield sub
            else:
                yield el


def tolist(anything):
    return anything if isinstance(anything, list) else [anything]


def tolist2(anything):
    return list(anything) if hasattr(anything, '__iter__') else [anything]


def print_verbose(prints, stuff):
    if prints:
        print(stuff)


def print_silent(silence, stuff):
    if not silence:
        print(stuff)


def custom_convert(x, func):
    if isinstance(x, func):
        return x
    else:
        try:
            return func(x)
        except:
            return None


def nested_convert(item, func):
    if hasattr(item, '__iter__') and not isinstance(item, basestring):
        return [nested_convert(x, func) for x in item]

    return custom_convert(item, func)


# ---------------------------------------------------------------------
# StableFill public function. The historical ``tablefill`` function name is
# kept for backwards compatibility.

def tablefill(silent         = False,
              verbose        = True,
              filetype       = 'auto',
              pvals          = [0.1, 0.05, 0.01],
              stars          = ['*', '**', '***'],
              nafilters      = ['.', '', 'NA', 'nan', 'NaN', 'NaN+0i', 'None', 'Inf', 'INF'],
              fillc          = False,
              nohead         = False,
              log_file       = None,
              log_only       = False,
              legacy_parsing = False,
              numpy_syntax   = False,
              use_floats     = False,
              ignore_xml     = False,
              xml_tables     = None,
              input_dir      = None,
              annotate       = False,
              remove_annotations = False,
              **kwargs):
    """Fill LaTeX, LyX, or Markdown template files with external inputs.

    Description
    -----------

    StableFill fills LaTeX, LyX, or Markdown tables and inline values with
    output from text files. The historical function name ``tablefill`` remains
    available for backwards compatibility.

    Required Input
    --------------

    template : str
        Name of user-written document to use as basis for update
    input : str
        Space-separated list of files with tables to be used in update.
    input_dir : str
        Directory with .txt input files. Files are read in sorted filename
        order. If neither input nor input_dir is provided, StableFill looks
        for a "tables" directory next to the template.
    output : str
        Filled template to be produced.

    For details on the files and the replacement engine, see the documentation.

        https://avvorstenbosch.github.io/StableFill/getting-started.html

    Optional Input
    --------------
    verbose : bool
        print a lot of info
    silent : bool
        try to print nothing at all
    filetype : str
        auto, lyx, tex, or md

    Output
    ------
    exit : str
        One of SUCCESS, WARNING, ERROR
    exit_msg : str
        Details on the exit status


    Usage
    -----
    exit, exit_msg = stablefill(template = 'template_file',
                                input    = 'input_file(s)',
                                output   = 'output_file')
    """
    if log_file:
        sys.stdout = Logger(log_file, log_only)

    print_verbose(verbose, "Arguments look OK. Will run StableFill.")
    try:
        if input_dir is not None:
            kwargs['input_dir'] = input_dir

        verbose = verbose and not silent
        logmsg  = "Parsing arguments..."
        print_verbose(verbose, logmsg)
        fill_engine = StableFillEngine(filetype,
                                       verbose,
                                       silent,
                                       pvals,
                                       stars,
                                       nafilters,
                                       fillc,
                                       nohead,
                                       legacy_parsing,
                                       numpy_syntax,
                                       use_floats,
                                       ignore_xml,
                                       xml_tables,
                                       annotate,
                                       remove_annotations)

        fill_engine.get_parsed_arguments(kwargs)
        fill_engine.get_file_type()
        fill_engine.get_regexps()

        if not fill_engine.remove_annotations:
            logmsg  = "Parsing StableFill input blocks into dictionaries:" + linesep + '\t'
            logmsg += (linesep + '\t').join(tolist(fill_engine.input))
            print_verbose(verbose, logmsg)
            fill_engine.get_parsed_tables()

        logmsg  = "Searching for labels in template:" + linesep + '\t'
        logmsg += (linesep + '\t').join(tolist(fill_engine.template))
        print_verbose(verbose, logmsg + linesep)
        fill_engine.get_filled_template()

        logmsg = "Adding warning that this was automatically generated..."
        print_verbose(verbose, logmsg)
        fill_engine.get_notification_message()

        logmsg = "Writing to output file '%s'" % fill_engine.output
        print_verbose(verbose, logmsg)
        fill_engine.write_to_output(fill_engine.filled_template)

        logmsg = "Wrapping up..." + linesep
        print_verbose(verbose, logmsg)
        fill_engine.get_exit_message()
        print_silent(silent, fill_engine.exit + '!')
        print_silent(silent, fill_engine.exit_msg)
        return fill_engine.exit, fill_engine.exit_msg
    except:
        exit_msg = format_exc()
        exit     = 'ERROR'
        print_silent(silent, exit + '!')
        print_silent(silent, exit_msg)
        return exit, exit_msg


stablefill = tablefill

# ---------------------------------------------------------------------
# StableFill CLI parsing internals


def inspect_stablefill(silent         = False,
                       verbose        = False,
                       filetype       = 'auto',
                       pvals          = [0.1, 0.05, 0.01],
                       stars          = ['*', '**', '***'],
                       nafilters      = ['.', '', 'NA', 'nan', 'NaN', 'NaN+0i', 'None', 'Inf', 'INF'],
                       fillc          = False,
                       legacy_parsing = False,
                       numpy_syntax   = False,
                       use_floats     = False,
                       ignore_xml     = False,
                       xml_tables     = None,
                       input_dir      = None,
                       output         = None,
                       **kwargs):
    """Return a human-readable dry-run report without writing output."""
    try:
        if input_dir is not None:
            kwargs['input_dir'] = input_dir
        if output is not None:
            kwargs['output'] = output

        engine = StableFillEngine(filetype,
                                  verbose,
                                  silent,
                                  pvals,
                                  stars,
                                  nafilters,
                                  fillc,
                                  True,
                                  legacy_parsing,
                                  numpy_syntax,
                                  use_floats,
                                  ignore_xml,
                                  xml_tables)
        engine.get_parsed_arguments(kwargs, require_output=False)
        engine.get_file_type()
        engine.get_regexps()
        engine.get_parsed_tables()
        report = engine.get_inspection_report()
        print_silent(silent, report)
        return 'SUCCESS', report
    except:
        exit_msg = format_exc()
        print_silent(silent, 'ERROR!')
        print_silent(silent, exit_msg)
        return 'ERROR', exit_msg


def run_inspect_command(argv=None):
    fill = StableFillCLIParser(command='inspect', argv=argv)
    fill.get_input_parser()
    fill.get_parsed_arguments()
    fill.get_argument_strings()
    fill.get_file_type()

    status, _ = inspect_stablefill(template       = fill.template,
                                   input          = fill.input,
                                   input_dir      = fill.input_dir,
                                   output         = fill.output,
                                   filetype       = fill.ext,
                                   verbose        = fill.verbose,
                                   silent         = fill.silent,
                                   pvals          = fill.pvals,
                                   stars          = fill.stars,
                                   nafilters      = fill.nafilters,
                                   fillc          = fill.fillc,
                                   legacy_parsing = fill.legacy_parsing,
                                   numpy_syntax   = fill.numpy_syntax,
                                   use_floats     = fill.use_floats,
                                   ignore_xml     = fill.ignore_xml,
                                   xml_tables     = fill.xml_tables)
    return 0 if status == 'SUCCESS' else 1


def run_init_command(argv=None):
    parser = argparse.ArgumentParser(
        prog=__program__ + ' init',
        description='Create a minimal StableFill project layout.',
    )
    parser.add_argument('directory',
                        nargs='?',
                        default='.',
                        help='Project directory to initialize (default: current directory).')
    parser.add_argument('--tables-dir',
                        default='tables',
                        help='Directory for .txt result files (default: tables).')
    parser.add_argument('--template',
                        default='paper_template.tex',
                        help='Template path to write into stablefill.toml.')
    parser.add_argument('--output',
                        default='paper_filled.tex',
                        help='Output path to write into stablefill.toml.')
    parser.add_argument('-f', '--force',
                        action='store_true',
                        help='Overwrite an existing stablefill.toml.')
    args = parser.parse_args(argv)

    root = path.abspath(args.directory)
    if not path.isdir(root):
        makedirs(root)

    tables_dir = path.join(root, args.tables_dir)
    if not path.isdir(tables_dir):
        makedirs(tables_dir)
        tables_status = 'created'
    else:
        tables_status = 'already exists'

    config_path = path.join(root, CONFIG_BASENAME)
    config_existed = path.isfile(config_path)
    if config_existed and not args.force:
        config_status = 'already exists'
    else:
        with open(config_path, 'w') as handle:
            handle.write('template = "%s"%s' % (_toml_path(args.template), linesep))
            handle.write('output = "%s"%s' % (_toml_path(args.output), linesep))
            handle.write('input_dir = "%s"%s' % (_toml_path(args.tables_dir), linesep))
            handle.write('no_header = true%s' % linesep)
        config_status = 'updated' if config_existed else 'created'

    print('StableFill project initialized in %s' % root)
    print('  %s: %s' % (args.tables_dir, tables_status))
    print('  %s: %s' % (CONFIG_BASENAME, config_status))
    return 0


def _toml_path(value):
    return value.replace('\\', '/').replace('"', '\\"')


class StableFillCLIParser:
    """
    WARNING: Internal class to parse arguments to pass to StableFill.
    """
    def __init__(self, command='fill', argv=None):
        self.command = command
        self.argv = sys.argv[1:] if argv is None else argv
        self.compiler = {'tex': "xelatex ",
                         'lyx': "lyx -e pdf2 ",
                         'md': "pandoc -i "}
        self.bibtex   = {'tex': "bibtex ",
                         'lyx': "echo Not sure how to run BiBTeX via LyX on ",
                         'md': "echo Not sure how to run BiBTeX via pandoc on "}

    def get_input_parser(self):
        """
        Parse command-line arguments using argparse; return parser
        """
        parser_desc    = __purpose__ if self.command == 'fill' else "Inspect what StableFill would fill without writing output."
        parser_prog    = __program__ if self.command == 'fill' else __program__ + ' ' + self.command
        # parser_use     = __program__ + ' ' + __usage__
        parser_version = __version__
        parser = argparse.ArgumentParser(prog  = parser_prog,
                                         description = parser_desc)
        parser.add_argument('-v', '--version',
                            action   = 'version',
                            version  = parser_version,
                            help     = "Show current version")
        parser.add_argument('--config',
                            dest     = 'config',
                            type     = str,
                            nargs    = 1,
                            metavar  = 'CONFIG',
                            default  = None,
                            help     = "TOML configuration file (default: stablefill.toml when present)",
                            required = False)
        parser.add_argument('template',
                            nargs    = '?',
                            type     = str,
                            metavar  = 'TEMPLATE',
                            help     = "Code template")
        parser.add_argument('-i', '--input',
                            dest     = 'input',
                            type     = str,
                            nargs    = '*',
                            metavar  = 'INPUT',
                            default  = None,
                            help     = "Input files with tables"
                                       " (default: INPUT_table)",
                            required = False)
        parser.add_argument('-d', '--input-dir',
                            dest     = 'input_dir',
                            type     = str,
                            nargs    = 1,
                            metavar  = 'DIR',
                            default  = None,
                            help     = "Directory with .txt input files. If no input is provided, StableFill looks for a tables directory next to TEMPLATE.",
                            required = False)
        parser.add_argument('-o', '--output',
                            dest     = 'output',
                            type     = str,
                            nargs    = 1,
                            metavar  = 'OUTPUT',
                            default  = None,
                            help     = "Processed template file"
                                       " (default: INPUT_filled)",
                            required = False)
        parser.add_argument('-t', '--type',
                            dest     = 'filetype',
                            type     = str,
                            nargs    = 1,
                            choices  = ['auto', 'lyx', 'tex', 'md'],
                            default  = ['auto'],
                            help     = "Template file type (default: auto)",
                            required = False)
        parser.add_argument('--pvals',
                            dest     = 'pvals',
                            type     = str,
                            nargs    = '*',
                            default  = ['0.1', '0.05', '0.01'],
                            help     = "Significance thresholds",
                            required = False)
        parser.add_argument('--stars',
                            dest     = 'stars',
                            type     = str,
                            nargs    = '*',
                            default  = ['*', '**', '***'],
                            help     = "Stars for sig thresholds "
                                       "(enclose each in quotes)",
                            required = False)
        parser.add_argument('--na-filters',
                            dest     = 'nafilters',
                            type     = str,
                            nargs    = '*',
                            default  = ['.', '', 'NA', 'nan', 'NaN', 'NaN+0i', 'None', 'Inf', 'INF'],
                            help     = "Filters for missing values"
                                       "(enclose each in quotes)",
                            required = False)
        parser.add_argument('-f', '--force',
                            dest     = 'force',
                            action   = 'store_true',
                            help     = "Name input/output automatically",
                            required = False)
        parser.add_argument('-c', '--compile',
                            dest     = 'compile',
                            action   = 'store_true',
                            help     = "Compile output",
                            required = False)
        parser.add_argument('-b', '--bibtex',
                            dest     = 'bibtex',
                            action   = 'store_true',
                            help     = "Compile BiBTeX",
                            required = False)
        parser.add_argument('-fc', '--fill-comments',
                            dest     = 'fill_comments',
                            action   = 'store_true',
                            help     = "Fill placeholders in comments",
                            required = False)
        parser.add_argument('--annotate',
                            dest     = 'annotate',
                            action   = 'store_true',
                            help     = "Keep placeholders and add/update [[SF: value]] annotations.",
                            required = False)
        parser.add_argument('--remove-annotations',
                            dest     = 'remove_annotations',
                            action   = 'store_true',
                            help     = "Remove all [[SF: value]] annotations without filling.",
                            required = False)
        parser.add_argument('-nc', '--no-header',
                            dest     = 'no_header',
                            action   = 'store_true',
                            help     = "Supress header for filled template.",
                            required = False)
        parser.add_argument('--ignore-xml',
                            dest     = 'ignore_xml',
                            action   = 'store_true',
                            help     = "Ignore XML in template comments.",
                            required = False)
        parser.add_argument('--legacy-parsing',
                            dest     = 'legacy_parsing',
                            action   = 'store_true',
                            help     = "Legacy parsing for XML tables.",
                            required = False)
        parser.add_argument('--numpy-syntax',
                            dest     = 'numpy_syntax',
                            action   = 'store_true',
                            help     = "Numpy syntax for custom XML tables.",
                            required = False)
        parser.add_argument('--use-floats',
                            dest     = 'use_floats',
                            action   = 'store_true',
                            help     = "Use floats for custom XML python.",
                            required = False)
        parser.add_argument('--xml-tables',
                            dest     = 'xml_tables',
                            type     = str,
                            nargs    = '*',
                            metavar  = 'INPUT',
                            default  = None,
                            help     = "Files with custom XML combinations (deprecated).",
                            required = False),
        parser.add_argument('--log-file',
                            dest     = 'log_file',
                            type     = str,
                            nargs    = 1,
                            metavar  = 'LOG_FILE',
                            default  = None,
                            help     = "Print results to log file",
                            required = False),
        parser.add_argument('--log-only',
                            dest     = 'log_only',
                            action   = 'store_true',
                            help     = "Print results to log file only.",
                            required = False)
        parser.add_argument('--verbose',
                            dest     = 'verbose',
                            action   = 'store_true',
                            help     = "Verbose printing",
                            required = False)
        parser.add_argument('--silent',
                            dest     = 'silent',
                            action   = 'store_true',
                            help     = "No printing",
                            required = False)
        self.parser = parser

    def get_parsed_arguments(self):
        """
        Get arguments; if input and output names are missing, guess them
        (only guess with the --force option, otherwise don't run).
        """
        args = self.parser.parse_args(self.argv)
        config_path = args.config[0] if args.config else CONFIG_BASENAME
        if args.config and not path.isfile(config_path):
            raise IOError("Please check the config file exists:" + config_path)
        config = flatten_config(load_config_file(config_path))
        self.apply_config_defaults(args, config)

        if args.annotate and args.remove_annotations:
            raise ValueError("Use either --annotate or --remove-annotations, not both.")
        if args.input and args.input_dir:
            raise ValueError("Use either --input or --input-dir, not both.")

        if args.template is None and args.input and len(args.input) > 1:
            args.template = args.input[-1]
            args.input = args.input[:-1]

        if args.template is not None and args.input is None and args.input_dir is None and not args.remove_annotations:
            default_input_dir = path.join(path.dirname(path.abspath(args.template)), 'tables')
            if path.isdir(default_input_dir):
                args.input_dir = [default_input_dir]

        missing_args  = []
        missing_args += ['TEMPLATE'] if args.template is None else []
        missing_args += ['INPUT'] if not args.input and args.input_dir is None and not args.remove_annotations else []
        if self.command == 'fill':
            missing_args += ['OUTPUT'] if args.output is None else []
        if missing_args != []:
            if not args.force or 'TEMPLATE' in missing_args:
                isare = ' is ' if len(missing_args) == 1 else ' are '
                missing_args_msg   = ' and '.join(missing_args)
                missing_args_msg  += isare + 'missing without --force option.'
                raise KeyError(missing_args_msg)
            else:
                template_name = path.basename(args.template)
                if 'INPUT' in missing_args:
                    args.input = self.rename_file(template_name,
                                                  '_table', 'txt')
                if 'OUTPUT' in missing_args:
                    suffix = '_filled'
                    if args.annotate:
                        suffix = '_annotated'
                    elif args.remove_annotations:
                        suffix = '_clean'
                    args.output = self.rename_file(template_name, suffix)

        self.args = args

    def cli_option_present(self, *options):
        return any(option in self.argv for option in options)

    def apply_config_defaults(self, args, config):
        if not config:
            return

        if args.template is None and config.get('template') is not None:
            args.template = str(config['template'])
        if args.input is None and config.get('input') is not None:
            args.input = [str(value) for value in as_list(config['input'])]
        if args.input_dir is None and config.get('input_dir') is not None:
            args.input_dir = [str(config['input_dir'])]
        if args.output is None and config.get('output') is not None:
            args.output = [str(config['output'])]
        if not self.cli_option_present('-t', '--type') and config.get('filetype') is not None:
            args.filetype = [str(config['filetype'])]
        if not self.cli_option_present('--pvals') and config.get('pvals') is not None:
            args.pvals = [str(value) for value in as_list(config['pvals'])]
        if not self.cli_option_present('--stars') and config.get('stars') is not None:
            args.stars = [str(value) for value in as_list(config['stars'])]
        if not self.cli_option_present('--na-filters') and config.get('nafilters') is not None:
            args.nafilters = [str(value) for value in as_list(config['nafilters'])]

        for attr, option in [
            ('force', '--force'),
            ('compile', '--compile'),
            ('bibtex', '--bibtex'),
            ('fill_comments', '--fill-comments'),
            ('annotate', '--annotate'),
            ('remove_annotations', '--remove-annotations'),
            ('no_header', '--no-header'),
            ('ignore_xml', '--ignore-xml'),
            ('legacy_parsing', '--legacy-parsing'),
            ('numpy_syntax', '--numpy-syntax'),
            ('use_floats', '--use-floats'),
            ('log_only', '--log-only'),
            ('verbose', '--verbose'),
            ('silent', '--silent'),
        ]:
            if not self.cli_option_present(option) and config.get(attr) is not None:
                setattr(args, attr, bool(config[attr]))

        if args.xml_tables is None and config.get('xml_tables') is not None:
            args.xml_tables = [str(value) for value in as_list(config['xml_tables'])]
        if args.log_file is None and config.get('log_file') is not None:
            args.log_file = [str(config['log_file'])]

    def rename_file(self, base, add, ext = None):
        out  = path.splitext(base)
        add += out[-1] if ext is None else '.' + ext
        return [out[0] + add]

    def get_argument_strings(self):
        """
        Get arguments as strings to pass to StableFill.
        """
        self.template  = path.abspath(self.args.template)
        self.input     = '' if self.args.input is None else ' '.join([path.abspath(f) for f in self.args.input])
        self.input_dir = None if self.args.input_dir is None else path.abspath(self.args.input_dir[0])
        self.output    = None if self.args.output is None else path.abspath(self.args.output[0])
        self.silent    = self.args.silent
        self.verbose   = self.args.verbose and not self.args.silent
        self.stars     = self.args.stars
        self.nafilters = self.args.nafilters
        self.fillc     = self.args.fill_comments
        self.annotate  = self.args.annotate
        self.remove_annotations = self.args.remove_annotations
        self.nohead    = self.args.no_header
        self.log_file  = self.args.log_file[0] if self.args.log_file else None
        self.log_only  = self.args.log_only
        self.legacy_parsing = self.args.legacy_parsing
        self.numpy_syntax   = self.args.numpy_syntax
        self.use_floats     = self.args.use_floats
        self.ignore_xml     = self.args.ignore_xml
        self.xml_tables     = self.args.xml_tables
        try:
            self.pvals = [float(p) for p in self.args.pvals]
            assert all([(0 < p < 1) for p in self.pvals])
        except:
            raise ValueError("--pvals only takes numbers between 0 and 1")

        args_msg  = linesep + "I found these arguments:"
        args_msg += linesep + "template = %s" % self.template
        args_msg += linesep + "input    = %s" % self.input
        args_msg += linesep + "input_dir = %s" % self.input_dir
        args_msg += linesep + "output   = %s" % self.output
        args_msg += linesep
        print_verbose(self.verbose, args_msg)

    def get_file_type(self):
        fname = path.basename(self.template)
        ext   = path.splitext(fname)[-1].lower().strip('. ')
        inext = self.args.filetype[0].lower()
        if inext not in ['auto', 'tex', 'lyx', 'md', 'markdown']:
            unknown_type = "Type '%s' not allowed. Expected {auto,lyx,tex}."
            unknown_type = unknown_type % inext
            raise KeyError(unknown_type)
        elif inext == 'auto':
            if ext not in ['tex', 'lyx', 'md', 'markdown']:
                unknown_type  = "File type '%s' not known."
                unknown_type += " Expecting .lyx, .tex, or .md file."
                unknown_type = unknown_type % ext
                raise KeyError(unknown_type)
            else:
                if ext in ['md', 'markdown']:
                    self.ext = 'md'
                else:
                    self.ext = ext.lower()
                logmsg = "NOTE: Automatically detected input type as %s" % ext
                print_verbose(self.verbose, logmsg)
        else:
            self.ext = inext
            if ext != inext:
                mismatch_msg  = "NOTE: Provided template type '%s' "
                mismatch_msg += "does not match detected template type '%s'. "
                mismatch_msg += linesep + "Using program associated with '%s'"
                mismatch_msg  = mismatch_msg % (inext, ext, inext)
                print_verbose(self.verbose, mismatch_msg + linesep)

    def get_compiled(self):
        """
        Compile the filled template with the corresponding program.
        """

        if not self.args.compile and self.args.bibtex:
            print("NOTE: Cannot run BiBTeX without compiling." + linesep)

        if self.args.compile:
            chdir(path.dirname(path.abspath(self.output)))
            compile_program  = self.compiler[self.ext]
            compile_program += ' ' + self.output

            bibtex_auxfile   = path.splitext(path.basename(self.output))[0]
            bibtex_program   = self.bibtex[self.ext]
            bibtex_program  += ' ' + bibtex_auxfile + '.aux'

            logmsg = "Compiling in beta! Use with caution. Running"
            print_verbose(self.verbose, logmsg)
            print_verbose(self.verbose, compile_program + linesep)
            system(compile_program + linesep)
            if self.args.bibtex:
                system(bibtex_program + linesep)
                system(compile_program + linesep)
                system(compile_program + linesep)


# ---------------------------------------------------------------------
# StableFill engine internals

class StableFillEngine:
    """
    WARNING: Internal class used by StableFill.
    """
    def __init__(self,
                 filetype       = 'auto',
                 verbose        = True,
                 silent         = False,
                 pvals          = [0.1, 0.05, 0.01],
                 stars          = ['*', '**', '***'],
                 nafilters      = ['.', '', 'NA', 'nan', 'NaN', 'NaN+0i', 'None', 'Inf', 'INF'],
                 fillc          = False,
                 nohead         = False,
                 legacy_parsing = False,
                 numpy_syntax   = False,
                 use_floats     = False,
                 ignore_xml     = False,
                 xml_tables     = None,
                 annotate       = False,
                 remove_annotations = False):

        # Get file type
        self.filetype     = filetype.lower()
        if self.filetype not in ['auto', 'lyx', 'tex', 'md']:
            unknown_type  = "File type '%s' not known."
            unknown_type += " Expecting 'auto' or a .lyx, .tex, or .md file."
            unknown_type  = unknown_type % filetype
            raise KeyError(unknown_type)

        self.warn_msg  = {'nomatch': '',
                          'notable': '',
                          'nolabel': '',
                          'toolong': '',
                          'inline': ''}
        self.warnings  = {'nomatch': [],
                          'notable': [],
                          'nolabel': [],
                          'toolong': [],
                          'inline': []}
        self.warn_pre  = ""
        self.verbose   = verbose and not silent
        self.silent    = silent

        while len(pvals) > len(stars):
            i = 1
            while '*' * i in stars:
                i += 1
            stars += ['*' * i]

        stars               = stars[:len(pvals)]
        starlist            = [(p, s) for (p, s) in zip(pvals, stars)]
        starlist.sort(key = lambda p: p[0], reverse = True)
        self.pvals          = [p for (p, s) in starlist]
        self.stars          = [s for (p, s) in starlist]
        self.nafilters      = nafilters
        self.fillc          = fillc
        if annotate and remove_annotations:
            raise ValueError("Use either annotate or remove_annotations, not both.")

        self.annotate       = annotate
        self.remove_annotations = remove_annotations
        self.nohead         = nohead or annotate or remove_annotations
        self.legacy_parsing = legacy_parsing
        self.numpy_syntax   = numpy_syntax
        self.use_floats     = use_floats
        self.ignore_xml     = ignore_xml
        self.xml_tables     = xml_tables
        self._warned_deprecated_xml = False

    def warn_deprecated_xml(self):
        if self._warned_deprecated_xml:
            return
        self._warned_deprecated_xml = True
        warnings.warn(
            "Custom XML/Python table generation is deprecated and will be removed "
            "in a future StableFill release. Prefer explicit input tables and "
            "future derived-value configuration support.",
            FutureWarning,
            stacklevel=3,
        )

    def get_parsed_arguments(self, kwargs, require_output=True):
        """
        Gets template, input, and output from kwargs with checks for
            - All arguments are there as strings
            - All files exist
            - Output directory exists and is writable
        """
        args = ['template']
        if require_output:
            args += ['output']
        has_input = 'input' in kwargs and kwargs.get('input')
        has_input_dir = 'input_dir' in kwargs and kwargs.get('input_dir')
        if has_input and has_input_dir:
            raise ValueError("Use either input or input_dir, not both.")
        if not self.remove_annotations and not has_input and not has_input_dir:
            args += ['input']

        # XX
        missing_args = list(filter(lambda arg: arg not in kwargs.keys() or not kwargs.get(arg), args))
        if missing_args != []:
            template_for_default = kwargs.get('template')
            default_input_dir = None
            if not self.remove_annotations and template_for_default is not None:
                default_input_dir = path.join(path.dirname(path.abspath(template_for_default)), 'tables')
            if 'input' in missing_args and default_input_dir and path.isdir(default_input_dir):
                kwargs['input_dir'] = default_input_dir
                missing_args.remove('input')
                has_input_dir = True
            if missing_args != []:
                isare = " is " if len(missing_args) == 1 else " are "
                missing_args_msg  = " and ".join(missing_args)
                missing_args_msg += isare + "missing. Check function call."
                raise KeyError(missing_args_msg)

        # XX
        m = filter(lambda t: not isinstance(t[1], basestring), kwargs.items())
        mismatched_types = list(m)
        if mismatched_types != []:
            msg = "Expected str for '%s' but got type '%s'"
            msg = [msg % (k, v.__class__.__name__)
                   for k, v in mismatched_types]
            mismatched_msg = linesep.join(msg)
            raise TypeError(mismatched_msg)

        self.template = path.abspath(kwargs['template'])
        self.output   = path.abspath(kwargs['output']) if kwargs.get('output') else None
        self.input = []
        if not self.remove_annotations:
            if kwargs.get('input_dir'):
                self.input = self.discover_input_files(kwargs['input_dir'])
            else:
                self.input = [path.abspath(ins) for ins in kwargs['input'].split()]

        infiles = [self.template] + self.input
        missing_files = list(filter(lambda f: not path.isfile(f), infiles))
        if missing_files != []:
            missing_files_msg  = "Please check the following are available:"
            missing_files_msg += linesep + linesep.join(missing_files)
            raise IOError(missing_files_msg)

        if self.output is not None:
            outdir = path.split(self.output)[0]
            missing_path = not path.isdir(outdir)
            if missing_path:
                missing_outdir_msg  = "Please check the directory exists:"
                missing_outdir_msg += outdir
                raise IOError(missing_outdir_msg)

            cannot_write = not access(outdir, W_OK)
            if cannot_write:
                cannot_write_msg  = "Please check you have write access to: "
                cannot_write_msg += outdir
                raise IOError(cannot_write_msg)

    def discover_input_files(self, input_dir):
        """
        Return .txt input files from a directory in deterministic order.
        """
        input_dir = path.abspath(input_dir)
        if not path.isdir(input_dir):
            raise IOError("Please check the input directory exists:" + input_dir)

        inputs = []
        for filename in sorted(listdir(input_dir)):
            full = path.join(input_dir, filename)
            if path.isfile(full) and path.splitext(filename)[-1].lower() == '.txt':
                inputs += [full]

        if inputs == []:
            raise IOError("No .txt input files found in input directory:" + input_dir)

        return inputs

    def get_file_type(self):
        """
        Get file type and check if it matches the compilation type that
        was requested, if one was requested.
        """
        fname = path.basename(self.template)
        ext   = path.splitext(fname)[-1].lower().strip('. ')
        inext = self.filetype
        if inext == 'auto':
            if ext not in ['tex', 'lyx', 'md', 'markdown']:
                unknown_type  = "Option filetype = 'auto' detected type '%s'"
                unknown_type += " but was expecting a .lyx or .tex file."
                unknown_type  = unknown_type % ext
                raise KeyError(unknown_type)
            else:
                if ext in ['md', 'markdown']:
                    self.filetype = 'md'
                else:
                    self.filetype = ext.lower()
                logmsg = "NOTE: Automatically detected input type as %s" % ext
                print_verbose(self.verbose, logmsg)
        elif ext != inext:
            mismatch_msg  = "NOTE: Provided template type '%s' "
            mismatch_msg += "does not match detected template type '%s'"
            mismatch_msg += linesep + "Will use program associated with '%s'"
            mismatch_msg  = mismatch_msg % (inext, ext, inext)
            print_verbose(self.verbose, mismatch_msg + linesep)

    def get_regexps(self):
        """
        Define the regular expressions to use to find a token to fill,
        the start/end of a table, etc. based on the file type.
        """
        patterns = PlaceholderPatterns()
        grammar = grammar_for_filetype(self.filetype)
        self.scanner = TemplateScanner(grammar, template=self.template)
        self.placeholder_formatter = PlaceholderFormatter(
            patterns,
            renderer_for_filetype(self.filetype),
            self.pvals,
            self.stars,
        )

        self.tags      = '^<Tab:(.+)>[\r\n' + linesep + ']'
        self.matche    = patterns.escape
        self.match0    = patterns.any_placeholder
        self.matcha    = patterns.raw_or_stars
        self.matchb    = patterns.numeric
        self.matchc    = patterns.integer_decimal
        self.matchd    = patterns.absolute
        self.matchf    = patterns.python_format
        self.matchg    = patterns.imaginary
        self.comments  = grammar.comment
        self.begin     = grammar.begin
        self.end       = grammar.end
        self.label     = grammar.label

    def get_parsed_tables(self):
        """
        Parse table file(s) into a dictionary with tags as keys and
        lists of table entries as values
        """

        # TODO: I cannot believe the case-insensitivity here (i.e. the lower)
        # TODO: is the cause of all the evil in the world.

        # Read in all the tables. The parser accepts the historical
        # tab-delimited format as well as whitespace-delimited rows, which is
        # common in regression output with coefficients and standard errors.
        parsed_inputs = parse_input_files(self.input, self.nafilters)
        ctables       = parsed_inputs.tables
        scalar_values = parsed_inputs.values
        self.input_sources = parsed_inputs.sources
        self.scalar_values = scalar_values

        if not self.ignore_xml:
            xml_input  = self.template if self.xml_tables is None else self.xml_tables
            xml_prefix = r'^%\s*' if self.xml_tables is None else ''
            if self.legacy_parsing:
                self.parse_xml_file_legacy(ctables, xml_input, prefix = xml_prefix)
            else:
                self.parse_xml_file(ctables, xml_input, prefix = xml_prefix)

        # Read in actual and custom tables
        # self.tables = {k: self.filter_missing(v) for k, v in tables.items()}
        self.tables = dict((k, self.filter_missing([x.strip() for x in flatten(v)]))
                           for (k, v) in ctables.items())
        self.inline_values = dict((k, v[0]) for (k, v) in self.tables.items()
                                  if len(v) > 0)
        self.inline_values.update(scalar_values)

    def get_inspection_report(self):
        """Describe what StableFill would fill without mutating files."""
        if version_info >= (3, 0):
            read_template = open(self.template, 'r').readlines()
        else:
            read_template = open(self.template, 'rU').readlines()

        table_report = self.inspect_template_tables(read_template)
        inline_report = self.inspect_inline_placeholders(read_template)
        used_table_keys = set(row['label'] for row in table_report
                              if row['label'] and row['placeholder_count'] > 0
                              and row['label'] in self.tables)
        used_inline_keys = set(row['key'] for row in inline_report
                               if row['key'] in self.inline_values)
        scalar_values = getattr(self, 'scalar_values', {})
        unused_tables = sorted(set(self.tables.keys()) - used_table_keys - used_inline_keys)
        unused_values = sorted(set(scalar_values.keys()) - used_inline_keys)

        lines = []
        lines += ['StableFill inspect', '']
        lines += ['Template:', '  %s' % self.template]
        if self.output is not None:
            lines += ['Output:', '  %s' % self.output]
        lines += ['', 'Input files:']
        lines += ['  %s' % filename for filename in self.input]
        lines += ['', 'Input tables:']
        if self.tables:
            for key in sorted(self.tables.keys()):
                source = getattr(self, 'input_sources', {}).get(key, '(derived or unknown source)')
                lines += ['  tab:%s: %d values from %s' % (key, len(self.tables[key]), source)]
        else:
            lines += ['  (none)']

        lines += ['', 'Named values:']
        if scalar_values:
            for key in sorted(scalar_values.keys()):
                source = getattr(self, 'input_sources', {}).get(key, '(unknown source)')
                lines += ['  val:%s: %s from %s' % (key, scalar_values[key], source)]
        else:
            lines += ['  (none)']

        lines += ['', 'Template tables:']
        if table_report:
            for row in table_report:
                lines += ['  line %d: %s' % (row['start_line'], row['summary'])]
        else:
            lines += ['  (no table regions detected)']

        lines += ['', 'Inline placeholders:']
        if inline_report:
            for row in inline_report:
                lines += ['  line %d: {{%s}} -> %s' % (row['line'], row['raw_key'], row['status'])]
        else:
            lines += ['  (none)']

        lines += ['', 'Unused input:']
        lines += ['  tables: %s' % (', '.join('tab:%s' % key for key in unused_tables) or '(none)')]
        lines += ['  values: %s' % (', '.join('val:%s' % key for key in unused_values) or '(none)')]
        return linesep.join(lines)

    def inspect_template_tables(self, lines):
        reports = []
        table_start = -1
        current = None
        for index, line in enumerate(lines):
            if table_start == -1 and self.scanner.is_table_start(line):
                result = self.scanner.search_label(lines, index, self.tables.keys())
                table_start = index
                current = {
                    'start_line': index + 1,
                    'label': result.tag,
                    'placeholder_count': 0,
                    'end_line': result.end_line,
                }

            countable = current is not None
            if countable and (not self.scanner.is_comment(line) or self.fillc):
                current['placeholder_count'] += self.count_table_placeholders(line)

            if current is not None and self.scanner.is_table_end(line):
                current['end_line'] = index + 1
                current['summary'] = self.summarize_table_inspection(current)
                reports += [current]
                table_start = -1
                current = None

        if current is not None:
            current['summary'] = self.summarize_table_inspection(current)
            reports += [current]
        return reports

    def count_table_placeholders(self, line):
        count = 0
        for pattern in self.placeholder_formatter.patterns.active_patterns():
            count += len(list(re.finditer(pattern, line)))
        return count

    def summarize_table_inspection(self, row):
        label = row['label']
        placeholders = row['placeholder_count']
        if not label:
            return 'unlabeled table, skipped'
        if placeholders == 0:
            return 'tab:%s: ignored, no StableFill table placeholders' % label
        if label not in self.tables:
            return 'tab:%s: MISSING INPUT for %d placeholders' % (label, placeholders)

        available = len(self.tables[label])
        if available < placeholders:
            return 'tab:%s: TOO FEW VALUES, %d available for %d placeholders' % (
                label,
                available,
                placeholders,
            )
        if available > placeholders:
            return 'tab:%s: OK, %d placeholders; %d extra input values' % (
                label,
                placeholders,
                available - placeholders,
            )
        return 'tab:%s: OK, %d placeholders and %d input values' % (
            label,
            placeholders,
            available,
        )

    def inspect_inline_placeholders(self, lines):
        report = []
        for line_number, line in enumerate(lines, start=1):
            for match in INLINE_RE.finditer(line):
                raw_key = match.group('name').strip()
                key = normalize_key(raw_key)
                if key in self.inline_values:
                    status = 'OK (%s)' % self.format_inline_value(
                        self.inline_values[key],
                        match.group('format').strip() if match.group('format') else None,
                    )
                else:
                    status = 'MISSING INPUT'
                report += [{
                    'line': line_number,
                    'raw_key': raw_key,
                    'key': key,
                    'status': status,
                }]
        return report

    def parse_xml_file(self, ctables, xml_input, prefix = ''):
        r"""Parse custom tabs in comments/XML files

        Note that the parsing here is VERY crude (you will note it uses
        a combination of XML parsing and regexes). This is more or less
        intentional, since I want to be inflexible when using this
        feature as it is VERY experimental. As it becomes stable the
        function may move to proper XML parsing.

        Args:
            ctables (dict): Dictionary with input tables
            xml_input (list): Template or XML files with custom tags

        Kwargs:
            prefix (str): regex with prefix for XML parsing (if parsing
                          from template comments, this should be a LaTeX
                          comment, e.g. '^%\s*', as the tables would be
                          commented out in the file).

        Returns: Dictionary with resulting custom tables

        """

        # Read in all the custom tables
        xml_list     = tolist(xml_input)
        xml_toparse  = concat_files(xml_list)

        xml_regex  = prefix
        xml_regex += r"<tablefill-python\s+tag\s*=\s*['\"](.+)\s*['\"]"

        # Figure out where the custom XML tags are
        i = 0
        custom = []
        for line in xml_toparse:
            s = re.search(xml_regex, line)
            if s:
                j = i
                search = True
                while search and j < len(xml_toparse):
                    if re.search(r'</\s*tablefill-python\s*>', xml_toparse[j]):
                        search = False
                    j += 1

                if not search:
                    custom += [range(i, j)]

            i += 1

        # Prase each custom XMl tag into a dictionary
        cdict = {}
        for c in custom:
            chtml    = []
            cobj     = itemgetter(*c)(xml_toparse)
            for obj in cobj:
                chtml += [re.sub(r'^%\s*', '', obj)]

            try:
                cxml = xml.fromstringlist(chtml)
            except:
                xml_parse_msg = "Could not parse custom XML in lines %d-%d."
                raise Warning('\t' + xml_parse_msg % (c[0], c[-1]))

            t = cxml.get('tag')
            cdict[t] = cxml

        if cdict == {}:
            return

        self.warn_deprecated_xml()

        # Get temporary string and numeric dictionaries
        strdict = ctables
        numdict = {}
        for tag, table in ctables.items():
            numdict[tag] = nested_convert(table, float)

        numpy_strdict = {}
        numpy_numdict = {}
        if numpyok:
            for tag, table in strdict.items():
                numpy_strdict[tag] = numpy.asmatrix(table)

            for tag, table in numdict.items():
                numpy_numdict[tag] = numpy.asmatrix(table)

        # Create all the custom tables using python/numpy slicing
        print_verbose(self.verbose, linesep + "Creating custom tables")
        for tag, cxml in cdict.items():
            print_verbose(self.verbose, "\ttab:%s" % (tag))

            csyntax = cxml.get('syntax')
            if csyntax not in [None, 'python', 'numpy']:
                xml_syntax_msg  = "Custom table '%s' requested unknown syntax"
                xml_syntax_msg += " '%s'. Specify 'python' or 'numpy'."
                raise Warning('\t' + xml_syntax_msg % (tag, csyntax))

            usenumpy = self.numpy_syntax and not csyntax == 'python'
            usenumpy = usenumpy or (csyntax == 'numpy')
            if usenumpy and not numpyok:
                xml_numpy_msg  = "Custom table '%s' requested syntax 'numpy'"
                xml_numpy_msg += " but python failed to import numpy."
                raise Warning('\t' + xml_numpy_msg % tag)

            usetype = 'float' if self.use_floats else cxml.get('type')
            if usetype not in [None, 'float', 'numeric', 'str', 'string']:
                xml_usetype_msg  = "Custom table '%s' asked unknown type"
                xml_usetype_msg += " '%s'. Specify 'float' or 'str'."
                raise Warning('\t' + xml_usetype_msg % (tag, usetype))

            if usetype in ['float', 'numeric']:
                usedict = numpy_numdict if numpyok and usenumpy else numdict
            else:
                usedict = numpy_strdict if numpyok and usenumpy else strdict

            if numpyok and usenumpy:
                usedict.update({'numpy': numpy})

            addok = False
            try:
                clean_text = re.subn(r'\s|' + linesep, '', cxml.text)[0]
                print_verbose(self.verbose, "\t\t%s" % clean_text)
                ceval = eval(clean_text, usedict)

                if numpyok and usenumpy:
                    if usetype in ['float', 'numeric']:
                        numpy_numdict[tag] = ceval
                    else:
                        numpy_strdict[tag] = ceval

                    ceval = tolist2(ceval)
                    toadd = list(flatten([numpy.array([l]) for l in ceval]))
                    strdict[tag] = nested_convert(toadd, str)
                    numdict[tag] = nested_convert(toadd, float)
                    addok = True

                else:
                    ceval = tolist2(ceval)
                    toadd = list(flatten(ceval))
                    strdict[tag] = nested_convert(ceval, str)
                    numdict[tag] = nested_convert(ceval, float)
                    if numpyok:
                        numpy_strdict[tag] = numpy.asmatrix(strdict[tag])
                        numpy_numdict[tag] = numpy.asmatrix(numdict[tag])

                    addok = True
            except Exception:
                warn_custom = "custom 'tab:%s' failed to parse." % tag
                print_verbose(self.verbose, '\t' + warn_custom)
                print_verbose(self.verbose, sys.exc_info()[2])

            if numpyok and usenumpy:
                usedict.pop('numpy')

            if addok:
                ctables[tag] = list(nested_convert(toadd, str))

    def parse_xml_file_legacy(self, ctables, xml_input, prefix = ''):
        r"""Parse custom tabs in comments/XML files

        Note that the parsing here is VERY crude (you will note it uses
        a combination of XML parsing and regexes). This is more or less
        intentional, since I want to be inflexible when using this
        feature as it is VERY experimental. As it becomes stable the
        function may move to proper XML parsing.

        Args:
            ctables (dict): Dictionary with input tables
            xml_input (list): Template or XML files with custom tags

        Kwargs:
            prefix (str): regex with prefix for XML parsing (if parsing
                          from template comments, this should be a LaTeX
                          comment, e.g. '^%\s*', as the tables would be
                          commented out in the file).

        Returns: Dictionary with resulting custom tables

        """

        # Read in all the custom tables
        xml_list     = tolist(xml_input)
        xml_toparse  = concat_files(xml_list)

        xml_regex  = prefix
        xml_regex += r"<tablefill-(custom|python)\s+tag\s*=\s*['\"](.+)\s*['\"]"

        # Figure out where the custom XML tags are
        i = 0
        custom = []
        todo   = []
        for line in xml_toparse:
            s = re.search(xml_regex, line)
            if s:
                j = i
                w = s.groups()[0]
                todo  += [w]
                search = True
                while search and j < len(xml_toparse):
                    if re.search(r'</\s*tablefill-%s\s*>' % w, xml_toparse[j]):
                        search = False
                    j += 1

                if not search:
                    custom += [range(i, j)]

            i += 1

        # Put them into a dictionary
        cdict = {}
        edict = {}
        for c, e in zip(custom, todo):
            chtml    = []
            cobj     = itemgetter(*c)(xml_toparse)
            for obj in cobj:
                chtml += [re.sub(r'^%\s*', '', obj)]

            try:
                cxml = xml.fromstringlist(chtml)
            except:
                xml_parse_msg  = "Could not parse custom XML in lines %d-%d."
                raise Warning('\t' + xml_parse_msg % (c[0], c[-1]))

            t = cxml.get('tag')
            cdict[t] = cxml
            edict[t] = e

        # Create all the custom tables using python/numpy slicing
        if cdict != {}:
            self.warn_deprecated_xml()

        for tag, cxml in cdict.items():
            print_verbose(self.verbose, "\tcreating custom tab:%s" % (tag))

            csyntax = cxml.get('syntax')
            if csyntax not in [None, 'python', 'numpy']:
                xml_syntax_msg  = "Custom table '%s' requested unknown syntax"
                xml_syntax_msg += " '%s'. Specify 'python' or 'numpy'."
                raise Warning('\t' + xml_syntax_msg % (tag, csyntax))

            usenumpy = self.numpy_syntax and not csyntax == 'python'
            usenumpy = usenumpy or (csyntax == 'numpy')
            if usenumpy and not numpyok:
                xml_numpy_msg  = "Custom table '%s' requested syntax 'numpy'"
                xml_numpy_msg += " but python failed to import numpy."
                raise Warning('\t' + xml_numpy_msg % tag)

            convert = 'float' if self.use_floats else cxml.get('convert')
            if convert not in [None, 'float', 'str']:
                xml_convert_msg  = "Custom table '%s' asked unknown conversion"
                xml_convert_msg += " '%s'. Specify 'float' or 'str'."
                raise Warning('\t' + xml_convert_msg % (tag, convert))

            if edict[tag] == 'python':
                inputs  = [l.strip() for l in cxml.get('inputs').split(',')]
                inputs  = list(filter(lambda a: a != '', inputs))
                xmlexec = mktemp()
                with open(xmlexec, "w+") as tmp:
                    tmp.writelines(cxml.text)

                python = {}
                for table in inputs:
                    ptable = tolist(ctables[table])
                    if convert == 'float':
                        ptable = nested_convert(ptable, float)

                    if numpyok and usenumpy:
                        ptable = numpy.asmatrix(ptable)

                    python[table] = ptable

                try:
                    execfile(xmlexec, python)
                except:
                    xml_python_msg = "Custom code for '%s' failed to run."
                    raise Warning('\t' + xml_python_msg % tag)

                remove(xmlexec)
                try:
                    table_tag = python[tag]
                except:
                    xml_python_msg = "Code for '%s' did not create 'tag'"
                    raise Warning('\t' + xml_python_msg % tag)

                if numpyok and usenumpy:
                    table_tag = numpy.array(table_tag)

                table_tag = list(flatten(table_tag))
                if convert == 'float':
                    table_tag = nested_convert(table_tag, str)

                ctables[tag] = table_tag
            else:
                ctables[tag] = table_tag = []
                for combine in cxml.findall('combine'):
                    ctag  = combine.get('tag')
                    clist = ctables[ctag]
                    if numpyok and usenumpy:
                        clist = numpy.asmatrix(clist)

                    for subset in combine.text.split(';'):
                        clean_subset = subset.strip(linesep).replace(' ', '')
                        if clean_subset == '':
                            continue

                        try:
                            add = eval("clist%s" % (clean_subset))
                            if numpyok and usenumpy:
                                add = numpy.array(add)

                            table_tag += [add]
                        except:
                            warn_custom  = "custom 'tab:%s' failed to subset "
                            warn_custom += "'%s' from 'tab:%s'; will continue."
                            warn_msg = warn_custom % (tag, clean_subset, ctag)
                            print_verbose(self.verbose, warn_msg)
                            continue

                ctables[tag] = list(flatten(table_tag))

    def filter_missing(self, string_list):
        filters = self.nafilters
        return list(filter(lambda a: a not in filters, string_list))

    def get_filled_template(self):
        """
        Fill template file using table input(s). The idea is to read the
        template line by line and if the line matches the start of a
        table, search for the table label (to match to the input tags).

        If no label, print a note to that effect. If there is a label,
        grab the corresponding matrix from the inputs, and replace the
        tokens with the input values until the values run out or we
        reach the end of the table. Repeat for all template lines.

        This function raises warnings for
            - Token matched but in a commented out line.
            - Too many tokens in table and not enough values.
            - Token outside of begin/end table statement.
            - Table label does not match tag in inputs.
        """
        if version_info >= (3, 0):
            read_template = open(self.template, 'r').readlines()
        else:
            read_template = open(self.template, 'rU').readlines()
        if self.remove_annotations:
            self.filled_template = [strip_annotations(line) for line in read_template]
            return
        read_template, inline_warnings = replace_inline_placeholders(
            read_template,
            getattr(self, 'inline_values', {}),
            self.format_inline_value,
            annotate=self.annotate,
        )
        self.warnings['inline'] += inline_warnings
        table_start   = -1
        table_search  = False
        table_tag     = ''
        table_entry   = 0
        table_nomatch_warned = False

        warn = self.warn_pre
        for n in range(len(read_template)):
            line = read_template[n]
            if not table_search and self.scanner.is_table_start(line):
                table_search, table_tag = self.search_label(read_template, n)
                table_start  = n
                table_nomatch_warned = False
                search_msg   = self.get_search_msg(table_search, table_tag, n)
                print_verbose(self.verbose, search_msg)

            found = self.placeholder_formatter.has_placeholder(line)

            if found:
                if self.scanner.is_comment(line) and not self.fillc:
                    warn_incomments  = r"Line %d matches #(#|\d+,*|{.*})#"
                    warn_incomments += " but it appears to be commented out."
                    warn_incomments += " Skipping..."
                    print_verbose(self.verbose, warn + warn_incomments % n)
                elif table_search:
                    table  = self.tables[table_tag]
                    ntable = len(table)
                    try:
                        update = self.replace_line(line, table, table_entry,
                                                   line_number=n + 1,
                                                   table_tag=table_tag,
                                                   annotate=self.annotate)
                    except PlaceholderError as exc:
                        msg = "Could not fill template placeholder."
                        context = DiagnosticContext(file=self.template,
                                                    line=n + 1,
                                                    table=table_tag,
                                                    entry_index=table_entry + 1,
                                                    context=line.rstrip('\r\n'))
                        raise PlaceholderError(msg, context=context, cause=exc)
                    read_template[n], table_entry, entry_start = update
                    if ntable < table_entry:
                        self.warnings['toolong'] += [str(n)]

                        nstart        = entry_start + 1
                        nend          = table_entry
                        aux_toolong   = (n, nstart, nend, table_tag, ntable)

                        warn_toolong  = "Line %d has matches %d-%d for table"
                        warn_toolong += " %s but the corresponding input"
                        warn_toolong += " matrix only has %d entries."
                        warn_toolong += " Skipping..."
                        warn_toolong  = warn_toolong % aux_toolong

                        print_verbose(self.verbose, warn + warn_toolong)
                elif table_tag != '':
                    if not table_nomatch_warned:
                        self.warnings['nomatch'] += [table_tag]
                        table_nomatch_warned = True
                    print_verbose(self.verbose, warn + self.get_nomatch_msg(table_tag))
                elif table_start == -1:
                    self.warnings['notable'] += [str(n)]

                    warn_notable  = r"Line %d matches #(#|\d+,*|{.*})# but"
                    warn_notable += " is not in begin/end table statements."
                    warn_notable += " Skipping..."

                    print_verbose(self.verbose, warn + warn_notable % n)
                elif table_tag == '':
                    self.warnings['nolabel'] += [str(n)]
                    warn_nolabel  = r"Line %d matches #(#|\d+,*|{.*})#" % n
                    warn_nolabel += " but couldn't find " + self.label
                    warn_nolabel += " Skipping..."
                    print_verbose(self.verbose, warn + warn_nolabel)

            if self.scanner.is_table_end(line) and table_start != -1:
                if table_search:
                    search_msg   = "Table '%s' in line %d ended in line %d."
                    search_msg  += " %d replacements were made." % table_entry
                    search_msg   = search_msg % (table_tag, table_start, n)
                    print_verbose(self.verbose, search_msg + linesep)
                elif table_tag != '':
                    search_msg = "Table '%s' in line %d ended in line %d. Skipped."
                    print_verbose(self.verbose, (search_msg % (table_tag, table_start, n)) + linesep)

                table_start  = -1
                table_search = False
                table_tag    = ''
                table_entry  = 0
                table_nomatch_warned = False

        self.filled_template = read_template

    def search_label(self, intext, start):
        r"""
        Search for label in list 'intext' from position 'start' until an
        \end{table} statement. Returns label value ('' if none is found)
        and whether it matches a tag in the tables file
        """
        result = self.scanner.search_label(intext, start, self.tables.keys())
        return result.matched, result.tag

    def get_search_msg(self, search, tag, start):
        search_msg   = "Found table in line %d. " % start
        if tag == '':
            search_msg += "No label. Skipping..."
        else:
            search_msg += "Found label '%s'... " % tag
            if search:
                search_msg += "Found match!"
            else:
                search_msg += "No input match; will only warn if placeholders are found."

        return search_msg

    def get_nomatch_msg(self, tag):
        warn_nomatch  = "NO MATCHES FOR '%s' IN" + linesep + '\t'
        warn_nomatch += (linesep + '\t').join(self.input)
        warn_nomatch += linesep + "Please check input file(s)"

        return warn_nomatch % tag + linesep

    def escape_latex_entry(self, entry):
        """Escape unescaped LaTeX special characters in replacement text."""

        return self.placeholder_formatter.escape_entry(entry)

    def format_inline_value(self, entry, format_spec = None):
        """Render a ``{{name}}`` placeholder value.

        Inline values are intentionally simpler than sequential table
        placeholders. ``{{name}}`` uses the raw value, ``{{name|,.0f}}`` uses
        Python's format mini-language, and ``{{pvalue|*}}`` maps p-values to
        significance stars. Existing StableFill placeholder fragments such as
        ``{{name|#0,#}}`` are accepted for users who already know them.
        """
        return self.placeholder_formatter.format_inline_value(entry, format_spec)

    def replace_line(self, line, table, tablen, line_number=None, table_tag=None, annotate=False):
        r"""
        Replaces all matches of #(#|\d+,*|{.*})# in source order.
        The engine deliberately does not infer a rectangular shape from
        LaTeX columns, so ragged rows, multicolumn headers, and uneven
        placeholder counts are filled top-to-bottom, left-to-right.
        """
        return self.placeholder_formatter.replace_line(line,
                                                       table,
                                                       tablen,
                                                       template=self.template,
                                                       line_number=line_number,
                                                       table_tag=table_tag,
                                                       annotate=annotate)

    def get_notification_message(self):
        r"""
        Inserts a message atop the LaTeX file that this was created by
        StableFill. Includes the following warnings, when applicable:
            - #(#|\d+,*)# is found on a line outside a table environment
            - #(#|\d+,*)# is on a table environment with no label
            - A tabular environment's label has no match in tables.txt
        """
        n   = 0
        if self.filetype == 'tex':
            head  = 3 * [72 * '%' + linesep]
            tail  = head
            pre   = '% '
            after = linesep
        elif self.filetype == 'lyx':
            pre   = "\\begin_layout Plain Layout" + linesep
            after = "\\end_layout" + linesep
            head  = ["\\begin_layout Standard" + linesep]
            head += ["\\begin_inset Note Note" + linesep]
            head += ["status open" + linesep + linesep]
            tail  = ["\\end_inset" + linesep]
            tail += ["\\end_layout" + linesep]
            while not self.filled_template[n].startswith('\\begin_body'):
                n += 1
            n += 1
        elif self.filetype == 'md':
            pre   = ""
            after = linesep
            head  = ["<!-- "]
            tail  = [" -->", linesep, linesep]

        for key in self.warnings.keys():
            self.warnings[key] = ', '.join(self.warnings[key])

        self.warning = True in [v != '' for v in self.warnings.values()]
        if self.warning:
            fillt  = (self.template, self.input)
            fillh  = self.template
            fillt  = ("'template' file", "'input' file(s)")
            fillh  = "'template' file"
            imtags = "WARNING: These tags were in %s but not in %s: " % fillt
            imhead = "WARNING: Lines in %s matching '#(#|d+,*)#'" % fillh
            imend  = linesep + pre if self.filetype == 'tex' else '; '
            imend += "Output '%s' may not compile!" % self.output

        if self.warnings['nomatch'] != '':
            self.warn_msg['nomatch']  = imtags
            self.warn_msg['nomatch'] += self.warnings['nomatch'] + imend

        if self.warnings['notable'] != '':
            self.warn_msg['notable']  = imhead
            self.warn_msg['notable'] += " were not in a table environment: "
            self.warn_msg['notable'] += self.warnings['notable'] + imend

        if self.warnings['nolabel'] != '':
            self.warn_msg['nolabel']  = imhead
            self.warn_msg['nolabel'] += " but the environment had no label: "
            self.warn_msg['nolabel'] += self.warnings['nolabel'] + imend

        if self.warnings['toolong'] != '':
            self.warn_msg['toolong']  = imhead
            self.warn_msg['toolong'] += " but their corresponding input matrix"
            self.warn_msg['toolong'] += " ran out of entries: "
            self.warn_msg['toolong'] += self.warnings['toolong'] + imend

        if self.warnings['inline'] != '':
            self.warn_msg['inline']  = "WARNING: Some inline {{name}} "
            self.warn_msg['inline'] += "placeholders were not filled: "
            self.warn_msg['inline'] += self.warnings['inline'] + imend

        msg  = ["This file was produced by StableFill."]
        msg += ["\tTemplate file: %s" % self.template]
        msg += ["\tInput file(s): %s" % self.input]
        msg += ["To make changes, edit the input and template files."]
        msg += [pre + after]

        if self.warning:
            msg += ["THERE WAS AN ISSUE CREATING THIS FILE!"]
            msg += [s for s in self.warn_msg.values()]
        else:
            msg += ["DO NOT EDIT THIS FILE DIRECTLY."]

        if self.nohead:
            return

        msg = [pre + m + after for m in msg]
        self.filled_template[n:n] = head + msg + tail

    def write_to_output(self, text):
        outfile = open(self.output, 'w')
        outfile.write(''.join(text))
        outfile.close()

    def get_exit_message(self):
        if self.warning:
            msg  = ["The following issues were found:"]
            msg += list(filter(lambda wm: wm != '', self.warn_msg.values()))
            self.exit_msg = linesep.join(msg)
            self.exit     = 'WARNING'
        else:
            msg  = "All tags in '%s' successfully filled by StableFill"
            msg += linesep + "Output can be found in '%s'" + linesep
            self.exit_msg = msg % (self.template, self.output)
            self.exit     = 'SUCCESS'


class Logger(object):
    def __init__(self, log_file, log_only):
        self.log_only = log_only
        if not self.log_only:
            self.terminal = sys.stdout
        self.log = open(log_file, "w")

    def write(self, message):
        if not self.log_only:
            self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


# ---------------------------------------------------------------------
# Run the function

if __name__ == "__main__":
    main()
