# RiboViz

**Ribosome profiling** provides a detailed global snapshot of protein synthesis in a cell.  At its core, this technique makes use of the observation that a translating ribosome protects around 30 nucleotides of the mRNA from nuclease activity.  High-throughput sequencing of these ribosome protected fragments (called ribosome footprints) offers a precise record of the number and location of the ribosomes at the time at which translation is stopped. Mapping the position of the ribosome protected fragments indicates the translated regions within the transcriptome.  Moreover, ribosomes spend different periods of time at different positions, leading to variation in the footprint density along the mRNA transcript. This provides an estimate of how much protein is being produced from each mRNA. Importantly, ribosome profiling is as precise and detailed as RNA sequencing. Even in a short time, since its introduction in 2009, ribosome profiling has been playing a key role in driving biological discovery.

We have developed a bioinformatics tool-kit, **riboviz**, for analyzing ribosome profiling datasets. **RiboViz** consists of a comprehensive and flexible backend analysis pipeline. The current iteration of **RiboViz* is designed for yeast datasets.

Existing yeast datasets consist of a mix of studies, some of which use elongation inhibitors such as cycloheximide (CHX) and others that flash freeze (FF) the samples to prevent initiation and elongation during sample preparation. In general, each experimental step can potentially introduce biases in processed datasets. **RiboViz** can help identify these biases by allowing users to compare and contrast datasets obtained under different experimental conditions.

All the codes for processing the raw reads is available in this repository.

For information on **RiboViz**, see "riboviz: analysis and visualization of ribosome profiling datasets", Carja et al., BMC Bioinformatics 2017. doi:10.1186/s12859-017-1873-8.

## Getting started

* [Introduction](./docs/introduction.md)
* [Install prerequisites](./docs/install.md)
* [Quick install scripts](./docs/quick-install.md) (Ubuntu and CentOS only)
* [Map mRNA and ribosome protected reads to transcriptome and collect data intoan HDF5 file](./docs/run-vignette.md). This page describes how you can run a "vignette" of the back-end analysis pipeline, to demostrate RiboViz's capabilities.
* [Content and provenance of repository data files](./docs/data.md)
* [Prepare data](./docs/prepare-data.md)
* [Structure of HDF5 data](./docs/hdf5-data.md)
* [Developer guide](./docs/developer-guide.md)

## Releases

| Release | Description |
| ------- | ----------- |
| [1.1.0](https://github.com/riboviz/RiboViz/releases/tag/1.1.0) | Most recent version prior to commencement of BBSRC/NSF Riboviz project |
| [1.0.0](https://github.com/riboviz/RiboViz/releases/tag/1.0.0) | Associated with Carja et al. (2017) "riboviz: analysis and visualization of ribosome profiling datasets", BMC Bioinformatics, volume 18, article 461 (2017), 25 October 2017, doi: [10.1186/s12859-017-1873-8](https://doi.org/10.1186/s12859-017-1873-8) |
| [0.9.0](https://github.com/riboviz/RiboViz/releases/tag/0.9.0) | Additional code/data associated with the paper below |
| [0.8.0](https://github.com/riboviz/RiboViz/releases/tag/0.8.0) | Associated with Carja et al. (2017) "riboviz: analysis and visualization of ribosome profiling datasets", bioRXiv, 12 January 2017,doi: [10.1101/100032](https://doi.org/10.1101/100032) |
