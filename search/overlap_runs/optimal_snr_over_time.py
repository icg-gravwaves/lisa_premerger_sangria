"""
This is a script to run the search analysis using a file as input.
"""

# Import necessary libraries
import h5py  # Library for interacting with HDF5 files
import copy  # Library for creating copies of objects
import json  # Library for parsing JSON data
import argparse  # Library for parsing command-line arguments
import logging  # Library for logging messages
from tqdm import tqdm  # Library for creating progress bars
import numpy as np
from matplotlib import pyplot as plt

# Import specific modules from the PyCBC library
import pycbc
import pycbc.types
from pycbc.psd import interpolate
from pycbc.types import MultiDetOptionAction  # Custom action for argparse
from pycbc.psd.lisa_pre_merger import generate_pre_merger_psds  # Function to generate pre-merger PSDs
from pycbc.waveform.pre_merger_waveform import (
    pre_process_data_lisa_pre_merger,  # Function to preprocess data for LISA pre-merger
    generate_waveform_lisa_pre_merger,  # Function to generate waveform for LISA pre-merger
)
import ldc.io.hdf5 as hdfio

from utils import (
    ldc_to_bbhx,
    get_optimal_snr,
    get_full_optimal_snr,
    get_snr_series
)
rtsumsq = lambda x: np.sqrt(sum(xi ** 2 for xi in x))

# Set up argument parser for command-line arguments
parser = argparse.ArgumentParser()

parser.add_argument(
    '--psd-files',
    required=True,
    action=MultiDetOptionAction,
)

# Add argument for the data file (required)
parser.add_argument('--data-file', required=True)

parser.add_argument("--optimal-days-before", type=float, default=25)

# Add argument for the number of days before merger (required)
parser.add_argument('--days-before-merger', type=float, nargs='+', default=[0.5, 1, 4, 7, 14])

# Add argument for the kernel length with a default value
parser.add_argument('--kernel-length', type=int, default=17280)

# Add argument for the data length with a default value (seconds)
parser.add_argument('--data-length', type=int, default=2592000)

# Add argument for the lower frequency cutoff with a default value
parser.add_argument('--f-lower', type=float, default=1e-6)

# Add argument for the sample rate with a default value
parser.add_argument('--sample-rate', type=float, default=0.2)

parser.add_argument('--output-file')

parser.add_argument('--output-plot')

parser.add_argument('--log-xscale', action='store_true')

parser.add_argument('--n-optimal', type=int, default=1200)

# Add argument for reducing the bank factor
parser.add_argument('--reduce-bank-factor', type=int,
                    default=1,
                    help="Reduce the bank by a factor of this number, "
                         "useful for performing the search quickly in testing"
                         "Default: don't do this")

# Parse the command-line arguments provided by the user
args = parser.parse_args()

window_length = 17280

mbhbs, _ = hdfio.load_array(args.data_file, name="sky/mbhb/cat")

waveform_params_shared = {
    't_obs_start': args.data_length, # This is setting the data length.
    'f_lower': args.f_lower,
    'low-frequency-cutoff': 1e-6, 
    'f_final': args.sample_rate / 2,
    'delta_f': 1 / args.data_length,
    'tdi': '1.5',
    't_offset': 0,
    'approximant': 'BBHX_PhenomD',
    'mode_array': [(2,2)],
    'tc': args.data_length,
}


psds_for_whitening = {
    f'LISA_{channel}': interpolate(
        generate_pre_merger_psds(
            psd_file=args.psd_files[channel],
            duration=args.data_length,
            sample_rate=args.sample_rate,
            kernel_length=args.kernel_length
        )['FD'],
        1 / args.data_length
    )
    for channel in ['A','E']
}

flen = int(args.data_length * args.sample_rate) // 2 + 1
delta_f = 1 / args.data_length

psds_standard = {
    f'LISA_{channel}': pycbc.psd.from_txt(
        args.psd_files[channel],
        flen,
        delta_f,
        delta_f,
        is_asd_file=False
    )
    for channel in ['A','E']
}

if args.log_xscale:
    cutoff_days = np.logspace(
        np.log10(1 / 24),
        np.log10(args.optimal_days_before),
        args.n_optimal
    )[::-1]
else:
    cutoff_days = np.linspace(
        1 / 24,
        args.optimal_days_before,
        args.n_optimal
    )[::-1]

# Add the zero time
cutoff_days = np.concatenate((cutoff_days, [0]))

with h5py.File(args.output_file,'w') as ofile:
    ofile.create_dataset(
        'cutoff_days',
        data=-cutoff_days[::-1],
    )

for signal_number in np.arange(15):
    logging.info("Signal number %d", signal_number)
    optimal_snr_over_time = np.zeros_like(cutoff_days)
    signal_waveform = ldc_to_bbhx(
        mbhbs[signal_number],
        waveform_params_shared
    )
    logging.info("Calculating optimal SNR over time")
    for i, cutoff_day in enumerate(tqdm(cutoff_days)):
        cutoff_s = cutoff_day * 86400
        optimal_snr = get_optimal_snr(
            signal_waveform,
            psds_for_whitening,
            cutoff_s,
            window_length=window_length,
            delta_t=1. / args.sample_rate,
            kernel_length=args.kernel_length,
        )

        optimal_snr_over_time[i] = rtsumsq(optimal_snr)

    logging.info(
        "Updating zero cutoff time to be the full signal"
    )

    optimal_snr_over_time[-1] = rtsumsq(get_full_optimal_snr(
        signal_waveform,
        psds_standard
    ))


    with h5py.File(args.output_file,'a') as ofile:
        ofile.create_dataset(
            f'optimal_snr_signal_{signal_number}',
            data=optimal_snr_over_time[::-1],
        )