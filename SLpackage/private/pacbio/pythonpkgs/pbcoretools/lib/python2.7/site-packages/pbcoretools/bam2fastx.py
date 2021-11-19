
"""
Wrapper function for running bam2fasta/bam2fastq, with zipfile support.
"""

import functools
import tempfile
import logging
import gzip
import time
import re
import os.path as op
import pipes
import os
import sys

from pbcore.io import (openDataSet, BarcodeSet, FastaReader, FastaWriter,
                       FastqReader, FastqWriter, SubreadSet)
from pbcommand.engine import run_cmd
from pbcommand.utils import walker

from pbcoretools.file_utils import archive_files, get_barcode_sample_mappings

log = logging.getLogger(__name__)


def _filesize(fn):
    """In bytes.
    Raise if fn does not exist.
    """
    return os.stat(fn).st_size


def _check_exists_and_not_empty(fn):
    if not os.path.exists(fn):
        raise IOError('File {!r} does not exist.'.format(fn))
    if 0 == _filesize(fn):
        raise IOError('File {!r} is empty.'.format(fn))


def _ungzip_fastx(gzip_file_name, fastx_file_name, retry=True):
    """
    Decompress an output from bam2fastx.
    """
    try:
        # An empty file gzips to a non-empty gzip file.
        # So an empty gzip-file is likely incomplete, but it
        # would be accepted by gzip.open().
        _check_exists_and_not_empty(gzip_file_name)

        with gzip.open(gzip_file_name, "rb") as gz_in:
            with open(fastx_file_name, "wb") as fastx_out:
                def _fread():
                    return gz_in.read(1024)
                for chunk in iter(_fread, ''):
                    fastx_out.write(chunk)
    except IOError as e:
        if retry:
            log.error(e)
            log.warn("Will re-try in 10 seconds in case of NFS glitch")
            time.sleep(10)
            return _ungzip_fastx(gzip_file_name, fastx_file_name, retry=False)
        else:
            raise


def _run_bam_to_fastx(program_name, fastx_reader, fastx_writer,
                      input_file_name, output_file_name, tmp_dir=None,
                      seqid_prefix=None, subreads_in=None):
    """
    Converts a dataset to a set of fastx file, possibly archived.
    Can take a subreadset or consensusreadset as input.
    Will convert to either fasta or fastq.
    If the dataset is barcoded, it will split the fastx files per-barcode.
    If the output file is .zip, the fastx file(s) will be archived accordingly.
    """
    assert isinstance(program_name, basestring)
    barcode_mode = False
    barcode_sets = set()
    if output_file_name.endswith(".zip"):
        with openDataSet(input_file_name) as ds_in:
            barcode_mode = ds_in.isBarcoded
            if barcode_mode:
                # attempt to collect the labels of barcodes used on this
                # dataset.  assumes that all BAM files used the same barcodes
                for bam in ds_in.externalResources:
                    if bam.barcodes is not None:
                        barcode_sets.add(bam.barcodes)
    barcode_labels = []
    bio_samples_to_bc = None
    if barcode_mode:
        if len(barcode_sets) == 1:
            bc_file = list(barcode_sets)[0]
            log.info("Reading barcode labels from %s", bc_file)
            try:
                with BarcodeSet(bc_file) as bc_in:
                    for bc in bc_in:
                        barcode_labels.append(bc.id)
            except IOError as e:
                log.error("Can't read %s", bc_file)
                log.error(e)
        elif len(barcode_sets) > 1:
            log.warn("Multiple barcode sets used for this SubreadSet:")
            for fn in sorted(list(barcode_sets)):
                log.warn("  %s", fn)
        else:
            log.info("No barcode labels available")
        if subreads_in is not None:
            bio_samples_to_bc = {}
            with SubreadSet(subreads_in, strict=True) as subread_ds:
                if subread_ds.isBarcoded:
                    bio_samples_to_bc = get_barcode_sample_mappings(subread_ds)
    base_ext = re.sub("bam2", ".", program_name)
    suffix = "{f}.gz".format(f=base_ext)
    tmp_out_prefix = tempfile.NamedTemporaryFile(dir=tmp_dir).name
    tmp_out_dir = op.dirname(tmp_out_prefix)
    args = [
        program_name,
        "-o", tmp_out_prefix,
        input_file_name,
    ]
    if barcode_mode:
        args.insert(1, "--split-barcodes")
    if seqid_prefix is not None:
        args.extend(["--seqid-prefix", pipes.quote(seqid_prefix)])
    log.info(" ".join(args))
    remove_files = []
    result = run_cmd(" ".join(args),
                     stdout_fh=sys.stdout,
                     stderr_fh=sys.stderr)

    def _is_fastx_file(fn):
        return fn.startswith(tmp_out_prefix) and fn.endswith(suffix)

    try:
        assert result.exit_code == 0, "{p} exited with code {c}".format(
            p=program_name, c=result.exit_code)
        if output_file_name.endswith(".zip"):
            tc_out_dir = op.dirname(output_file_name)
            fastx_file_names = []
            # find the barcoded FASTX files and un-gzip them to the same
            # output directory and file prefix as the ultimate output
            for fn in walker(tmp_out_dir, _is_fastx_file):
                if barcode_mode:
                    # bam2fastx outputs files with the barcode indices
                    # encoded in the file names; here we attempt to
                    # translate these to barcode labels, falling back on
                    # the original indices if necessary
                    bc_fwd_rev = fn.split(".")[-3].split("_")
                    bc_label = "unbarcoded"
                    if (bc_fwd_rev != ["65535", "65535"] and
                            bc_fwd_rev != ["-1", "-1"]):
                        def _label_or_none(x):
                            try:
                                bc = int(x)
                                if bc < 0:
                                    return "none"
                                elif bc < len(barcode_labels):
                                    return barcode_labels[bc]
                            except ValueError as e:
                                pass
                            return x
                        bc_fwd_label = _label_or_none(bc_fwd_rev[0])
                        bc_rev_label = _label_or_none(bc_fwd_rev[1])
                        bc_label = "{f}--{r}".format(f=bc_fwd_label,
                                                     r=bc_rev_label)
                    suffix2 = ".{l}{t}".format(l=bc_label, t=base_ext)
                    if bio_samples_to_bc is not None:
                        sample = bio_samples_to_bc.get(bc_label, "unknown")
                        suffix2 = ".{}".format(sample) + suffix2
                else:
                    suffix2 = base_ext
                base, ext = op.splitext(op.basename(output_file_name))
                fn_out = base
                if not fn_out.endswith(suffix2):
                    fn_out = re.sub(base_ext, suffix2, fn_out)
                fastx_out = op.join(tc_out_dir, fn_out)
                _ungzip_fastx(fn, fastx_out)
                fastx_file_names.append(fastx_out)
                remove_files.append(fn)
            assert len(fastx_file_names) > 0
            remove_files.extend(fastx_file_names)
            return archive_files(fastx_file_names, output_file_name)
        else:
            tmp_out = "{p}{b}.gz".format(p=tmp_out_prefix, b=base_ext)
            _ungzip_fastx(tmp_out, output_file_name)
            remove_files = [tmp_out]
    finally:
        for fn in remove_files:
            os.remove(fn)
    return 0


run_bam_to_fasta = functools.partial(_run_bam_to_fastx, "bam2fasta",
                                     FastaReader, FastaWriter)
run_bam_to_fastq = functools.partial(_run_bam_to_fastx, "bam2fastq",
                                     FastqReader, FastqWriter)
