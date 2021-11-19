"""
Dataset filtering tool that incorporates downsampling; replaces old pbsmrtpipe
task pbcoretools.tasks.filter_dataset.
"""

import logging
import re
import os.path as op
import sys

from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log

from pbcoretools.filters import run_filter_dataset

log = logging.getLogger(__name__)
__version__ = "0.1"


def run_args(args):
    return run_filter_dataset(
        in_file=args.dataset,
        out_file=args.xml_out,
        read_length=args.min_read_length,
        other_filters=args.filters,
        downsample_factor=args.downsample)


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument("dataset", help="Dataset XML input file")
    p.add_argument("xml_out", help="Output dataset XML file")
    p.add_argument("filters", help="Filters as string")
    p.add_argument("--downsample", action="store", type=int, default=0,
                   help="Downsampling factor")
    p.add_argument("--min-read-length", action="store", type=int, default=0,
                   help="Minimum read length")
    return p


def main(argv=sys.argv):
    return pacbio_args_runner(
        argv=argv[1:],
        parser=_get_parser(),
        args_runner_func=run_args,
        alog=log,
        setup_log_func=setup_log)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
