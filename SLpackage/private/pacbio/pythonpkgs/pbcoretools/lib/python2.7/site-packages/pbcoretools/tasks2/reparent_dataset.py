"""
Reparenting for running demux pipelines manually
"""

import logging
import os.path as op
import sys

from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log

from pbcoretools.file_utils import reparent_dataset

log = logging.getLogger(__name__)
__version__ = "0.1"


def run_args(args):
    return reparent_dataset(
        input_file=args.input_reads,
        dataset_name=args.dataset_name,
        output_file=args.output_file)


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument(
        "input_reads", help="SubreadSet or ConsensusReadSet use as INPUT for lima")
    p.add_argument("dataset_name", help="Dataset name")
    p.add_argument("output_file", help="Output dataset XML")
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
