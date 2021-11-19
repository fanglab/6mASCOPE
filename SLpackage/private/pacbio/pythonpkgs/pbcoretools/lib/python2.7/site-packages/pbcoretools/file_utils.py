
"""
File conversion utility functions.
"""

from collections import defaultdict
import multiprocessing
import tempfile
import zipfile
import logging
import shutil
import uuid
import copy
import csv
import re
import os.path as op
import os

from pbcore.io import (SubreadSet, FastqReader, FastqWriter, BarcodeSet,
                       openDataSet, ConsensusReadSet, DataSet)
from pbcore.io.dataset.DataSetUtils import loadMockCollectionMetadata
from pbcommand.models import FileTypes, DataStore

log = logging.getLogger(__name__)


class Constants(object):
    # default filter applied to output of 'lima'
    BARCODE_QUALITY_GREATER_THAN = 26
    ALLOWED_BC_TYPES = set([f.file_type_id for f in
                            [FileTypes.DS_SUBREADS, FileTypes.DS_CCS]])


def archive_files(input_file_names, output_file_name, remove_path=True):
    """
    Create a zipfile from a list of input files.

    :param remove_path: if True, the directory will be removed from the input
                        file names before archiving.  All inputs and the output
                        file must be in the same directory for this to work.
    """
    archive_file_names = input_file_names
    if remove_path:
        archive_file_names = [op.basename(fn) for fn in archive_file_names]
    log.info("Creating zip file %s", output_file_name)
    with zipfile.ZipFile(output_file_name, "w", zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zip_out:
        for file_name, archive_file_name in zip(input_file_names,
                                                archive_file_names):
            zip_out.write(file_name, archive_file_name)
    return 0


def split_laa_fastq(input_file_name, output_file_base, subreads_file_name,
                    bio_samples_by_bc=None):
    """
    Split an LAA FASTQ file into one file per barcode.
    """
    if op.getsize(input_file_name) == 0:
        return []
    records = defaultdict(list)
    with FastqReader(input_file_name) as fastq_in:
        for rec in fastq_in:
            bc_id = re.sub("^Barcode", "", rec.id.split("_")[0])
            records[bc_id].append(rec)
    if bio_samples_by_bc is None:
        bio_samples_by_bc = {}
        with SubreadSet(subreads_file_name, strict=True) as ds:
            if ds.isBarcoded:
                bio_samples_by_bc = get_barcode_sample_mappings(ds)
    outputs = []
    for bc_id in sorted(records.keys()):
        bio_sample = bio_samples_by_bc.get(bc_id, "unknown")
        ofn = "{b}.{s}.{i}.fastq".format(b=output_file_base, s=bio_sample,
                                         i=bc_id)
        with FastqWriter(ofn) as fastq_out:
            for rec in records[bc_id]:
                fastq_out.writeRecord(rec)
        outputs.append(ofn)
    return outputs


def split_laa_fastq_archived(input_file_name, output_file_name, subreads_file_name):
    """
    Split an LAA FASTQ file into one file per barcode and package as zip.
    """
    base, ext = op.splitext(output_file_name)
    assert (ext == ".zip")
    fastq_files = list(split_laa_fastq(
        input_file_name, base, subreads_file_name))
    if len(fastq_files) == 0:  # workaround for empty input
        with zipfile.ZipFile(output_file_name, "w", allowZip64=True) as zip_out:
            return 0
    return archive_files(fastq_files, output_file_name)


def iterate_datastore_read_set_files(datastore_file,
                                     allowed_read_types=Constants.ALLOWED_BC_TYPES):
    """
    Iterate over dataset (e.g., SubreadSet or ConsensusReadSet) files listed in a datastore JSON.
    """
    ds = DataStore.load_from_json(datastore_file)
    files = ds.files.values()
    for f in files:
        if f.file_type_id in allowed_read_types:
            yield f


def get_barcode_sample_mappings(ds):
    barcoded_samples = []
    for bioSample in ds.metadata.bioSamples:
        for dnaBc in bioSample.DNABarcodes:
            barcoded_samples.append((dnaBc.name, bioSample.name))
    # recover the original barcode FASTA file so we can map the barcode
    # indices in the BAM file to the labels
    bc_sets = {extRes.barcodes for extRes in ds.externalResources
               if extRes.barcodes is not None}
    if len(bc_sets) > 1:
        log.warn("Multiple BarcodeSets detected - further processing skipped.")
    elif len(bc_sets) == 0:
        log.warn("Can't find original BarcodeSet - further processing skipped.")
    else:
        with BarcodeSet(list(bc_sets)[0]) as bcs:
            labels = [rec.id for rec in bcs]
            bam_bc = set()  # barcode labels actually present in BAM files
            for rr in ds.resourceReaders():
                def mk_lbl(i, j): return "{}--{}".format(labels[i], labels[j])
                for fw, rev in zip(rr.pbi.bcForward, rr.pbi.bcReverse):
                    if fw == -1 or rev == -1:
                        continue
                    bam_bc.add(mk_lbl(fw, rev))
            bc_filtered = []
            bc_with_sample = set()
            # exclude barcodes from XML that are not present in BAM
            for bc_label, bio_sample in barcoded_samples:
                bc_with_sample.add(bc_label)
                if not bc_label in bam_bc:
                    log.info("Leaving out %s (not present in BAM files)",
                             bc_label)
                else:
                    bc_filtered.append((bc_label, bio_sample))
            # add barcodes that are in the BAM but not the XML metadata
            for bc_label in list(bam_bc):
                if not bc_label in bc_with_sample:
                    log.info("Adding barcode %s with unknown sample",
                             bc_label)
                    bc_filtered.append((bc_label, "unknown"))
            barcoded_samples = bc_filtered
    return dict(barcoded_samples)


def make_barcode_sample_csv(subreads, csv_file):
    headers = ["Barcode Name", "Bio Sample Name"]
    barcoded_samples = {}
    with SubreadSet(subreads, strict=True) as ds:
        if ds.isBarcoded:
            barcoded_samples = get_barcode_sample_mappings(ds)
    with open(csv_file, "w") as csv_out:
        writer = csv.writer(csv_out, delimiter=',', lineterminator="\n")
        writer.writerow(headers)
        for bc_label in sorted(barcoded_samples.keys()):
            writer.writerow(
                [bc_label, barcoded_samples.get(bc_label, "UnnamedSample")])
    return barcoded_samples


def make_combined_laa_zip(fastq_file, summary_csv, input_subreads, output_file_name):
    tmp_dir = tempfile.mkdtemp()
    summary_csv_tmp = op.join(tmp_dir, "consensus_sequence_statistics.csv")
    shutil.copyfile(summary_csv, summary_csv_tmp)
    barcodes_csv = "Barcoded_Sample_Names.csv"
    bio_samples_by_bc = make_barcode_sample_csv(input_subreads, barcodes_csv)
    fastq_files = split_laa_fastq(fastq_file, "consensus", input_subreads,
                                  bio_samples_by_bc)
    all_files = fastq_files + [summary_csv_tmp, barcodes_csv]
    try:
        return archive_files(all_files, output_file_name)
    finally:
        for file_name in fastq_files + [barcodes_csv]:
            os.remove(file_name)
        shutil.rmtree(tmp_dir)


def consolidate_barcodes(ds, bio_sample):
    deletions = []
    for k, bc in enumerate(bio_sample.DNABarcodes):
        if bc.uniqueId != ds.uuid:
            log.debug("Discarding DNABarcode tag %s", bc)
            deletions.append(k)
    if len(deletions) == len(bio_sample.DNABarcodes):
        bio_sample.DNABarcodes[0].uniqueId = ds.uuid
        deletions = deletions[1:]
    for k in reversed(deletions):
        bio_sample.DNABarcodes.pop(k)


def discard_bio_samples(subreads, barcode_label):
    """
    Remove any BioSample records from a SubreadSet that are not associated
    with the specified barcode.
    """
    deletions = []
    for k, bio_sample in enumerate(subreads.metadata.bioSamples):
        barcodes = set([bc.name for bc in bio_sample.DNABarcodes])
        if barcode_label in barcodes:
            if len(bio_sample.DNABarcodes) > 1:
                consolidate_barcodes(subreads, bio_sample)
            continue
        if len(barcodes) == 0:
            log.warn("No barcodes defined for sample %s", bio_sample.name)
        deletions.append(k)
    for k in reversed(deletions):
        subreads.metadata.bioSamples.pop(k)
    if len(subreads.metadata.bioSamples) == 0:
        log.warn("Dataset has no BioSamples")
        log.warn("Will create new BioSample and DNABarcode records")
        subreads.metadata.bioSamples.addSample(barcode_label)
        subreads.metadata.bioSamples[0].DNABarcodes.addBarcode(barcode_label)


def get_bio_sample_name(ds):
    bio_samples = {s.name for s in ds.metadata.bioSamples}
    if len(bio_samples) == 0:
        log.warn("No BioSample records present")
        return "UnnamedSample"
    elif len(bio_samples) > 1:
        log.warn("Multiple unique BioSample records present")
        return "multiple_samples"
    else:
        return list(bio_samples)[0]


def get_ds_name(ds, base_name, barcode_label):
    """
    Given the base (parent) dataset name, add a suffix indicating sample
    """
    suffix = "(unknown sample)"
    try:
        n_samples = len(ds.metadata.bioSamples)
        if n_samples == 1:
            suffix = "(%s)" % ds.metadata.bioSamples[0].name
        elif n_samples > 1:
            suffix = "(multiple samples)"
        else:
            raise IndexError("No BioSample records present")
    except IndexError:
        if barcode_label is not None:
            suffix = "({l})".format(l=barcode_label)
    return "{n} {s}".format(n=base_name, s=suffix)


def _get_uuid(ds, barcode_label):
    for bio_sample in ds.metadata.bioSamples:
        for dna_bc in bio_sample.DNABarcodes:
            if dna_bc.name == barcode_label and dna_bc.uniqueId:
                return dna_bc.uniqueId


def uniqueify_collections(metadata):
    uuids = set()
    deletions = []
    for k, collection in enumerate(metadata.collections):
        if collection.uniqueId in uuids:
            deletions.append(k)
        uuids.add(collection.uniqueId)
    for k in reversed(deletions):
        metadata.collections.pop(k)


# XXX this is a separate function to enable mocking using non-barcoded BAMs
def _update_barcoded_dataset(
        dataset,
        datastore_file,
        barcode_pair,
        barcode_names,
        parent_info,
        use_barcode_uuids,
        bio_samples_d,
        barcode_uuids_d,
        output_file,
        min_score_filter=Constants.BARCODE_QUALITY_GREATER_THAN):
    parent_uuid, parent_type, parent_name = parent_info
    barcode_label = None
    bcf, bcr = barcode_pair
    barcode_label = "{f}--{r}".format(f=barcode_names[bcf],
                                      r=barcode_names[bcr])
    discard_bio_samples(dataset, barcode_label)
    sample_name = bio_samples_d.get(barcode_label, None)
    if sample_name is not None:
        force_set_all_bio_sample_names(dataset, sample_name)
    assert parent_type == dataset.datasetType
    dataset.subdatasets = []
    dataset.metadata.addParentDataSet(parent_uuid,
                                      parent_type,
                                      createdBy="AnalysisJob",
                                      timeStampedName="")
    dataset.name = get_ds_name(dataset, parent_name, barcode_label)
    if min_score_filter is not None:
        dataset.filters.addRequirement(bq=[('>', min_score_filter)])
    if use_barcode_uuids:
        uuid = barcode_uuids_d.get(barcode_label, None)
        if uuid is not None:
            dataset.objMetadata["UniqueId"] = uuid
            log.info("Set dataset UUID to %s", dataset.uuid)
        else:
            log.warn("No UUID defined for this barcoded dataset.")
            dataset.newUuid()
    else:
        dataset.newUuid()
    dataset.updateCounts()
    dataset.write(output_file)
    f_new = copy.deepcopy(datastore_file)
    f_new.name = dataset.name
    f_new.path = output_file
    f_new.uuid = dataset.uuid
    return f_new


def _update_barcoded_sample_metadata(
        base_dir,
        ds_file,
        barcode_names,
        parent_info,
        isoseq_mode,
        use_barcode_uuids,
        bio_samples_d,
        barcode_uuids_d,
        min_score_filter=Constants.BARCODE_QUALITY_GREATER_THAN,
        require_file_id="barcoding.tasks.lima-0"):
    # the unbarcoded BAM is also a ConsensusReadSet right now, but we
    # shouldn't rely on that
    assert require_file_id is None or ds_file.file_id == require_file_id
    ds_out = op.join(base_dir, op.basename(ds_file.path))
    with openDataSet(ds_file.path, strict=True) as ds:
        assert ds.datasetType in Constants.ALLOWED_BC_TYPES, ds.datasetType
        uniqueify_collections(ds.metadata)
        barcode_label = None
        ds_barcodes = sorted(
            list(set(zip(ds.index.bcForward, ds.index.bcReverse))))
        if isoseq_mode:
            ds_barcodes = sorted(
                list(set([tuple(sorted(bcs)) for bcs in ds_barcodes])))
        if len(ds_barcodes) > 1:
            raise IOError(
                "The file {f} contains multiple barcodes: {b}".format(
                    f=ds_file.path, b="; ".join([str(bc) for bc in ds_barcodes])))
        return _update_barcoded_dataset(ds, ds_file, ds_barcodes[0], barcode_names, parent_info, use_barcode_uuids, bio_samples_d, barcode_uuids_d, ds_out, min_score_filter)


def _mock_update_barcoded_sample_metadata(
        base_dir,
        ds_file,
        barcode_names,
        parent_info,
        use_barcode_uuids,
        barcode_pair,
        bio_samples_d,
        barcode_uuids_d,
        min_score_filter=None):
    ds_out = op.join(base_dir, op.basename(ds_file.path))
    with openDataSet(ds_file.path, skipCounts=True) as ds:
        assert ds.datasetType in Constants.ALLOWED_BC_TYPES, ds.datasetType
        uniqueify_collections(ds.metadata)
        return _update_barcoded_dataset(ds, ds_file, barcode_pair, barcode_names, parent_info, use_barcode_uuids, bio_samples_d, barcode_uuids_d, ds_out, min_score_filter=None)


def _load_files_for_update(
        input_reads,
        barcode_set,
        datastore_file,
        require_file_id="barcoding.tasks.lima-0"):
    barcode_names = []
    with BarcodeSet(barcode_set) as bc_in:
        for rec in bc_in:
            barcode_names.append(rec.id)
    parent_ds = openDataSet(input_reads)
    parent_info = (parent_ds.uuid, parent_ds.datasetType, parent_ds.name)
    update_files = []
    for f in iterate_datastore_read_set_files(datastore_file):
        if require_file_id is None or f.file_id == require_file_id:
            update_files.append(f)
    bio_samples_d = {}
    barcode_uuids_d = {}
    for bio_sample in parent_ds.metadata.bioSamples:
        for dnabc in bio_sample.DNABarcodes:
            bio_samples_d[dnabc.name] = bio_sample.name
            barcode_uuids_d[dnabc.name] = dnabc.uniqueId
    return barcode_names, bio_samples_d, barcode_uuids_d, update_files, parent_info


def update_barcoded_sample_metadata(
        base_dir,
        datastore_file,
        input_reads,
        barcode_set,
        isoseq_mode=False,
        use_barcode_uuids=True,
        nproc=1,
        min_score_filter=Constants.BARCODE_QUALITY_GREATER_THAN):
    """
    Given a datastore JSON of SubreadSets produced by barcoding, apply the
    following updates to each:
    1. Include only the BioSample(s) corresponding to its barcode
    2. Add the BioSample name to the dataset name
    3. Add a ParentDataSet record in the Provenance section.
    """
    barcode_names, bio_samples_d, barcode_uuids_d, update_files, parent_info = _load_files_for_update(
        input_reads, barcode_set, datastore_file)
    pool = multiprocessing.Pool(nproc)
    _results = []
    for ds_file in update_files:
        _results.append(
            pool.apply_async(_update_barcoded_sample_metadata,
                             (base_dir,
                              ds_file,
                              barcode_names,
                              parent_info,
                              isoseq_mode,
                              use_barcode_uuids,
                              bio_samples_d,
                              barcode_uuids_d,
                              min_score_filter)))
    pool.close()
    pool.join()
    datastore_files = [r.get() for r in _results]
    # copy over the un-barcoded reads BAM
    dstore = DataStore.load_from_json(datastore_file)
    files = dstore.files.values()
    for f in files:
        if f.file_id != "barcoding.tasks.lima-0":
            datastore_files.append(f)
    return DataStore(datastore_files)


def mock_update_barcoded_sample_metadata(
        base_dir,
        datastore_file,
        input_reads,
        barcode_set,
        use_barcode_uuids=True):
    """
    Function to mimic the actual update function, without actually reading
    any barcoding information from the datasets.  Instead, the barcodes
    defined in the input dataset will be applied sequentially.
    """
    barcode_names, bio_samples_d, barcode_uuids_d, update_files, parent_info = _load_files_for_update(
        input_reads, barcode_set, datastore_file, None)
    barcode_ids = {name: i for i, name in enumerate(barcode_names)}
    bc_pairs = []
    ds_files = {}
    for bc_label in barcode_uuids_d.keys():
        bc_fw_label, bc_rev_label = bc_label.split("--")
        bc_pairs.append((barcode_ids[bc_fw_label], barcode_ids[bc_rev_label]))
        suffix = ".{l}.subreadset.xml".format(l=bc_label)
        for ds_file in update_files:
            if ds_file.path.endswith(suffix):
                ds_files[bc_pairs[-1]] = ds_file
    new_files = []
    assert len(bc_pairs) >= len(update_files)
    for bc_pair in bc_pairs:
        ds_file = ds_files[bc_pair]
        new_files.append(_mock_update_barcoded_sample_metadata(
            base_dir,
            ds_file,
            barcode_names,
            parent_info,
            use_barcode_uuids,
            bc_pair,
            bio_samples_d,
            barcode_uuids_d))
    return DataStore(new_files)


def add_mock_collection_metadata(ds):
    """
    For every movie defined in the BAM headers, add a CollectionMetadata
    object with dummy values if one does not already exist.  The 'Context'
    field will be set to the movie name.
    """
    have_movies = {c.context for c in ds.metadata.collections}
    all_movie_names = set([rg.MovieName for rg in ds.readGroupTable])
    new_movie_names = sorted(list(all_movie_names - have_movies))
    for movie_name in new_movie_names:
        coll = loadMockCollectionMetadata()
        coll.context = movie_name
        # This is not really ideal, since it's supposed to correspond to the
        # original SubreadSet UUID (I think).  But as long as it's unique, it
        # shouldn't matter for downstream apps.
        coll.uniqueId = uuid.uuid4()
        ds.metadata.collections.append(coll)
    return len(new_movie_names)


def force_set_all_well_sample_names(ds, sample_name):
    """
    Set the WellSample name for all collections in the dataset metadata.
    """
    for collection in ds.metadata.collections:
        collection.wellSample.name = sample_name


def force_set_all_bio_sample_names(ds, sample_name):
    """
    Set the BioSample name(s) (adding new records if necessary) for a dataset.

    :return: the number of BioSamples modified (including new samples)
    """
    n_total = 0
    bioSamples = ds.metadata.bioSamples
    n_samples = len(bioSamples)
    n_total += max(1, n_samples)
    if n_samples == 0:
        log.debug("Adding new BioSample '%s' to dataset", sample_name)
        bioSamples.addSample(sample_name)
    elif n_samples == 1:
        bioSamples[0].name = sample_name
    else:
        log.warn("Multiple BioSamples found: '%s'",
                 "', '".join([s.name for s in bioSamples]))
        log.warn("These will be overwritten with '%s'", sample_name)
        for sample in bioSamples:
            sample.name = sample_name
    return n_total


# Regular expression pattern of sample strings: must be a string
# of length >= 1, the leading character must be a letter or number,
# the remaining characters must be in [a-zA-Z0-9\_\-]
SAMPLE_CHARSET_RE_STR = '[a-zA-Z0-9\-\_]'
SAMPLE_CHARSET_RE = re.compile(r"{}".format(SAMPLE_CHARSET_RE_STR))


def sanitize_sample(sample):
    """Simple method to sanitize sample to match sample pattern
    ...doctest:
        >>> def a_generator(): return 'a'
        >>> sanitize_sample('1' * 20) # no length limit
        '11111111111111111111'
        >>> sanitize_sample('-123')
        '-123'
        >>> sanitize_sample('123 !&?') # all invalid characters go to '_'
        '123____'
    """
    if len(sample) == 0:
        raise ValueError('Sample must not be an empty string')
    sanitized_sample = ''
    for c in sample:
        if not SAMPLE_CHARSET_RE.search(c):
            c = '_'
        sanitized_sample += c
    return sanitized_sample


def get_sanitized_bio_sample_name(ds):
    """Return sanitized biosample name"""
    sample = get_bio_sample_name(ds)
    ssample = sanitize_sample(sample)
    log.warning(
        "Sanitize biosample name from {!r} to {!r}".format(sample, ssample))
    return ssample


def get_prefixes(ds_file):
    if not ds_file.endswith('.subreadset.xml') and not ds_file.endswith('.consensusreadset.xml'):
        raise ValueError("Unsupported readtype {}, must either be SubreadSet or ConsensusReadSet!".
                         format(ds_file))
    cls = SubreadSet if ds_file.endswith(
        'subreadset.xml') else ConsensusReadSet
    with cls(ds_file) as ds:
        seqid_prefix = get_sanitized_bio_sample_name(ds)
        return ("{}_HQ_".format(seqid_prefix), "{}_LQ_".format(seqid_prefix))


def sanitize_dataset_tags(dset, remove_hidden=False):
    tags = {t.strip() for t in dset.tags.split(",")}
    if "chunked" in tags or "filtered" in tags:
        tags.discard("chunked")
        tags.discard("filtered")
    if "hidden" in tags and remove_hidden:
        tags.discard("hidden")
    if "" in tags:
        tags.discard("")
    dset.tags = ",".join(sorted(list(tags)))
    name_fields = dset.name.split()
    if "(filtered)" in name_fields:
        name_fields.remove("(filtered)")
    dset.name = " ".join(name_fields)


def reparent_dataset(input_file, dataset_name, output_file):
    with openDataSet(input_file, strict=True) as ds_in:
        if len(ds_in.metadata.provenance) > 0:
            log.warn("Removing existing provenance record: %s",
                     ds_in.metadata.provenance)
            ds_in.metadata.provenance = None
        ds_in.name = dataset_name
        ds_in.newUuid(random=True)
        sanitize_dataset_tags(ds_in, remove_hidden=True)
        ds_in.write(output_file)
    return 0


def update_consensus_reads(ccs_in, subreads_in, ccs_out, use_run_design_uuid=False):
    ds_subreads = SubreadSet(subreads_in, skipCounts=True)
    with ConsensusReadSet(ccs_in) as ds:
        ds.name = ds_subreads.name + " (CCS)"
        run_design_uuid = None
        if use_run_design_uuid:
            uuids = set([])
            for collection in ds.metadata.collections:
                if collection.consensusReadSetRef is not None:
                    uuids.add(collection.consensusReadSetRef.uuid)
            if len(uuids) == 1:
                run_design_uuid = list(uuids)[0]
            elif len(uuids) == 0:
                log.warn("No pre-defined ConsensusReadSetRef UUID found")
            else:
                log.warn("Multiple ConsensusReadSetRef UUIDs found")
        if len(ds.metadata.bioSamples) == 0:
            for bio_sample in ds_subreads.metadata.bioSamples:
                ds.metadata.bioSamples.append(bio_sample)
        if run_design_uuid is not None:
            ds.uuid = run_design_uuid
        else:
            ds.newUuid()
        sanitize_dataset_tags(ds, remove_hidden=True)
        ds.write(ccs_out)
    return 0
