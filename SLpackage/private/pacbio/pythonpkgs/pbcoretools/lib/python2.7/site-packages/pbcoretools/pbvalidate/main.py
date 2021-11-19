
"""
Utility for validating files produced by PacBio software against our own
internal specifications.
"""

from __future__ import absolute_import

from cStringIO import StringIO
from xml.dom import minidom
import warnings
import argparse
import logging
import os.path
import time
import re
import sys

from pbcommand.cli import (pbparser_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.models.parser import get_pbparser
from pbcommand.models import FileTypes
from pbcommand.utils import setup_log

from . import bam
from . import fasta
from . import dataset
from . import utils

__version__ = "0.6"

FASTA_EXTENSIONS = {".fasta", ".fa", ".fna", ".fsa"}


def get_parser(parser=None):
    if parser is None:
        parser = get_default_argparser_with_base_opts(
            version=__version__,
            description=__doc__,
            default_level="CRITICAL")
    parser.add_argument('file', help="BAM, FASTA, or DataSet XML file")
    parser.add_argument("--quick", dest="quick", action="store_true",
                        help="Limits validation to the first 100 records " +
                             "(plus file header); equivalent to " +
                             "--max-records=100")
    parser.add_argument("--max", dest="max_errors", action="store", type=int,
                        help="Exit after MAX_ERRORS have been recorded " +
                             "(DEFAULT: check entire file)")
    parser.add_argument("--max-records", dest="max_records", action="store",
                        type=int,
                        help="Exit after MAX_RECORDS have been inspected " +
                             "(DEFAULT: check entire file)")
    parser.add_argument("--type", dest="file_type", action="store",
                        choices=["BAM", "Fasta"] + dataset.DatasetTypes.ALL,
                        help="Use the specified file type instead of guessing")
    parser.add_argument("--index", dest="validate_index", action="store_true",
                        help="Require index files (.fai or .pbi)")
    parser.add_argument("--strict", dest="strict", action="store_true",
                        help="Turn on additional validation, primarily for " +
                             "DataSet XML")
    parser.add_argument("-x", "--xunit-out", dest="xunit_out", action="store",
                        default=None, help="Xunit test results for Jenkins")
    parser.add_argument("--alarms", dest="alarms_out", action="store",
                        default=None, help="alarms.json for errors")
    g1 = parser.add_argument_group('bam', "BAM options")
    g2 = parser.add_argument_group('fasta', "Fasta options")
    bam.get_format_specific_args(g1)
    fasta.get_format_specific_args(g2)
    return parser


def get_parser_tc():
    p = get_pbparser("pbcoretools.tasks.pbvalidate", "0.1.0", "pbvalidate",
                     "Run pbvalidate on SubreadSet",
                     "python -m pbcoretools.pbvalidate.main --resolved-tool-contract",
                     is_distributed=True, nproc=1, default_level="WARN")
    p.tool_contract_parser.add_input_file_type(FileTypes.DS_SUBREADS,
                                               "subreads",
                                               name="SubreadSet",
                                               description="PacBio Subread DataSet XML")
    p.tool_contract_parser.add_output_file_type(FileTypes.XML, "junit_report",
                                                name="JUnit Report", description="JUnit Report",
                                                default_name="tests_junit")
    get_parser(p.arg_parser.parser)
    return p


class run_validator (object):

    def __init__(self, args, out=sys.stdout, save_exit_code=False):
        if not os.path.isfile(args.file):
            raise IOError("Not a file: %s" % args.file)
        if args.quiet:
            warnings.simplefilter("ignore")
        self.file_name = args.file
        self.silent = args.xunit_out is not None and not save_exit_code
        base, ext = os.path.splitext(args.file)
        if ext == ".gz":
            ext_ = ext
            base, ext = os.path.splitext(base)
        if args.quiet:
            out = StringIO()
        self.t_start = time.time()
        if (args.file_type == "Fasta" or
                (args.file_type is None and ext in FASTA_EXTENSIONS)):
            self.errors, self.metrics = fasta.validate_fasta(
                file_name=args.file,
                strict=args.strict,
                validate_index=args.validate_index,
                quick=args.quick)
        elif (args.file_type == "BAM" or
              (args.file_type is None and ext in [".bam"])):
            self.errors, self.metrics = bam.validate_bam(
                file_name=args.file,
                reference=args.reference,
                aligned=args.aligned,
                contents=args.contents,
                quick=args.quick,
                max_errors=args.max_errors,
                max_records=args.max_records,
                validate_index=args.validate_index)
        elif (args.file_type in ["AlignmentSet", "ReferenceSet", "SubreadSet"] or
              ext in [".xml"]):
            self.errors, self.metrics = dataset.validate_dataset(
                file_name=args.file,
                dataset_type=args.file_type,
                reference=args.reference,
                quick=args.quick,
                max_errors=args.max_errors,
                max_records=args.max_records,
                aligned=args.aligned,
                contents=args.contents,
                validate_index=args.validate_index,
                strict=args.strict)
        else:
            raise NotImplementedError("No validator found for '%s'." % ext)
        self.t_end = time.time()
        if not args.quiet:
            utils.show_validation_errors(self.errors, out=out)
        if args.alarms_out:
            utils.dump_alarms_json(self.errors, args.alarms_out)
        if args.xunit_out is not None:
            doc = self.to_xml()
            with open(args.xunit_out, "w") as xml_out:
                xml_out.write(doc.toprettyxml(indent="  "))

    @property
    def time(self):
        return self.t_end - self.t_start

    @property
    def n_errors(self):
        return len(self.errors)

    @property
    def return_code(self):
        if self.silent:
            return 0
        return min(1, self.n_errors)

    @property
    def error_string(self):
        err_out = StringIO()
        utils.show_validation_errors(self.errors, out=err_out)
        return err_out.getvalue()

    def to_xml(self):
        doc = minidom.Document()
        root = doc.createElement("testsuite")
        doc.appendChild(root)
        root.setAttribute("errors", "0")
        root.setAttribute("name", "pbvalidate")
        root.setAttribute("skips", "0")
        root.setAttribute("time", str(self.time))
        n_failed = 0
        for e, n in utils.iter_non_redundant_errors(self.errors):
            testcase = doc.createElement("testcase")
            testcase.setAttribute("classname", e.__class__.__name__)
            fn_fields = re.sub("/", "_", self.file_name)
            testcase.setAttribute("name", "test_%s" % fn_fields)
            testcase.setAttribute("time", str(self.time))
            failure = doc.createElement("failure")
            msg = str(e)
            if n > 1:
                msg += "(%d similar errors not shown)" % (n-1)
            failure.setAttribute("message", msg)
            failure.appendChild(doc.createCDATASection(str(e.object_ref)))
            testcase.appendChild(failure)
            root.appendChild(testcase)
            n_failed += 1
        root.setAttribute("tests", str(n_failed))
        root.setAttribute("failures", str(n_failed))
        return doc


def run(*args, **kwds):
    return run_validator(*args, **kwds).return_code


def run_rtc(rtc):
    argv = [
        rtc.task.input_files[0],
        "--type", "SubreadSet",
        "--index", "--quick",
        # FIXME we should use --strict, but pyxb is a pain
        "--xunit-out", rtc.task.output_files[0]
    ]
    p = get_parser()
    args = p.parse_args(argv)
    return run_validator(args, save_exit_code=True).return_code


def main(argv=sys.argv):
    return pbparser_runner(
        argv=argv[1:],
        parser=get_parser_tc(),
        args_runner_func=run,
        contract_runner_func=run_rtc,
        alog=logging.getLogger(),
        setup_log_func=setup_log)


if __name__ == "__main__":
    sys.exit(main())
