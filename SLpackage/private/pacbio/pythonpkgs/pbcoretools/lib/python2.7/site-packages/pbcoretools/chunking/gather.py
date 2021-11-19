
from collections import defaultdict, namedtuple, OrderedDict
from functools import partial as P
from zipfile import ZipFile
import itertools
import argparse
import tarfile
import logging
import shutil
import json
import math
import os.path as op
import sys

from pbcommand.pb_io.common import load_pipeline_chunks_from_json
from pbcommand.validators import fofn_to_files, validate_file
from pbcommand.pb_io.report import load_report_from_json
from pbcommand.common_options import add_debug_option
from pbcommand.cli.utils import main_runner_default, subparser_builder
from pbcommand.cli import get_default_argparser
from pbcommand.models.report import Report
from pbcommand.models import DataStore

from pbcore.io import (SubreadSet, ContigSet, AlignmentSet, ConsensusReadSet,
                       ConsensusAlignmentSet, TranscriptSet, TranscriptAlignmentSet)
from pbcore.io.FastaIO import FastaReader, FastaWriter
from pbcore.io.FastqIO import FastqReader, FastqWriter
from pbcore.io.GffIO import merge_gffs_sorted
from pbcore.io.VcfIO import merge_vcfs_sorted

from pbcoretools.file_utils import sanitize_dataset_tags

log = logging.getLogger(__name__)

__version__ = '1.1'


def _validate_chunk_json_file(path):
    chunks = load_pipeline_chunks_from_json(path)
    return path


def __gather_fastx(fastx_reader, fastx_writer, fastx_files, output_file):

    n = 0
    with fastx_writer(output_file) as writer:
        for fastx_file in fastx_files:
            with fastx_reader(fastx_file) as reader:
                for record in reader:
                    n += 1
                    writer.writeRecord(record)

    log.info("Completed gathering {n} files (with {x} records) to {f}".format(
        n=len(fastx_files), f=output_file, x=n))


gather_fasta = P(__gather_fastx, FastaReader, FastaWriter)
gather_fastq = P(__gather_fastx, FastqReader, FastqWriter)
gather_gff = merge_gffs_sorted
gather_vcf = merge_vcfs_sorted


def _read_header(csv_file):
    with open(csv_file, 'r') as f:
        header = f.readline()

    if ',' in header:
        return header.rstrip().split(',')
    else:
        return None


def __has_header(handle):
    next(handle)


def __has_header_and_one_record(handle):
    # has header
    __has_header(handle)
    # has at least one record
    next(handle)


def __csv_inspector(func, csv_file):

    is_empty = False
    with open(csv_file, 'r') as f:
        try:
            func(f)
        except StopIteration:
            is_empty = True

    return is_empty


_csv_is_empty = P(__csv_inspector, __has_header_and_one_record)
_csv_has_header = P(_csv_is_empty, __has_header)


def get_datum_from_chunks_by_chunk_key(chunks, chunk_key):
    log.info(
        "extracting datum from chunks using chunk-key '{c}'".format(c=chunk_key))
    datum = []
    for chunk in chunks:
        if chunk_key in chunk.chunk_keys:
            value = chunk.chunk_d[chunk_key]
            datum.append(value)
        else:
            raise KeyError("Unable to find chunk key '{i}' in {p}".format(
                i=chunk_key, p=chunk))

    return datum


def gather_csv(csv_files, output_file, skip_empty=True):
    """

    :param csv_files:
    :param output_file:
    :param skip_empty: Emtpy files with or without the header will be skipped

    :type skip_empty: bool
    :return:
    """

    header = _read_header(csv_files[0])
    #nfields = 0 if header is None else len(header)

    with open(output_file, 'w') as writer:
        if header is not None:
            writer.write(",".join(header) + "\n")
        for csv_file in csv_files:
            if not _csv_is_empty(csv_file):
                header = _read_header(csv_file)
                # should do a comparison of the headers to make sure they
                # have the same number of fields
                with open(csv_file, 'r') as f:
                    # skip header
                    _ = f.readline()
                    for record in f:
                        writer.write(record)

    log.info("successfully merged {n} files to {f}".format(
        n=len(csv_files), f=output_file))

    return output_file


def gather_report(json_files, output_file):
    """
    Combines statistics (usually raw counts) stored as JSON files.
    Data models: pbcommand.models.report
    """
    reports = [load_report_from_json(fn) for fn in json_files]
    merged = Report.merge(reports)
    with open(output_file, "w") as writer:
        writer.write(merged.to_json())
    return output_file


def gather_txt(input_files, output_file, skip_empty=False):
    """
    Very simple concatenation of text files labeled by file name.
    """
    lines = []
    for input_file in input_files:
        with open(input_file, "r") as txt:
            lines.append("### FILE {f}:\n{t}".format(f=input_file,
                                                     t=txt.read()))
    with open(output_file, "w") as out:
        out.write("\n\n\n".join(lines))
    return output_file


def gather_fofn(input_files, output_file, skip_empty=True):
    """
    This should be better spec'ed and impose a tighter constraint on the FOFN

    :param input_files: List of file paths
    :param output_file: File Path
    :param skip_empty: Ignore empty files

    :return: Output file

    :rtype: str
    """

    all_files = []
    for input_file in input_files:
        file_names = fofn_to_files(input_file)
        all_files.extend(file_names)

    with open(output_file, 'w') as f:
        f.write("\n".join(all_files))

    return output_file


def gather_datastore(input_files, output_file, skip_empty=True):
    ds = DataStore([])
    for i_fn in input_files:
        for uuid, f in DataStore.load_from_json(i_fn).files.iteritems():
            ds.add(f)
    ds.write_json(output_file)


def __gather_contigset(resource_file_extension, input_files, output_file,
                       new_resource_file=None,
                       skip_empty=True):
    """
    :param input_files: List of file paths
    :param output_file: File Path
    :param new_resource_file: the path of the file to which the other contig
                              files are consolidated
    :param skip_empty: Ignore empty files (doesn't do much yet)

    :return: Output file

    :rtype: str
    """
    if skip_empty:
        _input_files = []
        for file_name in input_files:
            cs = ContigSet(file_name)
            if len(cs.toExternalFiles()) > 0:
                _input_files.append(file_name)
        input_files = _input_files
    tbr = ContigSet(*input_files)
    if not new_resource_file:
        if output_file.endswith('xml'):
            new_resource_file = output_file[:-3] + resource_file_extension
    tbr.consolidate(new_resource_file)
    tbr.newUuid()
    sanitize_dataset_tags(tbr)
    tbr.write(output_file)
    return output_file


gather_contigset = P(__gather_contigset, "fasta")


def __gather_fastx_contigset(format_type, input_files, output_file):
    if len(input_files) == 1:
        shutil.copyfile(input_files[0], output_file)
    else:
        contigset_name = op.splitext(output_file)[0] + ".contigset.xml"
        __gather_contigset(format_type, input_files, contigset_name,
                           new_resource_file=output_file)
        assert op.isfile(output_file)
        return output_file


gather_fasta_contigset = P(__gather_fastx_contigset, "fasta")
gather_fastq_contigset = P(__gather_fastx_contigset, "fastq")


def _uniqueify_metadata(ds):
    if ds.metadata is not None and len(ds.metadata.collections) > 1:
        have_collections = set()
        k = 0
        while k < len(ds.metadata.collections):
            if ds.metadata.collections[k].uniqueId in have_collections:
                ds.metadata.collections.pop(k)
            else:
                have_collections.add(ds.metadata.collections[k].uniqueId)
                k += 1


def __gather_readset(dataset_type, input_files, output_file, skip_empty=True,
                     consolidate=False, consolidate_n_files=1):
    """
    :param input_files: List of file paths
    :param output_file: File Path
    :param skip_empty: Ignore empty files (doesn't do much yet)

    :return: Output file

    :rtype: str
    """
    tbr = dataset_type(*input_files)
    _uniqueify_metadata(tbr)
    if consolidate:
        new_resource_file = output_file[:-4] + ".bam"
        tbr.consolidate(new_resource_file, numFiles=consolidate_n_files)
        tbr.induceIndices()
    tbr.newUuid()
    sanitize_dataset_tags(tbr)
    tbr.write(output_file)
    return output_file


gather_subreadset = P(__gather_readset, SubreadSet)
gather_alignmentset = P(__gather_readset, AlignmentSet)
gather_ccsset = P(__gather_readset, ConsensusReadSet)
gather_ccs_alignmentset = P(__gather_readset, ConsensusAlignmentSet)
gather_transcripts = P(__gather_readset, TranscriptSet)
gather_transcript_alignmentset = P(__gather_readset, TranscriptAlignmentSet)


def gather_tgz(input_files, output_file):
    """
    Deprecated, use ZIP files instead where possible.
    """
    with tarfile.open(output_file, mode="w:gz") as tgz_out:
        for tgz_file in input_files:
            with tarfile.open(tgz_file, mode="r:gz") as tgz_in:
                for member in tgz_in.getmembers():
                    tgz_out.addfile(member, tgz_in.extractfile(member.name))
    return output_file


def gather_zip(input_files, output_file):
    """
    Gather ZIP archives; used in minor variants analysis.
    """
    with ZipFile(output_file, "w", allowZip64=True) as zip_out:
        for zip_file in input_files:
            with ZipFile(zip_file, "r") as zip_in:
                for member in zip_in.namelist():
                    f = zip_in.open(member)
                    zip_out.writestr(member, f.read())
    return output_file


def gather_json(input_files, output_file):
    """
    Gather chunked JSON dictionaries, which must have mutually non-overlapping
    keys.  Used in minor variants analysis.
    """
    gathered = {}
    for chunk_file in input_files:
        with open(chunk_file) as json_in:
            d = json.loads(json_in.read())
            assert len(set(d.keys()).intersection(gathered)) == 0
            gathered.update(d)
    with open(output_file, "w") as json_out:
        json_out.write(json.dumps(gathered))
    return output_file


def __add_chunk_key_option(default_chunk_key):
    def _add_chunk_key_option(p):
        p.add_argument('--chunk-key', type=str, default=default_chunk_key,
                       help="Chunk key (e.g, $chunk.my_chunk_key_id) to gather over")
        return p
    return _add_chunk_key_option


add_chunk_key_csv = __add_chunk_key_option('$chunk.csv_id')
add_chunk_key_txt = __add_chunk_key_option('$chunk.txt_id')
add_chunk_key_fasta = __add_chunk_key_option('$chunk.fasta_id')
add_chunk_key_fastq = __add_chunk_key_option('$chunk.fastq_id')
add_chunk_key_gff = __add_chunk_key_option('$chunk.gff_id')
add_chunk_key_vcf = __add_chunk_key_option('$chunk.vcf_id')
add_chunk_key_fofn = __add_chunk_key_option('$chunk.fofn_id')
add_chunk_key_subreadset = __add_chunk_key_option('$chunk.subreadset_id')
add_chunk_key_alignmentset = __add_chunk_key_option('$chunk.alignmentset_id')
add_chunk_key_ccsset = __add_chunk_key_option('$chunk.ccsset_id')
add_chunk_key_ccs_alignmentset = __add_chunk_key_option(
    '$chunk.ccs_alignmentset_id')
add_chunk_key_transcripts = __add_chunk_key_option('$chunk.transcriptset_id')
# TODO: change this to contigset_id once quiver emits contigsets
add_chunk_key_contigset = __add_chunk_key_option('$chunk.fasta_id')
add_chunk_key_report = __add_chunk_key_option('$chunk.json_id')
add_chunk_key_tgz = __add_chunk_key_option('$chunk.tgz_id')


def __gather_options(output_file_message, input_files_message, input_validate_func, add_chunk_key_func_):
    def _f(p):
        p.add_argument('chunk_json',
                       type=input_validate_func,
                       help=input_files_message)
        p.add_argument('-o', '--output', type=str, help=output_file_message)
        return add_chunk_key_func_(p)
    return _f


def __add_gather_options(output_file_msg, input_file_msg, chunk_key_func):
    def _f(p):
        add_debug_option(p)
        f = __gather_options(output_file_msg, input_file_msg,
                             validate_file, chunk_key_func)
        return f(p)
    return _f


_gather_csv_options = __add_gather_options(
    "Output CSV file", "input CSV file", add_chunk_key_csv)
_gather_txt_options = __add_gather_options(
    "Output text file", "input text file", add_chunk_key_txt)
_gather_report_options = __add_gather_options(
    "Output JSON file", "input JSON file", add_chunk_key_report)
_gather_fastq_options = __add_gather_options(
    "Output Fastq file", "Chunk input JSON file", add_chunk_key_fastq)
_gather_fasta_options = __add_gather_options(
    "Output Fasta file", "Chunk input JSON file", add_chunk_key_fasta)
_gather_gff_options = __add_gather_options(
    "Output GFF file", "Chunk input JSON file", add_chunk_key_gff)
_gather_vcf_options = __add_gather_options(
    "Output VCF file", "Chunk input JSON file", add_chunk_key_vcf)
_gather_fofn_options = __add_gather_options(
    "Output Fofn file", "Chunk input JSON file", add_chunk_key_fofn)
_gather_subreadset_options = __add_gather_options("Output SubreadSet XML file",
                                                  "Chunk input JSON file",
                                                  add_chunk_key_subreadset)
_gather_ccsset_options = __add_gather_options("Output ConsensusReadSet XML file",
                                              "Chunk input JSON file",
                                              add_chunk_key_ccsset)
_gather_alignmentset_options = __add_gather_options("Output AlignmentSet XML file",
                                                    "Chunk input JSON file",
                                                    add_chunk_key_alignmentset)
_gather_ccs_alignmentset_options = __add_gather_options("Output ConsensusAlignmentSet XML file",
                                                        "Chunk input JSON file",
                                                        add_chunk_key_ccs_alignmentset)
_gather_transcripts_options = __add_gather_options("Output TranscriptSet XML file",
                                                   "Chunk input JSON file",
                                                   add_chunk_key_transcripts)
_gather_contigset_options = __add_gather_options("Output ContigSet XML file",
                                                 "Chunk input JSON file",
                                                 add_chunk_key_contigset)
_gather_tgz_options = __add_gather_options(
    "Output TGZ file", "input TGZ file", add_chunk_key_tgz)


def __gather_runner(func, chunk_input_json, output_file, chunk_key, **kwargs):
    chunks = load_pipeline_chunks_from_json(chunk_input_json)

    # Allow looseness
    if not chunk_key.startswith('$chunk.'):
        chunk_key = '$chunk.' + chunk_key
        log.warn(
            "Prepending chunk key with '$chunk.' to '{c}'".format(c=chunk_key))

    chunked_files = get_datum_from_chunks_by_chunk_key(chunks, chunk_key)
    _ = func(chunked_files, output_file, **kwargs)
    return 0


def __rtc_gather_runner(func, rtc):
    # Gather Resolved ToolContracts will have a chunk
    return func(rtc.task.input_files[0], rtc.task.output_files[0], rtc.task.chunk_key)


def __args_gather_runner(func, args):
    return __gather_runner(func, args.chunk_json, args.output, args.chunk_key)


# These make assumptions about the CLI argparser args labels (e.g.,
# args.chunk_key)
_args_runner_gather_fasta = P(__args_gather_runner, gather_fasta)
_args_runner_gather_gff = P(__args_gather_runner, gather_gff)
_args_runner_gather_vcf = P(__args_gather_runner, gather_vcf)
_args_runner_gather_fastq = P(__args_gather_runner, gather_fastq)
_args_runner_gather_fastq_contigset = P(
    __args_gather_runner, gather_fastq_contigset)
_args_runner_gather_fofn = P(__args_gather_runner, gather_fofn)
_args_runner_gather_subreadset = P(__args_gather_runner, gather_subreadset)
_args_runner_gather_alignmentset = P(__args_gather_runner, gather_alignmentset)
_args_runner_gather_ccsset = P(__args_gather_runner, gather_ccsset)
_args_runner_gather_ccs_alignmentset = P(
    __args_gather_runner, gather_ccs_alignmentset)
_args_runner_gather_contigset = P(__args_gather_runner, gather_contigset)
_args_runner_gather_transcripts = P(__args_gather_runner, gather_transcripts)
_args_runner_gather_csv = P(__args_gather_runner, gather_csv)
_args_runner_gather_txt = P(__args_gather_runner, gather_txt)
_args_runner_gather_report = P(__args_gather_runner, gather_report)
_args_runner_gather_tgz = P(__args_gather_runner, gather_tgz)

# (chunk.json, output_file, chunk_key)
run_main_gather_fasta = P(__gather_runner, gather_fasta)
run_main_gather_fastq = P(__gather_runner, gather_fastq)
run_main_gather_fastq_contigset = P(__gather_runner, gather_fastq_contigset)
run_main_gather_csv = P(__gather_runner, gather_csv)
run_main_gather_txt = P(__gather_runner, gather_txt)
run_main_gather_report = P(__gather_runner, gather_report)
run_main_gather_gff = P(__gather_runner, gather_gff)
run_main_gather_vcf = P(__gather_runner, gather_vcf)
run_main_gather_alignmentset = P(__gather_runner, gather_alignmentset)
run_main_gather_subreadset = P(__gather_runner, gather_subreadset)
run_main_gather_contigset = P(__gather_runner, gather_contigset)
run_main_gather_ccsset = P(__gather_runner, gather_ccsset)
run_main_gather_ccs_alignmentset = P(__gather_runner, gather_ccs_alignmentset)
run_main_gather_transcripts = P(__gather_runner, gather_transcripts)
run_main_gather_transcript_alignmentset = P(
    __gather_runner, gather_transcript_alignmentset)
run_main_gather_tgz = P(__gather_runner, gather_tgz)
run_main_gather_zip = P(__gather_runner, gather_zip)
run_main_gather_fofn = P(__gather_runner, gather_fofn)
