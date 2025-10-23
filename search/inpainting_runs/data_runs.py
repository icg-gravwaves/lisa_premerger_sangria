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

# Import specific modules from the PyCBC library
import pycbc
import pycbc.types
from pycbc.psd import interpolate
from pycbc.types import MultiDetOptionAction  # Custom action for argparse

import ldc.io.hdf5 as hdfio

from utils import (
    generate_pre_merger_psds,
    pre_process_data_lisa_pre_merger,  # Function to preprocess data for LISA pre-merger
    generate_waveform_lisa_pre_merger,  # Function to generate waveform for LISA pre-merger
    get_snr_from_series,  # Function to get SNR from a series
    plot_best_waveform,  # Function to plot the best waveform
    load_ldc_timeseries, # function to load timeseries
    generate_waveform_for_data,
)

# Set up argument parser for command-line arguments
parser = argparse.ArgumentParser()

# Add argument for the PSD files (required) with custom action for multiple detectors
parser.add_argument(
    '--psd-files',
    required=True,
    action=MultiDetOptionAction,
)

# Add argument for the bank file (required)
parser.add_argument('--bank-file', required=True)

# Add argument for the data file (required)
parser.add_argument('--data-file', required=True)

# # Add argument for the end time (required)
parser.add_argument('--end-time', required=True, type=float,
                    help="This is the end time being considered in the file.")

# Search time - the amount of time that will be considered
# valid of the SNR time series 
parser.add_argument('--search-time', type=float, default=86400.)

# Add argument for the number of days before merger (required)
parser.add_argument('--days-before-merger', type=float, required=True)

# Add argument for the kernel length with a default value
parser.add_argument('--kernel-length', type=int, default=17280)

# Add argument for the data length with a default value (seconds)
parser.add_argument('--data-length', type=int, default=2592000)

parser.add_argument(
    '--remove-signals-after-coalescence',
    type=float,
    help="Remove signals from the data this amount of time (s) after "
         "the coalescence. e.g. if we consider that a signal would "
         "be considered found accurately half an hour after the coalescence, "
         "set this to 1800. Default - don't do this"
)

parser.add_argument(
    '--remove-all-mbhbs',
    action='store_true',
    help="If given, remove all mbhbs from the dataset. Thsi flag means that "
    "--remove-signals-after-coalescence has no effect"
)

parser.add_argument(
    '--remove-all-gbs',
    action='store_true',
    help="If given, remove all galactic binaries from the dataset"
)

# Add argument for the lower frequency cutoff with a default value
parser.add_argument('--f-lower', type=float, default=1e-6)

# Add argument for the sample rate with a default value
parser.add_argument('--sample-rate', type=float, default=0.2)

# Add argument for plotting the best waveform
parser.add_argument("--plot-best-waveform", action='store_true')

# Add argument for reducing the bank factor
parser.add_argument('--reduce-bank-factor', type=int,
                    help="Reduce the bank by a factor of this number, "
                         "useful for performing the search quickly in testing"
                         "Default: don't do this")

parser.add_argument(
    '--inpaint',
    action='store_true',
    help='Use inpainting rather than FIR filter for analysis'
)

# Parse the command-line arguments provided by the user
args = parser.parse_args()

#############################
# Generate the necessary PSDs
#############################

# Initialize logging for the PyCBC library
pycbc.init_logging(True)
logging.info(f"{args.days_before_merger} days before merger")

# Set the defaults required for the waveform parameters
waveform_params_shared = {
    't_obs_start': args.data_length, # This is setting the data length.
    'f_lower': args.f_lower,
    'low-frequency-cutoff': 1e-6, 
    'f_final': args.sample_rate / 2,
    'delta_f': 1 / args.data_length,
    'tdi': '1.5',
    't_offset': 0,
    'cutoff_deltat': 0,
}


time_before = 86400 * args.days_before_merger

cutoff_time=time_before
window_length=17280


remove_noiseless_groups = []
if args.remove_all_mbhbs:
    remove_noiseless_groups.append('sky/mbhb/tdi')
if args.remove_all_gbs:
    remove_noiseless_groups += [f"sky/{i}gb/tdi" for i in ['v','d','i']]

data = load_ldc_timeseries(
    args.data_file,
    remove_noiseless_groups=remove_noiseless_groups,
    delta_t=1./args.sample_rate
)

mbhb_data = load_ldc_timeseries(
    args.data_file,
    data_group='sky/mbhb/tdi',
    delta_t=1./args.sample_rate,
)

end_idx = int(args.end_time * args.sample_rate) # seconds * hertz = unitless
start_idx = int(end_idx - args.data_length * args.sample_rate) # unitless - unitless
start_time = args.end_time - args.data_length # seconds - number of samples / (number of samples per second) = seconds

logging.info("Cutting to %.3f seconds of data", args.data_length)

for channel in data.keys():
    data[channel] = data[channel][start_idx:end_idx]
    mbhb_data[channel] = mbhb_data[channel][start_idx:end_idx]
    
if args.remove_signals_after_coalescence is not None and not args.remove_all_mbhbs:
    from matplotlib import pyplot as plt
    mbhbs, _ = hdfio.load_array(args.data_file, name="sky/mbhb/cat")
    for i, mbhb in enumerate(mbhbs):

        if args.end_time < (mbhb['CoalescenceTime'] + args.remove_signals_after_coalescence):
            logging.info("Signal %d not yet reached", i)
            continue

        if mbhb['CoalescenceTime'] < (args.end_time - args.data_length * args.sample_rate * 2):
            logging.info("Signal %d is well before the searched time - ignore it", i)
            continue
    
        logging.info("Removing signal %d from data", i)

        waveform_for_removal = generate_waveform_for_data(
            mbhb,
            start_time,
            args.end_time,
            1. / args.sample_rate,
        )

        plt.plot(
            data['LISA_A'].sample_times - mbhb['CoalescenceTime'],
            data['LISA_A'],
            label='Data LISA A',
            alpha=0.25
        )
        plt.plot(
            data['LISA_E'].sample_times - mbhb['CoalescenceTime'],
            data['LISA_E'],
            label='Data LISA E',
            alpha=0.25
        )
        plt.plot(
            mbhb_data['LISA_A'].sample_times - mbhb['CoalescenceTime'],
            mbhb_data['LISA_A'],
            c='tab:blue',
            label='MBHB LISA_A',
        )
        plt.plot(
            mbhb_data['LISA_E'].sample_times - mbhb['CoalescenceTime'],
            mbhb_data['LISA_E'],
            c='tab:orange',
            label='MBHB LISA_E',
        )
        plt.plot(
            waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
            waveform_for_removal['LISA_A'],
            c='tab:green',
            linestyle=':',
            label='Waveform LISA A'
        )
        plt.plot(
            waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
            waveform_for_removal['LISA_E'],
            c='tab:red',
            linestyle=':',
            label='Waveform LISA E'
        )

        plt.axvline(0, c='r', linestyle=':')
        plt.xlim(-2000, 1000)
        plt.ylim(-1e-19, 1e-19)
        plt.legend(loc='upper left')
        plt.savefig("waveform_for_removal.png")

        logging.info('Removing from data')
        subtracted = {
            channel: data[channel] - waveform_for_removal[channel]
            for channel in data.keys()
        }

        plt.figure()
        plt.plot(
            waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
            data['LISA_A'],
            alpha=0.5,
            c='tab:blue',
            label='Original LISA A'
            )
        plt.plot(
            waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
            data['LISA_E'],
            alpha=0.5,
            c='tab:orange',
            label='Original LISA E'
        )
        plt.plot(
            waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
            subtracted['LISA_A'],
            c='tab:blue',
            label='Subtracted LISA A'
            )
        plt.plot(
            waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
            subtracted['LISA_E'],
            c='tab:orange',
            label='Subtracted LISA E'
        )
        plt.axvline(0, c='r', linestyle=':')
        plt.xlim(-2000, 1000)
        plt.ylim(-1e-19, 1e-19)
        plt.legend(loc='upper left')
        plt.savefig("waveform_removed.png")

        data = subtracted

psds_for_whitening = {
    f'LISA_{channel}':  interpolate(
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

logging.info("Generated PSD objects")

lisa_a_zero_phase_kern_pycbc_fd = psds_for_whitening['LISA_A']
lisa_e_zero_phase_kern_pycbc_fd = psds_for_whitening['LISA_E']

#  For inpainting, this will be overwhitened with the 
data = pre_process_data_lisa_pre_merger(
    data,
    sample_rate=args.sample_rate,
    psds_for_whitening=psds_for_whitening,
    window_length=window_length,
    cutoff_time=cutoff_time,
    forward_zeroes=args.kernel_length,
)

data_f = {
    channel: data[channel].to_frequencyseries()
    for channel in ['LISA_A','LISA_E']
}

logging.info(f"Beginning filtering with bank %s", args.bank_file)
max_snrsq = 0
snr_vals = "Problem - no SNRs found > 0"
with h5py.File(args.bank_file, 'r') as bank_file:
    for idx in tqdm(range(len(bank_file['mass1'])), disable=False):

        if args.reduce_bank_factor is not None and idx % args.reduce_bank_factor:
                # For testing: reduce the bank size by this factor to make the search quicker
                continue
        bank_wf = copy.deepcopy(waveform_params_shared)
        bank_wf['approximant'] = 'BBHX_PhenomD'
        bank_wf['mode_array'] = [(2,2)]
        # Update waveform params to use the ones from the bank file
        bank_wf['tc'] = args.data_length
        bank_wf['mass1'] = bank_file['mass1'][idx]
        bank_wf['mass2'] = bank_file['mass2'][idx]
        bank_wf['inclination'] = bank_file['inclination'][idx]
        bank_wf['polarization'] = bank_file['polarization'][idx]
        bank_wf['spin1z'] = bank_file['spin1z'][idx]
        bank_wf['spin2z'] = bank_file['spin2z'][idx]
        #bank_wf['coa_phase'] = hfile['coa_phase'][idx]
        bank_wf['eclipticlatitude'] = bank_file['eclipticlatitude'][idx]
        bank_wf['eclipticlongitude'] = bank_file['eclipticlongitude'][idx]
    
        snr, iidx, times = get_snr_from_series(
            bank_wf,
            data_f,
            psds_for_whitening,
            window_length=window_length,
            cutoff_time=cutoff_time,
            kernel_length=args.kernel_length,
            search_time=args.search_time,
            delta_t=1. / args.sample_rate,
        )

        snr_qs = snr[0] ** 2 + snr[1] ** 2
        if snr_qs > max_snrsq:
            max_snrsq = snr_qs
            snr_vals = [idx, snr, max_snrsq ** 0.5, iidx, times, copy.deepcopy(bank_wf)]

print(snr_vals)

# The following is all for testing, so we exit here
if args.plot_best_waveform:
    plot_best_waveform(
        snr_vals,
        data_f,
        psds_for_whitening,
        time_before,
        window_length,
        args.search_time,
        args.kernel_length,
        delta_t=1. / args.sample_rate,
    )
logging.info('Done!')
