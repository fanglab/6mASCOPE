
"""
BAM consolidation wrapper whose default behavior is dependent on input size.
"""

from __future__ import division
import logging
import uuid
import os.path as op
import os
import sys

from pbcommand.models import FileTypes, DataStore, DataStoreFile
from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log
from pbcore.io import openDataSet

log = logging.getLogger(__name__)
__version__ = "0.2.0"

# 10 GB is the max size we consolidate automatically
MAX_SIZE_GB = 10


# TODO this should live somewhere central
def _to_datastore(bam_file, bam_bai_file, datastore_json):
    files = [
        DataStoreFile(
            uuid.uuid4(),
            "mapped_bam",
            FileTypes.BAM.file_type_id,
            op.abspath(bam_file),
            name="Mapped BAM",
            description="Mapped reads in BAM format"),
        DataStoreFile(
            uuid.uuid4(),
            "mapped_bam_bai",
            FileTypes.BAMBAI.file_type_id,
            op.abspath(bam_bai_file),
            name="Mapped BAM Index",
            description="samtools index of mapped reads BAM")
    ]
    datastore = DataStore(files)
    datastore.write_json(datastore_json)
    return 0


def run_args(args):
    if op.exists(args.output_bam):
        raise IOError("{f} already exists".format(f=args.output_bam))
    bam_size = sum([op.getsize(r.bam) for r in args.dataset.externalResources])
    size_gb = bam_size / 1e9
    log.info("Total file size (in gigabytes): {s}".format(s=size_gb))
    metatype = args.dataset.datasetType
    bam_prefix = op.splitext(args.output_bam)[0]
    xml_out = ".".join([bam_prefix, FileTypes.ALL()[metatype].ext])
    log.info("Output dataset file name: {f}".format(f=xml_out))
    datastore_json = args.datastore
    if datastore_json is None:
        datastore_json = bam_prefix + ".datastore.json"
    bai_file = args.output_bam + ".bai"
    pbi_file = args.output_bam + ".pbi"
    if len(args.dataset.externalResources) == 1:
        log.info("Dataset already has a single BAM file: {f}".format(
                 f=args.dataset.externalResources[0].bam))
        log.info("Making sure we have a .bai index too")
        args.dataset.induceIndices()
        log.info("Symlinking as {f}".format(f=args.output_bam))
        os.symlink(args.dataset.externalResources[0].bam, args.output_bam)
        os.symlink(args.dataset.externalResources[0].bai, bai_file)
        os.symlink(args.dataset.externalResources[0].pbi, pbi_file)
        args.dataset.write(xml_out)
        return _to_datastore(args.output_bam, bai_file, datastore_json)
    elif size_gb > args.max_size:
        if not args.force:
            log.warn(
                "Skipping BAM consolidation because file size cutoff was exceeded")
            return 0
        else:
            log.warn("--force was used, so BAM consolidation will be run anyway")
    args.dataset.consolidate(args.output_bam,
                             numFiles=1,
                             useTmp=not args.noTmp)
    args.dataset.write(xml_out)
    return _to_datastore(args.output_bam, bai_file, datastore_json)


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument("dataset", type=openDataSet, help="Path to input dataset")
    p.add_argument("output_bam", help="Name of consolidated BAM file")
    p.add_argument("--force", action="store_true", default=False,
                   help="Consolidate the BAM files even if they exceed the size cutoff")
    p.add_argument("--max-size", action="store", type=int, default=MAX_SIZE_GB,
                   help="Maximum size (in GB) of files to consolidate")
    p.add_argument("--noTmp", default=False, action='store_true',
                   help="Don't copy to a tmp location to ensure local"
                        " disk use")
    p.add_argument("--datastore", action="store", default=None,
                   help="Name of output datastore file (defaults to same base name as BAM file with .datastore.json extension)")
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
