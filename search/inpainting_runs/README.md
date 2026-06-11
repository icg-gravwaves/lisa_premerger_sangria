# Inpainting Search Results

Now that we have explained how inpainting can be used as part of a pre-merger search, lets try it out.

Similar to the zero-latency filter search, we have the code `data_runs.py`, but with some vital changes.

## Shared code / preprocessing

A lot of the code is shared between the two `data_runs.py` codes. Should this be in a common module? Probably, but if we changed it, we would want to rerun to test, and dont want to waste comput resources like that.

The code to load the data, subtract the mean, remove signals if needed etc. is all shared between the two codes. The only real differences are as follows:

### PSD generation
The PSDs do not have the zero-latency kernel applied, so we just load them straight from the data.

### Zero-padding
For inpainting, we pad the data with zeros at the end. This affects things like the frequency resolution of the PSD that is needed.

## Loop through bank waveforms
This loop is very similar. The waveform is loaded from the bank and passed to a SNR series function. For inpainting though, we have a loop over the days-before-merger points that we want to consider (`--time-points-days`). For each of these, we compare to the best SNR that has come before and update as appropriate.

Next we compare zero-latency filter and inpainting SNR outputs using the functions defined so that we are confident that they match what we have developed.