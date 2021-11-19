"""
Task to generate BAM/FASTA/FASTQ outputs of a CCS job, with datastore
attributes defined so they appear in the SMRT Link UI.  Unlike the old
pbsmrtpipe task, this one only generates a single output file, allowing the
outputs to be parallelized by the workflow engine.
"""

import logging
import os.path as op
import sys

from pbcommand.models import FileTypes, DataStore
from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log
from pbcore.io import ConsensusReadSet
from pbcore.util.statistics import accuracy_as_phred_qv

from pbcoretools.tasks.auto_ccs_outputs import (get_prefix_and_bam_file_name,
                                                to_fastx_files,
                                                consolidate_bam)

log = logging.getLogger(__name__)
__version__ = "0.1.0"


class Constants(object):
    BASE_EXT = ".Q20"
    BAM_EXT = ".ccs.bam"
    BAM_ID = "ccs_bam_out"
    FASTA_ID = "ccs_fasta_out"
    FASTQ_ID = "ccs_fastq_out"
    FASTA2_ID = "ccs_fasta_lq_out"
    FASTQ2_ID = "ccs_fastq_lq_out"
    FASTA_FILE_IDS = [FASTA_ID, FASTA2_ID]
    FASTQ_FILE_IDS = [FASTQ_ID, FASTQ2_ID]


def run_args(args):
    datastore_out = op.abspath(args.datastore_out)
    base_dir = op.dirname(datastore_out)
    datastore_files = []
    with ConsensusReadSet(args.dataset_file, strict=True) as ds:
        bam_file_name, file_prefix = get_prefix_and_bam_file_name(
            ds, is_barcoded=False)
        if args.mode == "fasta":
            datastore_files.extend(to_fastx_files(
                FileTypes.FASTA, ds, args.dataset_file, Constants.FASTA_FILE_IDS, base_dir, file_prefix))
        elif args.mode == "fastq":
            datastore_files.extend(to_fastx_files(
                FileTypes.FASTQ, ds, args.dataset_file, Constants.FASTQ_FILE_IDS, base_dir, file_prefix))
        elif args.mode == "consolidate":
            if bam_file_name is None:
                datastore_files.append(
                    consolidate_bam(base_dir, file_prefix, ds))
    DataStore(datastore_files).write_json(datastore_out)
    return 0


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument("mode", choices=["consolidate", "fasta", "fastq"])
    p.add_argument("dataset_file")
    p.add_argument("datastore_out")
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
