
"""
bam2fastq zip file export with tmp dir support
"""

import functools
import logging
import sys

from pbcommand.models import FileTypes
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log

from pbcoretools.bam2fastx import run_bam_to_fastq
from pbcoretools.tasks.bam2fasta_archive import (
    get_parser_impl, run_args_impl, run_rtc_impl)

log = logging.getLogger(__name__)


class Constants(object):
    TOOL_ID = "pbcoretools.tasks.bam2fastq_archive"
    VERSION = "0.4.2"
    DRIVER = "python -m pbcoretools.tasks.bam2fastq_archive --resolved-tool-contract"
    FILE_TYPE = FileTypes.DS_SUBREADS
    FORMAT_NAME = "fastq"
    TOOL_NAME = "bam2fastq"
    READ_TYPE = "subreads"


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           get_parser_impl(Constants),
                           functools.partial(run_args_impl, run_bam_to_fastq),
                           functools.partial(run_rtc_impl, run_bam_to_fastq),
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
