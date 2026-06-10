# Zero Latency Searches

Now that we have the PSDs and we are confident that we can do the pre-merger search even with the galactic binary foreground, we look at the search itself.

We want to implement the zero-latency filter search used in [our previous paper](https://arxiv.org/abs/2411.07020), so we look at the modifications we need to make:

The template bank will need updating - the PSD is similar, but different enough that we do need to consider the bank.

The Sangria-HM data is the full two years of flight for LISA. We need to slice the data so that we effectively see an end to the data, and walk that slice through the data hour-by-hour

We then saw an issue: the overlap between the 