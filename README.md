# Inpainting over the cracks: challenges of applying pre-merger searches for massive black hole binaries to realistic LISA datasets

This is the data release for the paper [*Inpainting over the cracks: challenges of applying pre-merger searches for massive black hole binaries to realistic LISA datasets*](https://arxiv.org/abs/2605.13738).
We release the data behind each figure and the code and configuration used to produce each of them. We also release steps needed and codes to reproduce the search using our code.

# Reproducing our analysis
In the data release, we discuss different parts of the analysis and how they were performed

We provide an outline of the commands used to submit jobs. Exact commands will depend on your computing setup, but the ones we used are included so that they can be adapted as needed.

## Reproducing the analysis environment
As always with python, software dependencies will change in the coming years, and this code may be incompatible with future releases of any dependency.

This paper was generated using a fork of PyCBC at https://github.com/icg-gravwaves/pycbc/tree/lisa-pre-merger. This was forked from PyCBC at cd0e16a.

We also provide an environment file here so that if the user wants to use our work as a basis for development, that is possible. The conda environment is defined yaml files for [linux](install_reqs_linux.yml) and or [mac](install_reqs_mac.yml), which can be used for the analysis, dependoing on your OS:

For linux use 
`conda env create -f install_reqs_linux.yml`
or for mac
`conda env create -f install_reqs_mac.yml`

Make sure you have activated the environment using `conda activate env_lisa_premerger_sangria`

This is the repo used to control analysis and data release for the paper [Inpainting over the cracks: challenges of applying pre-merger searches for massive black hole binaries to realistic LISA datasets](https://arxiv.org/abs/2605.13738)

## Data Release

## Datasets

## PSD Estimation
[The first section](./estimate_psds/README.md), shows our investigation into the noise properties of the Sangria-HM dataset and its applicability to pre-merger massive black hole binary searches.

This corresponds to Section II of the paper, and shows generation of Figures 1 & 2, and Table 1 of the paper.

## Inpainting
This section shows some investigations we performed which were not included in the paper, but help to illustrate Section IV of the paper.

## Applying the premerger searches
The next sections show how our searches were applied to the Sangria-HM dataset.

### Zero-latency search
This section corresponds to Section III of the paper, and shows generation of Figures 3-6.

### Inpainting
Here we show the analyses used in Section V, and generation of Figures 7-10, and Tables 3 & 4.

