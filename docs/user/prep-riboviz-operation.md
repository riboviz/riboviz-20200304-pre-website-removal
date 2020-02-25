# What the RiboViz workflow does

This page describes what `riboviz.tools.prep_riboviz` does. 

Configuration parameters are shown in brackets and are described in [Configuring the RiboViz workflow](./prep-riboviz-config.md).

---

## Coordinating local scripts and third-party components

`prep_riboviz` prepares ribosome profiling data for by implementing a workflow that uses a combination of local Python and R scripts and third-party components. These are as follows:

* `hisat2-build`: build rRNA and ORF indices.
* `cutadapt`: cut adapters.
* `hisat2`: align reads.
* `riboviz.tools.trim_5p_mismatch`: trim 5' mismatches from reads and remove reads with more than a set number of mismatches (local script, in `riboviz/tools/`).
* `umi_tools` (`extract`, `dedup`, `group`): extract barcodes and UMIs, deduplicate reads and group reads.
* `riboviz.tools.demultiplex_fastq`: demultiplex multiplexed files (local script, in `riboviz/tools/`).
* `samtools` (`view`, `sort`, `index`): convert SAM files to BAM files and index.
* `bedtools` (`genomecov`): export transcriptome coverage as bedgraphs.
* `bam_to_h5.R`: convert BAM to compressed H5 format (local script, in `rscripts/`)
* `generate_stats_figs.R`: generate summary statistics, analyses plots and QC plots (local script, in `rscripts/`)
* `collate_tpms.R`: collate TPMs across samples (local script, in `rscripts/`)
* `riboviz.tools.count_reads`: count the number of reads (sequences) processed by specific stages of the workflow (local script, in `riboviz/tools/`).

---

## Process ribosome profiling sample data

If sample files (`fq_files`) are specified, then `prep_riboviz` processes the sample files as follows:

1. Read configuration information from YAML configuration file.
2. Build hisat2 indices if requested (if `build_indices: TRUE`) using `hisat2 build` and save these into the index directory (`dir_index`).
3. Process each sample ID-sample file pair (`fq_files`) in turn:
   1. Cut out sequencing library adapters (`adapters`) using `cutadapt`.
   2. Extract UMIs using `umi_tools extract`, if requested (if `extract_umis: TRUE`), using a UMI-tools-compliant regular expression pattern (`umi_regexp`). The extracted UMIs are inserted into the read headers of the FASTQ records.
   3. Remove rRNA or other contaminating reads by alignment to rRNA index files (`rrna_index_prefix`) using `hisat2`.
   4. Align remaining reads to ORFs index files (`orf_index_prefix`). using `hisat2`.
   5. Trim 5' mismatches from reads and remove reads with more than 2 mismatches using `trim_5p_mismatch`.
   6. Output UMI groups pre-deduplication using `umi_tools group` if requested (if `dedup_umis: TRUE` and `group_umis: TRUE`)
   7. Deduplicate reads using `umi_tools dedup`, if requested (if `dedup_umis: TRUE`)
   8. Output UMI groups post-deduplication using `umi_tools group` if requested (if `dedup_umis: TRUE` and `group_umis: TRUE`)
   9. Export bedgraph files for plus and minus strands, if requested (if `make_bedgraph: TRUE`) using `bedtools genomecov`.
   10. Write intermediate files produced above into a sample-specific directory, named using the sample ID, within the temporary directory (`dir_tmp`).
   11. Make length-sensitive alignments in compressed h5 format using `bam_to_h5.R`.
   12. Generate summary statistics, and analyses and QC plots for both RPF and mRNA datasets using `generate_stats_figs.R`. This includes estimated read counts, reads per base, and transcripts per million for each ORF in each sample.
   13. Write output files produced above into an sample-specific directory, named using the sample ID, within the output directory (`dir_out`). 
4. Collate TPMs across results, using `collate_tpms.R` and write into output directory (`dir_out`). Only the results from successfully-processed samples are collated.
5. Count the number of reads (sequences) processed by specific stages if requested (if `count_reads: TRUE`).

[Workflow](../images/workflow.svg) (SVG) shows an images of the workflow with the key steps, inputs and outputs.

[Workflow with deduplication](../images/workflow-dedup.svg) (SVG) shows the workflow, if `dedup_umis: TRUE`.

---

## Process multiplexed ribosome profiling sample data

If a multiplexed file (`multiplex_fq_files`) is specified, then `prep_riboviz`, the `prep_riboviz` processes the multiplexed file as follows:

1. Read configuration information (as for 1. above).
2. Build hisat2 indices if requested (as for 2. above).
3. Read the multiplexed FASTQ file (`multiplex_fq_files`).
4. Cut out sequencing library adapters (`adapters`) using `cutadapt`.
5. Extract barcodes and UMIs using `umi_tools extract`, if requested (if `extract_umis: TRUE`), using a UMI-tools-compliant regular expression pattern (`umi_regexp`).
6. Demultiplex file with reference to the sample sheet (`sample_sheet`), using `demultiplex_fastq`. Sample IDs in the `SampleID` column in the sample sheet are used to name the demultiplexed files.
7. Process each demultiplexed FASTQ file which has one or more reads, in turn (as for 3.3 to 3.13 above)
8. Collate TPMs across results, using `collate_tpms.R` and write into output directory (`dir_out`) (as for 4. above.
9. Count the number of reads (sequences) processed by specific stages if requested (if `count_reads: TRUE`).

[Workflow with demultiplexing](../images/workflow-deplex.svg) (SVG) shows an images of the workflow with the key steps, inputs and outputs.

---

## Index files

Index files (HT2) are produced in the index directory (`dir_index`).

---

## Temporary files

Intermediate files are produced within the temporary directory (`dir_tmp`).

For each sample (`<SAMPLE_ID>`), intermediate files are produced in a sample-specific subdirectory (`<SAMPLE_ID>`):

* `trim.fq`: adapter trimmed reads. This is not present if a multiplexed file (`multiplex_fq_files`) is specified.
* `nonrRNA.fq`: non-rRNA reads.
* `rRNA_map.sam`: rRNA-mapped reads.
* `orf_map.sam`: ORF-mapped reads.
* `orf_map_clean.sam`: ORF-mapped reads with mismatched nt trimmed.
* `trim_5p_mismatch.tsv`: number of reads processed, discarded, trimmed and written when trimming 5' mismatches from reads and removing reads with more than a set number of mismatches.
* `unaligned.sam`: unaligned reads. These files can be used to find common contaminants or translated sequences not in your ORF annotation.


If deduplication is enabled (if `dedup_umis: TRUE`) the following sample-specific files are also produced:

* `extract_trim.fq`: adapter trimmed reads with UMIs extracted. This is not present if a multiplexed file (`multiplex_fq_files`) is specified.
* `pre_dedup.bam`: BAM file prior to deduplication.
* `pre_dedup.bam.bai`: BAM index file for `pre_dedup.bam`.
* UMI groups pre- and post-deduplication (if `group_umis: TRUE`):
  - `pre_dedup_groups.tsv`: UMI groups before deduplication.
  - `post_dedup_groups.tsv`: UMI groups after deduplication.
* UMI deduplication statistics:
  - `dedup_stats_edit_distance.tsv`: edit distance between UMIs at each position.
  - `dedup_stats_per_umi_per_position.tsv`: histogram of counts per position per UMI pre- and post-deduplication.
  - `dedup_stats_per_umi.tsv`: number of times each UMI was observed, total counts and median counts, pre- and post-deduplication
  - For more information on the `stats` files, see see UMI-tools [Dedup-specific options](https://umi-tools.readthedocs.io/en/latest/reference/dedup.html) and [documentation on stats file #250](https://github.com/CGATOxford/UMI-tools/issues/250)

If a multiplexed file (`multiplex_fq_files`) is specified, then the following files and directories are also written into the temporary directory:

* `<FASTQ_FILE_NAME_PREFIX>_trim.fq`: FASTQ file post-adapter trimming, where `<FASTQ_FILE_NAME_PREFIX>` is the name of the file (without path or extension) in `multiplex_fq_files`.
* `<FASTQ_FILE_NAME_PREFIX>_extract_trim.fq`: `<FASTQ_FILE_NAME_PREFIX_trim.fq` post-barcode and UMI extraction.
* `<FASTQ_FILE_NAME_PREFIX>_deplex/`: demultiplexing results directory including:
   - `num_reads.tsv`: a tab-separated values file with columns:
     - `SampleID`, copied from the sample sheet.
     - `TagRead` (barcode), coped from the sample sheet.
     - `NumReads`, number of reads detected for each sample.
     - Row with `SampleID` with value `Unassigned` and `NumReads` value with the number of unassigned reads.
     - Row with `SampleID` with value `Total` and `NumReads` value with the total number of reads processed. 
  - `<SAMPLE_ID>.fastq`: Files with demultiplexed reads, where `<SAMPLE_ID>` is a value in the `SampleID` column of the sample sheet. There will be one file per sample.
  - `Unassigned.fastq`: A FASTQ file with the reads that did not match any `TagRead` (barcode) in the sample sheet.

---

## Output files

Output files are produced within the output directory (`dir_out`).

For each sample (`<SAMPLE_ID>`), intermediate files are produced in a sample-specific subdirectory (`<SAMPLE_ID>`):

* `<SAMPLE_ID>.bam`: BAM file of reads mapped to transcripts, which can be directly used in genome browsers.
* `<SAMPLE_ID>.bam.bai`: BAM index file for `<SAMPLE_ID>.bam`.
* `minus.bedgraph`: bedgraph of reads from minus strand (if `make_bedgraph: TRUE`).
* `plus.bedgraph`: bedgraph of reads from plus strand (if `make_bedgraph: TRUE`).
* `<SAMPLE_ID>.h5`: length-sensitive alignments in compressed h5 format.
* `3nt_periodicity.tsv`
* `3nt_periodicity.pdf`
* `read_lengths.tsv`
* `read_lengths.pdf`
* `pos_sp_nt_freq.tsv`
* `pos_sp_rpf_norm_reads.pdf`
* `pos_sp_rpf_norm_reads.tsv`
* `features.pdf`
* `tpms.tsv`
* `codon_ribodens.tsv`
* `codon_ribodens.pdf`
* `startcodon_ribogridbar.pdf`
* `startcodon_ribogrid.pdf`
* `3ntframe_bygene.tsv`
* `3ntframe_propbygene.pdf`

In addition, the following files are also put into the output directory:

* `TPMs_collated.tsv`: file with the transcripts per million (tpm) for all successfully processed samples.
* `read_counts.tsv`: a [read counts file](#read-counts-file) (only if `count_reads: TRUE`).

---

## Log files

Information on the execution of `prep_riboviz`, including the causes of any errors, is added to a timestamped log file in the current directory, named `riboviz-YYYYMMDD-HHMMSS.log` (for example, `riboviz.20190926-002455.log`).

Log files for each processing step are placed in a timestamped subdirectory (`YYYYMMDD-HHMMSS`) within the logs directory (`dir_logs`). 

For each sample (`<SAMPLE_ID>`), log files are produced in a sample-specific directory (`<SAMPLE_ID>`) within this timestamped subdirectory.

The following log files are produced:

```
hisat2_build_r_rna.log
hisat2_build_orf.log
<SAMPLE_ID>/
  01_cutadapt.log
  02_hisat2_rrna.log
  03_hisat2_orf.log
  04_trim_5p_mismatch.log
  05_samtools_view_sort.log
  06_samtools_index.log
  07_bedtools_genome_cov_plus.log
  08_bedtools_genome_cov_minus.log
  09_bam_to_h5.log
  10_generate_stats_figs.log
collate_tpms.log
count_reads.log
```

If deduplication is enabled (if `dedup_umis: TRUE`), then the following log files are produced:

```
hisat2_build_r_rna.log
hisat2_build_orf.log
<SAMPLE_ID>/
  01_cutadapt.log
  02_umi_tools_extract.log
  03_hisat2_rrna.log
  04_hisat2_orf.log
  05_trim_5p_mismatch.log
  06_samtools_view_sort.log
  07_samtools_index.log
  08_umi_tools_group.log
  09_umi_tools_dedup.log
  10_samtools_index.log
  11_umi_tools_group.log
  12_bedtools_genome_cov_plus.log
  13_bedtools_genome_cov_minus.log
  14_bam_to_h5.log
  15_generate_stats_figs.log
collate_tpms.log
count_reads.log
```

If a multiplexed file (`multiplex_fq_files`) specified, then the following log files are produced:

```
hisat2_build_r_rna.log
hisat2_build_orf.log
cutadapt.log
umi_tools_extract.log
demultiplex_fastq.log
<SAMPLE_ID>/
  01_hisat2_rrna.log
  02_hisat2_orf.log
  03_trim_5p_mismatch.log
  04_samtools_view_sort.log
  05_samtools_index.log
  06_umi_tools_group.log
  07_umi_tools_dedup.log
  08_samtools_index.log
  09_umi_tools_group.log
  10_bedtools_genome_cov_plus.log
  11_bedtools_genome_cov_minus.log
  12_bam_to_h5.log
  13_generate_stats_figs.log
collate_tpms.log
count_reads.log
```

---

## Read counts file

`prep_riboviz` will summarise information about the number of reads in the input files and in the output files produced at each step of the workflow. This summary is produced by scanning input, temporary and output directories and counting the number of reads (sequences) processed by specific stages of a RiboViz workflow.

The read counts file, `read_counts.tsv`, is written into the output directory.

The reads counts file is a tab-separated values (TSV) file with the following columns:

* `SampleName`: Name of the sample to which this file belongs. This is
  an empty value if the step was not sample-specific
  (e.g. demultiplexing a multiplexed FASTQ file).
* `Program`: Program that wrote the file. The special token
  `input` denotes input files.
* `File`: Path to file.
* `NumReads`: Number of reads in the file.
* `Description`: Human-readable description of the file contents.

The following information is included:

* Input files: number of reads in the FASTQ files used as inputs.
* `cutadapt`: number of reads in the FASTQ file output.
* `riboviz.tools.demultiplex_fastq`: FASTQ files output by
  "demultiplex_fastq", using the information in the associated
  `num_reads.tsv` summary files, or, if these can't be found, the
  FASTQ files themselves.
* `hisat2`: number of reads in the SAM file and FASTQ file output.
* `riboviz.tools.trim_5p_mismatch`: number of reads in the SAM file
  output as recorded in the `trim_5p_mismatch.tsv` summary file
  output, or the SAM file itself, if the TSV file cannot be found.
* `umi_tools dedup`: number of reads in the BAM file output.

Here is an example of a read counts file produced when running the vignette:

```
SampleName	Program	File	NumReads	Description
WTnone	input	vignette/input/SRR1042855_s1mi.fastq.gz	963571	input
WT3AT	input	vignette/input/SRR1042864_s1mi.fastq.gz	1374448	input
WT3AT	cutadapt	vignette/tmp/WT3AT/trim.fq	1373362	Reads after removal of sequencing library adapters
WT3AT	hisat2	vignette/tmp/WT3AT/nonrRNA.fq	485226	rRNA or other contaminating reads removed by alignment to rRNA index files
WT3AT	hisat2	vignette/tmp/WT3AT/rRNA_map.sam	2254078	Reads with rRNA and other contaminating reads removed by alignment to rRNA index files
WT3AT	hisat2	vignette/tmp/WT3AT/unaligned.fq	476785	Unaligned reads removed by alignment of remaining reads to ORFs index files
WT3AT	hisat2	vignette/tmp/WT3AT/orf_map.sam	8698	Reads aligned to ORFs index files
WT3AT	riboviz.tools.trim_5p_mismatch	vignette/tmp/WT3AT/orf_map_clean.sam	8698	Reads after trimming of 5' mismatches and removal of those with more than 2 mismatches
WTnone	cutadapt	vignette/tmp/WTnone/trim.fq	952343	Reads after removal of sequencing library adapters
WTnone	hisat2	vignette/tmp/WTnone/nonrRNA.fq	466464	rRNA or other contaminating reads removed by alignment to rRNA index files
WTnone	hisat2	vignette/tmp/WTnone/rRNA_map.sam	1430213	Reads with rRNA and other contaminating reads removed by alignment to rRNA index files
WTnone	hisat2	vignette/tmp/WTnone/unaligned.fq	452266	Unaligned reads removed by alignment of remaining reads to ORFs index files
WTnone	hisat2	vignette/tmp/WTnone/orf_map.sam	14516	Reads aligned to ORFs index files
WTnone	riboviz.tools.trim_5p_mismatch	vignette/tmp/WTnone/orf_map_clean.sam	14516	Reads after trimming of 5' mismatches and removal of those with more than 2 mismatches
``
