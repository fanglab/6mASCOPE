
"""
bam2fasta zip file export with tmp dir support.  This module also contains
functionality shared with related tasks.
"""

import functools
import logging
import sys

from pbcommand.models import FileTypes, ResourceTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log

from pbcoretools.bam2fastx import run_bam_to_fasta

log = logging.getLogger(__name__)


class Constants(object):
    TOOL_ID = "pbcoretools.tasks.bam2fasta_archive"
    VERSION = "0.4.2"
    DRIVER = "python -m pbcoretools.tasks.bam2fasta_archive --resolved-tool-contract"
    FILE_TYPE = FileTypes.DS_SUBREADS
    FORMAT_NAME = "fasta"
    TOOL_NAME = "bam2fasta"
    READ_TYPE = "subreads"


def get_parser_impl(constants):
    fmt_name = constants.FORMAT_NAME
    p = get_pbparser(constants.TOOL_ID,
                     constants.VERSION,
                     "{t} export to ZIP".format(t=constants.TOOL_NAME),
                     __doc__,
                     constants.DRIVER,
                     is_distributed=True,
                     resource_types=(ResourceTypes.TMP_DIR,))
    p.add_input_file_type(constants.FILE_TYPE, "bam",
                          "Input {t}".format(t=constants.READ_TYPE),
                          "Input {i} XML".format(i=constants.FILE_TYPE.file_type_id))
    p.add_output_file_type(
        FileTypes.ZIP,
        "{f}_out".format(f=fmt_name),
        "{f} file(s)".format(f=fmt_name.upper()),
        description="Exported {f} as ZIP archive".format(f=fmt_name.upper()),
        default_name="{t}.{f}".format(t=constants.READ_TYPE, f=fmt_name))
    return p


def run_args_impl(f, args):
    out = args.fasta_out if hasattr(args, 'fasta_out') else args.fastq_out
    return f(args.bam, out)


def run_rtc_impl(f, rtc):
    return f(rtc.task.input_files[0], rtc.task.output_files[0],
             tmp_dir=rtc.task.tmpdir_resources[0].path)


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           get_parser_impl(Constants),
                           functools.partial(run_args_impl, run_bam_to_fasta),
                           functools.partial(run_rtc_impl, run_bam_to_fasta),
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
