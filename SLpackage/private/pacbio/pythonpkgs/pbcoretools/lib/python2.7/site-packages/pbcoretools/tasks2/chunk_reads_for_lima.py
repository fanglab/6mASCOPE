"""
Tool to generate chunked inputs for lima deumultiplexing.  The number of
outputs depends on whether --peek-guess is being used or not; in this mode we
pass the input dataset through without subdividing.
"""

import logging
import os.path as op
import sys

from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log
from pbcommand.models import FileTypes
from pbcore.io import openDataSet

log = logging.getLogger(__name__)
__version__ = "0.1"


def split_reads(ds_file, max_chunks, target_size, lima_peek_guess):
    reads = openDataSet(ds_file)
    ds_type = FileTypes.ALL()[reads.datasetType]
    if lima_peek_guess:
        log.info("--peek-guess is being used, writing single chunk")
        reads.write("chunk_all.{e}".format(e=ds_type.ext))
        return 1
    elif len(reads) < target_size:
        log.info("Dataset is < %d reads, writing single chunk", target_size)
        reads.write("chunk_all.{e}".format(e=ds_type.ext))
        return 1
    else:
        chunks = reads.split(maxChunks=max_chunks,
                             targetSize=target_size,
                             zmws=True)
        log.info("%d chunked datasets will be written", len(chunks))
        for i, ds in enumerate(chunks):
            file_name = "chunk{i}.{e}".format(i=i, e=ds_type.ext)
            ds.write(file_name)
            log.debug("Wrote %s", file_name)
        return len(chunks)


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument(
        "reads", help="SubreadSet or ConsensusReadSet use as INPUT for lima")
    p.add_argument("--maxChunks", default=0, type=int,
                   help="Split into at most <chunks> groups, possibly fewer")
    p.add_argument("--targetSize", default=5000, type=int,
                   help="Target number of records per chunk")
    p.add_argument("--lima-peek-guess", action="store_true", default=False,
                   help="Indicate whether lima is being run with --peek-guess; if true, only 1 chunk will be written.")
    return p


def run_args(args):
    nchunks = split_reads(args.reads, args.maxChunks,
                          args.targetSize, args.lima_peek_guess)
    return 0


def main(argv=sys.argv):
    return pacbio_args_runner(
        argv=argv[1:],
        parser=_get_parser(),
        args_runner_func=run_args,
        alog=log,
        setup_log_func=setup_log)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
