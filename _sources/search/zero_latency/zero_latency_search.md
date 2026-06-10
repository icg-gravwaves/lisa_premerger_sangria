# Zero Latency Searches

We have the PSDs and the banks - lets go!

Most of the following is in `data_runs.py`, but as we later move to a different search, many of the shared utilities have been added to [common_utils.py](../common_utils.py). As a result, it can be a little hard to follow what is happening in just the main code, but lets go through it step-by-step.



The Sangria-HM data is the full two years of flight for LISA. We need to slice the data so that we effectively see an end to the data, and walk that slice through the data hour-by-hour

We then saw an issue: the overlap between the 