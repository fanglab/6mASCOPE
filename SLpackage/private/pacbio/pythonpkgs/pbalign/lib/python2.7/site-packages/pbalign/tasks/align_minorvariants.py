
"""
pbalign wrapper for Minor Variants workflow
"""

import logging
import sys

from pbcommand.models import FileTypes, SymbolTypes, ResourceTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import ConsensusAlignmentSet

from pbalign.pbalignrunner import args_runner
from pbalign.options import get_contract_parser

log = logging.getLogger(__name__)
__version__ = "0.1"


class Constants(object):
    TOOL_ID = "pbalign.tasks.align_minorvariants"
    DRIVER_EXE = "python -m pbalign.tasks.align_minorvariants --resolved-tool-contract "


def get_parser():
    p = get_pbparser(Constants.TOOL_ID, __version__,
                     "Minor Variants Mapping", __doc__,
                     Constants.DRIVER_EXE,
                     is_distributed=True,
                     nproc=SymbolTypes.MAX_NPROC,
                     resource_types=(ResourceTypes.TMP_DIR,))
    p.add_input_file_type(FileTypes.DS_CCS, "ccs_in",
                          name="ConsensusReadSet",
                          description="ConsensusRead DataSet file")
    p.add_input_file_type(FileTypes.DS_REF, "referencePath",
        "ReferenceSet", "Reference DataSet or FASTA file")
    p.add_output_file_type(FileTypes.DS_ALIGN_CCS, "aligned",
        name="Alignments",
        description="Alignment results dataset",
        default_name="aligned")
    return p


def run_args(args):
    return 0


def run_rtc(rtc):
    p = get_contract_parser().arg_parser.parser
    argv = [
        rtc.task.input_files[0],
        rtc.task.input_files[1],
        rtc.task.output_files[0],
        "--nproc", str(rtc.task.nproc),
        "--maxMatch", "15",
        "--algorithmOptions",
        '--placeGapConsistently --scoreMatrix "-1 4 4 4 6 4 -1 4 4 6 4 4 -1 4 6 4 4 4 -1 6 6 6 6 6 6"',
        "--tmpDir", rtc.task.tmpdir_resources[0].path,
        "--log-level", rtc.task.log_level
    ]
    return args_runner(
        args=p.parse_args(argv),
        output_dataset_type=ConsensusAlignmentSet)


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           get_parser(),
                           run_args,
                           run_rtc,
                           log,
                           setup_log)


if __name__ == '__main__':
    sys.exit(main())
