# Estimating PSDs

Here we estimate the PSDs for use in performing the search.

We estimate PSDs for each channel from the Sangria-HM dataset, using the welch method of PSD estimation.

The model PSD shown and used throughout the paper is from the LDC get_noise_model function, which is what was used to generate the Sangria-HM dataset.

The 'dip' at 0.06Hz is removed from both the model and the estimated PSD by bridging the gap between the peaks either side with a smooth transition between the data and the bridge.

Plots of the PSDs and the dip removal method are given in the notebook.