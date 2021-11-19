"""
Tool to gather lima output in the form of 1 or more datastore JSON files; this
will combine the individual datasets and consolidate to a single BAM file each.
"""

from collections import defaultdict
import multiprocessing
import logging
import os.path as op
import sys

from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.utils import setup_log
from pbcommand.models import FileTypes, DataStore, DataStoreFile
from pbcore.io import openDataSet

log = logging.getLogger(__name__)
__version__ = "0.1"


def _merge_chunks(file_names, datastore_file):
    output_file = op.basename(file_names[0])
    ds = openDataSet(*file_names)
    if len(file_names) > 1:
        bam_file = ".".join(output_file.split(".")[:-2] + ["bam"])
        ds.consolidate(bam_file, useTmp=False)
        bc_file = ds.subdatasets[0].externalResources[0].barcodes
        if bc_file is not None:
            bc_file = op.realpath(bc_file)
            ds.externalResources[0].barcodes = bc_file
    ds.write(output_file, relPaths=False)
    log.info("Wrote %s", output_file)
    return DataStoreFile(ds.uuid,
                         datastore_file.source_id,
                         ds.datasetType,
                         op.abspath(output_file))


def gather_chunks(chunks, output_file, nproc=1):
    if len(chunks) == 1:
        datastore = DataStore.load_from_json(op.realpath(chunks[0]))
        log.info("Writing datastore to %s", output_file)
        datastore.write_json(output_file)
        return len(datastore.files)
    file_names_by_bc = defaultdict(list)
    datastore_files_by_bc = {}
    for file_name in chunks:
        log.info("Reading datastore from %s", file_name)
        datastore = DataStore.load_from_json(op.realpath(file_name))
        for ds_file in datastore.files.values():
            ds_file_name = op.realpath(ds_file.path)
            base_name = op.basename(ds_file_name)
            fields = base_name.split(".")
            bc_pair = fields[-3]
            file_names_by_bc[bc_pair].append(ds_file_name)
            datastore_files_by_bc[bc_pair] = ds_file
    log.info("Found %d unique barcode pairs", len(file_names_by_bc))
    _results = []
    pool = multiprocessing.Pool(nproc)
    for bc_pair, file_names in file_names_by_bc.iteritems():
        _results.append(
            pool.apply_async(_merge_chunks,
                             (file_names,
                              datastore_files_by_bc[bc_pair])))
    pool.close()
    pool.join()
    datastore_files = [r.get() for r in _results]
    datastore_out = DataStore(datastore_files)
    log.info("Writing datastore to %s", output_file)
    datastore_out.write_json(output_file)
    return len(datastore_files)


def _get_parser():
    p = get_default_argparser_with_base_opts(
        version=__version__,
        description=__doc__,
        default_level="INFO")
    p.add_argument("merged", help="Name of merge datastore file")
    p.add_argument("chunks", nargs="+", help="Chunk datastore outputs")
    p.add_argument("-j", "--nproc", dest="nproc", type=int, default=1,
                   help="Number of processors to use")
    return p


def run_args(args):
    gather_chunks(args.chunks, args.merged, nproc=args.nproc)
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
