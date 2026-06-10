# Zero Latency Searches

Now that we have the PSDs and we are confident that we can do the pre-merger search even with the galactic binary foreground, we look at the search itself.

We want to implement the zero-latency filter search used in [our previous paper](https://arxiv.org/abs/2411.07020), so we look at the modifications we need to make:

The [template bank](../template_bank/README.md) will need updating - the PSD is similar, but different enough that we do need to consider the bank.

Sangria-HM contains the full two years of data for LISA. We [explain](./zero_latency_search.md) how the search is performed (with examples), by slicing it so that we effectively see an end to the data, and step that slice through hour-by-hour.

Applying this directly, we then saw an issue: the signal merger has such high SNR that the pre-merger templates were producing false alarms even though the overlap was not significant. We [explain the issue](../overlap_runs/README.md), then [plot overlaps](../overlap_runs/plot_optimal_snr_fitting_factor.ipynb) and show [the methods used to remove signals from the data](./signal_removal.ipynb).

We then aoply this to the zero-latency filter search and [plot its results](./plot_data_results.ipynb).