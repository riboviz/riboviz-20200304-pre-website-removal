"""
:py:mod:`riboviz.fastq` tests.
"""
import gzip
import itertools
import os
import tempfile
import pytest
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from riboviz import fastq
from riboviz.barcodes_umis import NUCLEOTIDES


@pytest.fixture(scope="function", params=fastq.FASTQ_EXTS)
def tmp_file(request):
    """
    Create a temporary file with a FASTQ suffix.

    :param request: SubRequest with ``param`` member which has \
    a FASTQ suffix
    :type request: _pytest.fixtures.SubRequest
    :return: path to temporary file
    :rtype: str or unicode
    """
    _, tmp_file = tempfile.mkstemp(prefix="tmp",
                                   suffix="." + request.param)
    yield tmp_file
    if os.path.exists(tmp_file):
        os.remove(tmp_file)


@pytest.fixture(scope="function", params=fastq.FASTQ_GZ_EXTS)
def tmp_gz_file(request):
    """
    Create a temporary file with a FASTQ GZIP suffix.

    :param request: SubRequest with ``param`` member which has \
    a FASTQ GZipped suffix
    :type request: _pytest.fixtures.SubRequest
    :return: path to temporary file
    :rtype: str or unicode
    """
    _, tmp_gz_file = tempfile.mkstemp(prefix="tmp",
                                      suffix="." + request.param)
    yield tmp_gz_file
    if os.path.exists(tmp_gz_file):
        os.remove(tmp_gz_file)


@pytest.mark.parametrize("file_format", [fastq.FASTQ_GZ_FORMAT,
                                         fastq.FQ_GZ_FORMAT,
                                         fastq.FASTQ_GZ_FORMAT.upper(),
                                         fastq.FQ_GZ_FORMAT.upper()])
def test_is_fastq_gz(file_format):
    """
    Test :py:func:`riboviz.fastq.is_fastq_gz` with FASTQ GZIP file
    names.

    :param file_format: File name format
    :type file_format: str or unicode
    """
    assert fastq.is_fastq_gz(file_format.format("sample"))


@pytest.mark.parametrize("extension", [".txt", ""])
def test_not_is_fastq_gz(extension):
    """
    Test :py:func:`riboviz.fastq.is_fastq_gz` with non-FASTQ, non-GZIP
    file names.

    :param extension: Extension
    :type extension: str or unicode
    """
    assert not fastq.is_fastq_gz("sample{}".format(extension))


@pytest.mark.parametrize("file_format",
                         [(fastq.FASTQ_GZ_FORMAT,
                           fastq.FASTQ_FORMAT),
                          (fastq.FQ_GZ_FORMAT,
                           fastq.FQ_FORMAT),
                          (fastq.FASTQ_GZ_FORMAT.upper(),
                           fastq.FASTQ_FORMAT.upper()),
                          (fastq.FQ_GZ_FORMAT.upper(),
                           fastq.FQ_FORMAT.upper())])
def test_strip_fastq_gz(file_format):
    """
    Test :py:func:`riboviz.fastq.strip_fastq_gz` with FASTQ GZIP
    file names.

    Each ``file_format`` consists of a FASTQ GZIP file name format and
    the corresponding non-GZIP FASTQ file name format.

    :param file_format: File name format
    :type file_format: tuple(str or unicode, str or unicode)
    """
    gz_ext, ext = file_format
    assert fastq.strip_fastq_gz(gz_ext.format("sample")) == \
        ext.format("sample")


@pytest.mark.parametrize("extension", [".txt", ""])
def test_not_strip_fastq_gz(extension):
    """
    Test :py:func:`riboviz.fastq.strip_fastq_gz` with non-FASTQ,
    non-GZIP file names.

    :param extension: Extension
    :type extension: str or unicode
    """
    file_name = "sample{}".format(extension)
    assert file_name == fastq.strip_fastq_gz(file_name)


def get_test_fastq_sequences(read_length, count):
    """
    Get FASTQ sequences for test FASTQ files.

    A list of sequences is returned that consists of the first
    ``count`` reads of ``read_length`` found by enumerating
    combinations of :py:const:`riboviz.barcodes_umis.NUCLEOTIDES`,
    with quality scores from 0, ..., ``read_length`` - 1.

    :param read_length: Read length
    :type read_length: int
    :param count: Number of sequences
    :type count: int
    :return: List of sequences
    :rtype: list(Bio.SeqRecord.SeqRecord)
    """
    # Create a list of "count" reads AAAA, AAAC etc.
    reads = [''.join(i)
             for i in itertools.product(NUCLEOTIDES,
                                        repeat=read_length)][0:count]
    # Create a list of SeqRecords
    sequences = [SeqRecord(Seq(read),
                           id="read{}".format(i),
                           name="read{}".format(i),
                           description="read{}".format(i))
                 for read, i in zip(reads, range(0, len(reads)))]
    quality = list(range(0, read_length))
    for sequence in sequences:
        sequence.letter_annotations["phred_quality"] = quality
    return sequences


@pytest.mark.parametrize("count", [0, 1, 10])
def test_count_sequences(tmp_file, count):
    """
    Test :py:func:`riboviz.fastq.count_sequences`. with FASTQ files.

    :param tmp_file: path to temporary file
    :type tmp_file: str or unicode
    :param count: Number of sequences
    :type count: int
    """
    sequences = get_test_fastq_sequences(4, count)
    with open(tmp_file, "wt") as f:
        SeqIO.write(sequences, f, "fastq")
    assert fastq.count_sequences(tmp_file) == count


@pytest.mark.parametrize("count", [0, 1, 10])
def test_count_sequences_gz(tmp_gz_file, count):
    """
    Test :py:func:`riboviz.fastq.count_sequences` with GZIPped FASTQ
    files.

    :param tmp_gz_file: path to temporary file
    :type tmp_gz_file: str or unicode
    :param count: Number of sequences
    :type count: int
    """
    sequences = get_test_fastq_sequences(4, count)
    with gzip.open(tmp_gz_file, "wt") as f:
        SeqIO.write(sequences, f, "fastq")
    assert fastq.count_sequences(tmp_gz_file) == count
