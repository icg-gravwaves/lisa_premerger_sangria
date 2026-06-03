# Inpainting over the cracks: challenges of applying pre-merger searches for massive black hole binaries to realistic LISA datasets

This is the repo used to control analysis and data release for the paper [Inpainting over the cracks: challenges of applying pre-merger searches for massive black hole binaries to realistic LISA datasets](https://arxiv.org/abs/2605.13738)

## Data Release

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

## Datasets
Here we discuss the various datasets used in the paper, with download instructions given in the repository

## PSD Estimation
[The first section](./estimate_psds/README.md), shows our investigation into the noise properties of the Sangria-HM dataset, the estimated SNRs of the signals, and the applicability of our methodology to pre-merger massive black hole binary searches.

This corresponds to Section II of the paper, and shows generation of Figures 1 & 2, and Table 1 of the paper.

## Applying the zero-latency premerger search
The next sections show how the zero-latency search from [our previous work](https://arxiv.org/abs/2411.07020) was applied to the Sangria-HM dataset, and the issues faced with that.

This corresponds to Section III of the paper, and shows generation of Figures 3-6.

## Inpainting
After this, [we show](./inpainting/README.md) some investigations we performed which were not included in the paper, but help to illustrate Section IV of the paper.

## Applying the inpainting search
[Here](./search/inpainting_runs/README.md) we show the analysis used in Section V, applying inpainting as a premerger search to the Sangria-HM dataset.

This section has the generation of Figures 7, and Table 3.

## Overlapping Signals

[This section](./search/inpainting_runs/focused.md) discusses Section VI, and shows the analysis during a period of Sangria-HM data particularly densely-packed with signals.

We show generation of Figures 8-10, and Table 4.