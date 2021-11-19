"""
Tool to check input ConsensusReadSet for lima should not be already demultiplexed.
"""

from collections import defaultdict
import logging
import os.path as op
import sys
from argparse import ArgumentParser
from pbcore.io import ConsensusReadSet

log = logging.getLogger(__name__)
__version__ = "0.1"


def is_ccs_demultiplexed(input_file):
    log.info("Checking {} is lima-demultiplexed or not.".format(input_file))
    ds = ConsensusReadSet(input_file)
    return ds.isBarcoded


def run(args):
    ccs = args.ccs
    if is_ccs_demultiplexed(ccs):
        raise ValueError(
            "Input ConsensusReadSet {} must not be lima-demultiplexed!".format(ccs))


def get_parser():
    p = ArgumentParser(
        "Check input ConsensusReadSet must not be demultiplexed.")
    p.add_argument("ccs", type=str, help="Input ConsensusReadSet to check")
    return p


def main(argv=sys.argv[1:]):
    run(get_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
