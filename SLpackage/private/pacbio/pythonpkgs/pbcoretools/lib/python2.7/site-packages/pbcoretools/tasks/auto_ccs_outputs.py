"""
Generate single-file CCS BAM and FASTQ outputs from a ConsensusReadSet.
"""

import tempfile
import logging
import uuid
import math
import sys
import os.path as op
import re

import numpy as np

from pbcommand.models import FileTypes, ResourceTypes, get_pbparser, DataStoreFile, DataStore
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import ConsensusReadSet
from pbcore.util.statistics import accuracy_as_phred_qv

from pbcoretools.bam2fastx import run_bam_to_fastq, run_bam_to_fasta
from pbcoretools.filters import combine_filters

log = logging.getLogger(__name__)


class Constants(object):
    TOOL_ID = "pbcoretools.tasks.auto_ccs_outputs"
    VERSION = "0.2.0"
    DRIVER = "python -m pbcoretools.tasks.auto_ccs_outputs --resolved-tool-contract"
    BASE_EXT = ".Q20"
    BAM_EXT = ".ccs.bam"
    BAM_ID = "ccs_bam_out"
    FASTA_ID = "ccs_fasta_out"
    FASTQ_ID = "ccs_fastq_out"
    FASTA2_ID = "ccs_fasta_lq_out"
    FASTQ2_ID = "ccs_fastq_lq_out"


def _get_parser():
    p = get_pbparser(Constants.TOOL_ID,
                     Constants.VERSION,
                     "Generate primary CCS outputs",
                     __doc__,
                     Constants.DRIVER,
                     is_distributed=True)
    # resource_types=(ResourceTypes.TMP_DIR,))
    p.add_input_file_type(FileTypes.DS_CCS, "ccs_dataset",
                          "ConsensusReadSet XML",
                          "ConsensusReadSet XML")
    p.add_output_file_type(FileTypes.DATASTORE,
                           "datastore_out",
                           "DataStore JSON",
                           description="DataStore JSON",
                           default_name="ccs_outputs")
    return p


def _to_datastore_file(file_name, file_id, file_type, description):
    return DataStoreFile(uuid.uuid4(),
                         file_id,
                         file_type.file_type_id,
                         op.abspath(file_name),
                         name=op.basename(file_name),
                         description=description)


def consolidate_bam(base_dir, file_prefix, dataset):
    bam_file_name = op.join(base_dir, file_prefix + Constants.BAM_EXT)
    dataset.consolidate(bam_file_name)
    return _to_datastore_file(file_name=bam_file_name,
                             file_id=Constants.BAM_ID,
                             file_type=FileTypes.BAM_CCS,
                             description="CCS BAM file")


def _run_bam2fastx(file_type, dataset_file, fastx_file):
    if file_type == FileTypes.FASTQ:
        return run_bam_to_fastq(dataset_file, fastx_file)
    else:
        return run_bam_to_fasta(dataset_file, fastx_file)


def to_fastx_files(file_type, ds, ccs_dataset_file, file_ids, base_dir, file_prefix):
    fastx_file = op.join(base_dir, file_prefix +
                         Constants.BASE_EXT + "." + file_type.ext)
    ccs_q20 = ccs_dataset_file
    is_all_q20_or_better = np.all(ds.index.readQual >= 0.99)
    if not is_all_q20_or_better:
        ccs_hq = ds.copy()
        ccs_q20 = tempfile.NamedTemporaryFile(
            suffix=".consensusreadset.xml").name
        combine_filters(ccs_hq, {"rq": [('>=', 0.99)]})
        ccs_hq.write(ccs_q20)
    _run_bam2fastx(file_type, ccs_q20, fastx_file)
    datastore_files = [
        _to_datastore_file(fastx_file, file_ids[0], file_type, "Q20 Reads")
    ]
    if not is_all_q20_or_better:
        min_accuracy = float(np.min(ds.index.readQual))
        if min_accuracy <= 0:
            min_qv = 0
        else:
            min_qv = int(math.floor(accuracy_as_phred_qv(min_accuracy)))
        custom_ext = ".Q" + str(min_qv)
        fastx2_file = op.join(
            base_dir, file_prefix + custom_ext + "." + file_type.ext)
        _run_bam2fastx(file_type, ccs_dataset_file, fastx2_file)
        desc = "Q{q} Reads".format(q=min_qv)
        datastore_files.append(
            _to_datastore_file(fastx2_file, file_ids[1], file_type, desc))
    return datastore_files


def get_prefix_and_bam_file_name(ds, is_barcoded=False):
    bam_file_name = file_prefix = None
    if is_barcoded:
        assert len(ds.externalResources) == 1
        bam = ds.resourceReaders()[0]
        barcodes = list(set(zip(bam.pbi.bcForward, bam.pbi.bcReverse)))
        assert len(barcodes) == 1, "Multiple barcodes found in {f}: {b}".format(
            f=ds.fileNames[0], b=", ".join([str(b) for b in barcodes]))
        bam_file_name = ds.externalResources[0].bam
        log.info("Found a single barcoded BAM %s", bam_file_name)
        # we need to handle both '.bam' and '.ccs.bam'
        file_prefix = re.sub(".bam$", "",
                             re.sub(".ccs.bam$", "", op.basename(bam_file_name)))
    else:
        movies = sorted(list({rg.MovieName for rg in ds.readGroupTable}))
        file_prefix = "_".join(movies)
        if len(movies) > 1:
            log.warn("Multiple movies found: %s", movies)
            file_prefix = "multiple_movies"
    return bam_file_name, file_prefix


def run_ccs_bam_fastq_exports(ccs_dataset_file, base_dir, is_barcoded=False):
    """
    Take a ConsensusReadSet and write BAM/FASTQ files to the output
    directory.  If this is a demultiplexed dataset, it is assumed to have
    a single BAM file within a dataset that is already imported in SMRT Link.
    """
    datastore_files = []
    with ConsensusReadSet(ccs_dataset_file, strict=True) as ds:
        bam_file_name, file_prefix = get_prefix_and_bam_file_name(ds, is_barcoded)
        if bam_file_name is None:
            datastore_files.append(consolidate_bam(base_dir, file_prefix, ds))
        fasta_file_ids = [Constants.FASTA_ID, Constants.FASTA2_ID]
        fastq_file_ids = [Constants.FASTQ_ID, Constants.FASTQ2_ID]
        datastore_files.extend(
            to_fastx_files(FileTypes.FASTA, ds, ccs_dataset_file, fasta_file_ids, base_dir, file_prefix))
        datastore_files.extend(
            to_fastx_files(FileTypes.FASTQ, ds, ccs_dataset_file, fastq_file_ids, base_dir, file_prefix))
    return datastore_files


def _run_auto_ccs_outputs(ccs_dataset, datastore_out):
    base_dir = op.dirname(datastore_out)
    DataStore(run_ccs_bam_fastq_exports(ccs_dataset,
                                        base_dir)).write_json(datastore_out)
    return 0


def _run_args(args):
    return _run_auto_ccs_outputs(args.ccs_dataset, args.datastore_out)


def _run_rtc(rtc):
    return _run_auto_ccs_outputs(rtc.task.input_files[0],
                                 rtc.task.output_files[0])


def _main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           _get_parser(),
                           _run_args,
                           _run_rtc,
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
