"""
Create simulated FASTQ files to test UMI/deduplication, adaptor
trimming, and demultiplexing.

The following files are created.

Reads with 5' UMI, 3' UMI and adaptor:

* Prefix: ``umi5_umi3``.
* These files can be used to test adaptor trimming and deduplication.
* ``umi5_umi3_umi_adaptor.fastq``: FASTQ file with 9 reads, each with
  a 4nt UMI at the 5' end, a 4nt UMI at the 3' end and a 11nt adaptor
  at the 3' end. Reads can be grouped by UMI into 5 groups.
* ``umi5_umi3_umi.fastq``: FASTQ file identical to the above but with
  the adaptor trimmed.
* ``umi5_umi3.fastq``: FASTQ file identical to the above but with the
  UMIs extracted and concatenated to the header, with a ``_``
  delimiter.

Reads with 5' UMI, 3' UMI and adaptor:

* Prefix: ``umi3``.
* These files can be used to test adaptor trimming and deduplication.
* ``umi3_umi_adaptor.fastq``: FASTQ file with 8 reads, each with a 4nt
  UMI at the 3' end and a 11nt adaptor at the 3' end. Reads can be
  grouped by UMI into 4 groups.
* ``umi3_umi.fastq``: FASTQ file identical to the above but with the
  adaptor trimmed.
* ``umi3.fastq``: FASTQ file identical to the above but with the UMI
  extracted and concatenated to the header, with a ``_`` delimiter.

Reads with 5' UMI, 3' UMI, adaptor and barcode:

* Prefix: ``multiplex``.
* These files can be used to test adaptor trimming, demultiplexing and
  deduplication.
* ``multiplex_barcodes.tsv``: tab-separated values file with
  ``SampleID`` column (with values ``Tag0|1|2``) and ``TagRead``
  column (with values ``ACG``, ``GAC``, ``CGA``). This is consistent
  with the sample sheet file format expected by
  :py:mod:`riboviz.tools.demultiplex_fastq` and
  :py:mod:`riboviz.demultiplex_fastq`.
* ``multiplex_umi_barcode_adaptor.fastq``: FASTQ file with 90 reads:
    - Each read has a 4nt UMI at the 5' end, a 4nt UMI at the 3' end,
      a 3nt barcode at the 3' end and a 11nt adaptor at the 3' end.
    - There are 9 reads for each of the following barcodes:
        - ``ACG``, ``ACT``, ``TAG``
        - ``GAC``, ``GTC``, ``GTA``
        - ``CGA``, ``TGA``, ``CTT``
    - The second and third barcodes in each list have a mismatch of
      1nt and 2nt respectively with the first barcode in each list.
    - When the file is demultiplexed, assuming up to 2 mismatches are
      allowed, then 3 sets of 27 reads will be produced, grouped by
      the 1st barcode in each list.
    - There are 9 reads with barcode ``TTT``, which has a mismatch of
      3nts to ``ACG``, ``GAC``, ``CGA``. When the file is
      demultiplexed, assuming up to 2 mismatches are allowed, then
      these 9 reads will be unassigned.
* ``multiplex_umi_barcode.fastq``: FASTQ file identical to the above
  but with the adaptor trimmed.
* ``multiplex.fastq``: FASTQ file identical to the above but with the
  barcode and UMIs extracted into the header and delimited by ``_``.
* ``deplex/Tag0|1|2.fastq``: FASTQ files each with 27 reads
  representing the results expected when demultiplexing
  ``multiplex.fastq`` using :py:mod:`riboviz.tools.demultiplex_fastq`
  with ``multiplex_barcodes.tsv`` and 2 allowed mismatches.
* ``deplex/Unassigned.fastq``: FASTQ files with 9 reads representing
  the unassigned reads (those with barcode ``TTT``) expected when
  demultiplexing ``multiplex.fastq`` using
  :py:mod:`riboviz.tools.demultiplex_fastq` with
  ``multiplex_barcodes.tsv`` and 2 allowed mismatches.
* ``deplex/num_reads.tsv``: tab-separated values with expected counts of
  reads for each barcode expected when demultiplexing
  ``multiplex.fastq`` using :py:mod:`riboviz.tools.demultiplex_fastq`
  with ``multiplex_barcodes.tsv`` and 2 allowed mismatches.
"""
import os
import os.path
from random import choices
from random import seed
import shutil
import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from riboviz import barcodes_umis
from riboviz import demultiplex_fastq
from riboviz import fastq
from riboviz import sample_sheets

QUALITY_MEDIUM = list(range(30, 41))
""" List of medium quality scores. """
QUALITY_HIGH = list(range(39, 41))
""" List of high quality scores. """


def simulate_quality(k, qualities=QUALITY_MEDIUM, weights=None):
    """
    Simulate quality scores. This is a thin wrapper around Python
    `random.choices` whose default values represent medium Phred quality
    values. See
    https://docs.python.org/3/library/random.html#random.choices.

    :param k: Number of quality scores requested
    :type k: int
    :param qualities: Available quality scores
    :type qualities: list(int)
    :param weights: Optional weightings for qualities
    :type weights: list(ints)
    :return k: quality scores, selected at random from qualities
    :rtype: list(int)
    """
    return choices(qualities, k=k, weights=weights)


def make_fastq_record(name, reads, scores=None, qualities=QUALITY_MEDIUM):
    """
    Make a FASTQ record with a sequence ``reads`` and name
    ``name``.

    :param name: Name
    :type name: str or unicode
    :param reads: Reads
    :type reads: str or unicode
    :param scores: Quality scores
    :type scores: list(int)
    :param qualities: Available quality scores, used if scores is \
    ``None``, in conjunction with :py:func:`simulate_quality` \
    to calculate quality scores
    :type qualities: list(int)
    :return: fastq record
    :rtype: Bio.SeqRecord.SeqRecord
    """
    if scores is None:
        scores = simulate_quality(len(reads), qualities=qualities)
    record = SeqRecord(Seq(reads),
                       id=name,
                       name=name,
                       description=name)
    record.letter_annotations["phred_quality"] = scores
    return record


def trim_fastq_record_3prime(record,
                             trim,
                             add_trim=False,
                             delimiter=barcodes_umis.UMI_DELIMITER):
    """
    Copy FASTQ record, but trim sequence and quality scores at 3' end
    by given length.

    :param record: Record
    :type record: Bio.SeqRecord.SeqRecord
    :param trim: Number of nts to trim by
    :type trim: int
    :param delimiter: Delimiter to use, if ``add_trim`` is ``True``
    :type delimiter: str or unicode
    :param add_trim: Add subsequence that was trimmed to record ID?
    :type add_trim: bool
    :return: New record
    :rtype: Bio.SeqRecord.SeqRecord
    """
    quality = record.letter_annotations["phred_quality"]
    sequence = str(record.seq)
    record_extension = ""
    if add_trim:
        record_extension = delimiter + sequence[-trim:]
    return make_fastq_record(record.id + record_extension,
                             sequence[0:-trim],
                             quality[0:-trim])


def trim_fastq_record_5prime(record,
                             trim,
                             add_trim=False,
                             delimiter=barcodes_umis.UMI_DELIMITER):
    """
    Copy FASTQ record, but trim sequence and quality scores at 5' end
    by given length.

    :param record: Record
    :type record: Bio.SeqRecord.SeqRecord
    :param trim: Number of nts to trim by
    :type trim: int
    :param add_trim: Add subsequence that was trimmed to record ID?
    :type add_trim: bool
    :param delimiter: Delimiter to use, if ``add_trim`` is ``True``
    :type delimiter: str or unicode
    :return: New record
    :rtype: Bio.SeqRecord.SeqRecord
    """
    quality = record.letter_annotations["phred_quality"]
    sequence = str(record.seq)
    record_extension = ""
    if add_trim:
        record_extension = delimiter + sequence[0:trim]
    return make_fastq_record(record.id + record_extension,
                             sequence[trim:],
                             quality[trim:])


def make_fastq_records(tag,
                       read,
                       qualities,
                       umi5="",
                       umi3="",
                       barcode="",
                       adaptor="",
                       post_adaptor_nt=""):
    """
    Create a set of complementary FASTQ records.

    * A record for sequence: ``umi5`` + ``read`` + ``umi3`` +
      ``barcode`` + ``adaptor`` + ``post_adaptor_nt``.
    * A record as above with ``adaptor`` and ``post_adaptor_nt``
      trimmed: ``umi5`` + ``read`` + ``umi3`` + ``barcode``.
        - If ``adaptor`` and ``post_adaptor_nt`` are both ``''`` then
          this is equivalent to the above record.
    * A record as above with the barcode and UMIs trimmed and added to
      the header with ``_`` delimiters: ``read``.
        - If both the barcode and both UMIs are ``''`` then this is
          equivalent to the above record.
        - Depending on whether ``barcode``, ``umi5`` and ``umi3`` are
          ``''``  the header will be extended with one of:
            - ``<barcode>_<umi5><umi3>``
            - ``<barcode>_<umi3>``
            - ``_<umi5><umi3>``
            - ``<umi3>``

    :param tag: Human-readable tag
    :type tag: str or unicode
    :param read: Read
    :type read: str or unicode
    :param qualities: Available quality scores
    :type qualities: list(int)
    :param umi5: 5' end UMI
    :type umi5: str or unicode
    :param umi3: 3' end UMI
    :type umi3: str or unicode
    :param barcode: 3' end barcode
    :type barcode: str or unicode
    :param adaptor: 3' end adaptor
    :type adaptor: str or unicode
    :param post_adaptor_nt: 3' end post-adaptor nts
    :type post_adaptor_nt: str or unicode
    :return: full record, adaptor-trimmed record, barcode- and \
    UMI-extracted record
    :rtype: tuple(Bio.SeqRecord.SeqRecord, Bio.SeqRecord.SeqRecord, \
    Bio.SeqRecord.SeqRecord)
    """
    sequence = umi5 + read + umi3 + barcode + adaptor + post_adaptor_nt
    record = make_fastq_record(tag, sequence, qualities=qualities)
    # Record after adaptor trimming.
    trim_record = trim_fastq_record_3prime(
        record,
        len(adaptor) + len(post_adaptor_nt))
    if barcode != "":
        # Add barcode to record ID, using "_" delimiter for consistency
        # with UMI-tools.
        barcode_ext_record = trim_fastq_record_3prime(
            trim_record,
            len(barcode),
            True,
            barcodes_umis.BARCODE_DELIMITER)
    else:
        barcode_ext_record = trim_record
    umi3_delimiter = barcodes_umis.UMI_DELIMITER
    if umi5 != "":
        # Record after 5' UMI extraction.
        # Add UMI to record ID, using "_" delimiter for consistency
        # with UMI-tools.
        umi5_ext_record = trim_fastq_record_5prime(
            barcode_ext_record,
            len(umi5),
            True,
            barcodes_umis.UMI_DELIMITER)
        umi3_delimiter = ""
    else:
        umi5_ext_record = barcode_ext_record
    # Record after 3' UMI extraction.
    # Add UMI to record ID, using "_" delimiter for consistency
    # with UMI-tools, unless 5' UMI has been extracted, in which case
    # use "".
    umi3_ext_record = trim_fastq_record_3prime(
        umi5_ext_record,
        len(umi3),
        True,
        umi3_delimiter)
    return (record, trim_record, umi3_ext_record)


def create_fastq_simdata(output_dir):
    """
    Create simulated FASTQ files to test UMI/deduplication, adaptor
    trimming, and demultiplexing.

    :param output_dir: Output directory
    :type output_dir: str or unicode
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    make_fastq_record("SRR", "AAAA")
    seed(42)  # Fix random seed so can repeatedly create same files

    # Components for simulated reads compatible with the vignette
    # files yeast_yAL_CDS_w_250utrs.fa.
    # These are aimed at the Duncan & Mata format with 4nt UMI at
    # each end of read.
    read_a = "ATGGCATCCACCGATTTCTCCAAGATTGAA"  # 30nt starting ORF of YAL003W
    read_ae = "ATGGCATCCACCGATGTCTCCAAGATTGAA"  # 1 error in read A
    read_b = "TCTAGATTAGAAAGATTGACCTCATTAA"  # 28nt immediately following start of ORF of YAL038W

    # UMIs
    umi_x = "CGTA"
    umi_y = "ATAT"
    umi_ye = "ATAA"  # 1 error in umi_y
    umi_z = "CGGC"
    umi_ze = "CTGC"  # 1 error in umi_x
    umi_5 = "AAAA"
    umi_5c = "CCCC"

    adaptor = "CTGTAGGCACC"  # Adaptor sequence used in vignette data

    post_adaptor_nt = "AC"

    # Create raw data with 5' and 3' UMIs and an adaptor.
    # M.N in the record names note the group the record is expected
    # belong to (M) and its number within that group.
    # After deduplication there should only be 1 member of each
    # group.
    config_5_3_adaptor = [
        ["EWSim-1.1-umi5-reada-umix", umi_5, read_a, umi_x, QUALITY_HIGH],
        ["EWSim-1.2-umi5-reada-umix", umi_5, read_a, umi_x, QUALITY_MEDIUM],
        ["EWSim-1.3-umi5-readae-umix", umi_5, read_ae, umi_x, QUALITY_MEDIUM],
        ["EWSim-2.1-umi5-reada-umiy", umi_5, read_a, umi_y, QUALITY_MEDIUM]
    ]
    # Create raw data with 5' and 3' UMIs and an adaptor plus an
    # extra nt past the "", adaptor for the shorter read.
    config_5_3_post_adaptor_nt = [
        ["EWSim-3.1-umi5-readb-umix", umi_5, read_b, umi_x, QUALITY_MEDIUM],
        ["EWSim-4.1-umi5-readb-umiz", umi_5, read_b, umi_z, QUALITY_HIGH],
        ["EWSim-4.2-umi5-readb-umiz", umi_5, read_b, umi_z, QUALITY_MEDIUM],
        ["EWSim-4.3-umi5-readb-umize", umi_5, read_b, umi_ze, QUALITY_MEDIUM],
        ["EWSim-5.1-umi5c-readb-umix", umi_5c, read_b, umi_x, QUALITY_MEDIUM]
    ]
    records = [
        make_fastq_records(tag, read, qualities, umi5, umi3, "", adaptor)
        for [tag, umi5, read, umi3, qualities] in config_5_3_adaptor]
    records_post_adaptor_nt = [
        make_fastq_records(tag, read, qualities, umi5, umi3, "",
                           adaptor, post_adaptor_nt)
        for [tag, umi5, read, umi3, qualities] in config_5_3_post_adaptor_nt]
    records.extend(records_post_adaptor_nt)
    file_names = ["umi5_umi3_umi_adaptor",
                  "umi5_umi3_umi",
                  "umi5_umi3"]
    file_names = [fastq.FASTQ_FORMAT.format(f) for f in file_names]
    for file_name, fastq_records in zip(file_names, zip(*records)):
        with open(os.path.join(output_dir, file_name), "w") as f:
            SeqIO.write(fastq_records, f, "fastq")

    # Simulate raw data with only 3' umi.
    config_3 = [
        ["EWSim-1.1-reada-umix", read_a, umi_x, QUALITY_HIGH],
        ["EWSim-1.2-reada-umix", read_a, umi_x, QUALITY_MEDIUM],
        ["EWSim-1.3-readae-umix", read_ae, umi_x, QUALITY_MEDIUM],
        ["EWSim-2.1-reada-umiy", read_a, umi_y, QUALITY_MEDIUM],
        ["EWSim-3.1-readb-umix", read_b, umi_x, QUALITY_MEDIUM],
        ["EWSim-4.1-readb-umiz", read_b, umi_z, QUALITY_HIGH],
        ["EWSim-4.2-readb-umiz", read_b, umi_z, QUALITY_MEDIUM],
        ["EWSim-4.3-readb-umize", read_b, umi_ze, QUALITY_MEDIUM],
    ]
    records = [
        make_fastq_records(tag, read, qualities, "", umi3, "", adaptor)
        for [tag, read, umi3, qualities] in config_3]
    file_names = ["umi3_umi_adaptor",
                  "umi3_umi",
                  "umi3"]
    file_names = [fastq.FASTQ_FORMAT.format(f) for f in file_names]
    for file_name, fastq_records in zip(file_names, zip(*records)):
        with open(os.path.join(output_dir, file_name), "w") as f:
            SeqIO.write(fastq_records, f, "fastq")

    # Create multiplexed data.
    # Use same data as 5' and 3' UMIs and an adaptor but with
    # barcodes.
    # Barcodes (keys) each with list of barcodes with 1-nt and 2-nt
    # mismatches.
    barcode_sets = [['ACG', 'GAC', 'CGA'],  # Barcodes
                    ['ACT', 'GTC', 'TGA'],  # 1nt mismatches
                    ['TAG', 'GTA', 'CTT']]  # 2nt mismatches
    barcode_names = barcode_sets[0]
    num_barcodes = len(barcode_names)
    barcode_format = "-bar{:01d}.{:01d}"
    tag_format = "Tag{:01d}"
    deplex_dir = os.path.join(output_dir, "deplex")
    os.mkdir(deplex_dir)

    # Create sample-sheet.
    sample_sheet = pd.DataFrame(columns=[sample_sheets.SAMPLE_ID,
                                         sample_sheets.TAG_READ])
    sample_rows = []
    for index, barcode in enumerate(barcode_sets[0]):
        sample_rows.append([tag_format.format(index), barcode])
    sample_rows_df = pd.DataFrame(sample_rows, columns=sample_sheet.columns)
    sample_sheet = sample_sheet.append(sample_rows_df, ignore_index=True)
    sample_sheet[list(sample_sheet.columns)].to_csv(
        os.path.join(output_dir, "multiplex_barcodes.tsv"),
        sep="\t", index=False)

    # Barcode that will be unassigned during demultiplexing.
    barcode_sets[0].append('TTT')
    unassigned_index = num_barcodes
    num_reads_per_barcode = [0] * (num_barcodes + 1)
    # Iterate over mismatches then barcodes so can interleave reads
    # for each barcode i.e. reads for each barcodes will be created
    # first then the reads for the 1nt mismatches then those for 2nt
    # mismatches.
    for mismatch_index, barcodes in enumerate(barcode_sets):
        for barcode_index, barcode in enumerate(barcodes):
            records = [
                make_fastq_records(tag +
                                   barcode_format.format(barcode_index,
                                                         mismatch_index),
                                   read, qualities,
                                   umi5, umi3, barcode,
                                   adaptor, "")
                for [tag, umi5, read, umi3, qualities] in config_5_3_adaptor]
            records_post_adaptor_nt = [
                make_fastq_records(tag +
                                   barcode_format.format(barcode_index,
                                                         mismatch_index),
                                   read, qualities,
                                   umi5, umi3, barcode,
                                   adaptor, post_adaptor_nt)
                for [tag, umi5, read, umi3, qualities] in
                config_5_3_post_adaptor_nt]
            records.extend(records_post_adaptor_nt)
            num_reads_per_barcode[barcode_index] += len(records)
            # ZIP records into three lists: UMI+barcode+adaptor
            # records, UMI+barcode records, records with UMI+barcode
            # extracted
            records_by_type = list(zip(*records))
            file_names = ["multiplex_umi_barcode_adaptor",
                          "multiplex_umi_barcode",
                          "multiplex"]
            file_names = [fastq.FASTQ_FORMAT.format(f) for f in file_names]
            for file_name, fastq_records in zip(file_names, records_by_type):
                with open(os.path.join(output_dir, file_name), "a") as f:
                    SeqIO.write(fastq_records, f, "fastq")
            # Save records with UMI+barcode extracted in
            # barcode-specific files.
            _, _, extracted_records = records_by_type
            file_name = fastq.FASTQ_FORMAT.format(
                tag_format.format(barcode_index))
            with open(os.path.join(deplex_dir, file_name), "a") as f:
                SeqIO.write(extracted_records, f, "fastq")

    # The last file of barcode-specific reads will be that for the
    # unassigned reads so rename that file.
    unassigned_tag_filename = fastq.FASTQ_FORMAT.format(
        tag_format.format(unassigned_index))
    shutil.move(os.path.join(deplex_dir, unassigned_tag_filename),
                os.path.join(deplex_dir,
                             fastq.FASTQ_FORMAT.format(
                                 sample_sheets.UNASSIGNED_TAG)))

    # Save expected demultiplexing data on counts of reads per-barcode.
    num_unassigned_reads = num_reads_per_barcode[unassigned_index]
    del num_reads_per_barcode[unassigned_index]
    sample_sheet[sample_sheets.NUM_READS] = num_reads_per_barcode
    sample_sheets.save_deplexed_sample_sheet(
        sample_sheet,
        num_unassigned_reads,
        os.path.join(deplex_dir, demultiplex_fastq.NUM_READS_FILE))
