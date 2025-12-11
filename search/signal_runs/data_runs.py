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

# Import utility functions from the utils module
from utils import (
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
parser.add_argument(
    '--testing-plots',
    help='Plots to help with testing, give directory where '
    'the plots should go.',
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
    'approximant': 'BBHX_PhenomD',
    'mode_array': [(2,2)],
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
data_length_idx = int(args.data_length * args.sample_rate) # seconds * hertz = unitless
start_idx = int(end_idx - data_length_idx) # unitless - unitless
start_time = args.end_time - args.data_length # seconds - number of samples / (number of samples per second) = seconds

logging.info("Cutting to %.0f seconds of data", args.data_length)
logging.info(f'Data from {start_time:.0f} to {args.end_time:.0f}')

for channel in data.keys():
    data[channel] = data[channel][start_idx:end_idx]
    mbhb_data[channel] = mbhb_data[channel][start_idx:end_idx]
    
mbhbs, _ = hdfio.load_array(args.data_file, name="sky/mbhb/cat")

if args.remove_signals_after_coalescence is not None and not args.remove_all_mbhbs:
    for i, mbhb in enumerate(mbhbs):

        if args.end_time < (mbhb['CoalescenceTime'] + args.remove_signals_after_coalescence):
            logging.info("Signal %d at %.0f not yet reached", i, mbhb['CoalescenceTime'])
            continue

        if mbhb['CoalescenceTime'] < (args.end_time - args.data_length * 2):
            logging.info("Signal %d at %.0f is well before the searched time - ignore it", i, mbhb['CoalescenceTime'])
            continue
    
        logging.info("Removing signal %d at %.0f from data", i, mbhb['CoalescenceTime'])

        waveform_for_removal = generate_waveform_for_data(
            mbhb,
            start_time,
            args.end_time,
            1. / args.sample_rate,
        )

        logging.info('Removing from data')
        subtracted = {
            channel: data[channel] - waveform_for_removal[channel]
            for channel in data.keys()
        }

        if args.testing_plots is not None:
            logging.info('Plotting waveform and data before and after removal')
            fig1, ax1 = plt.subplots(1)
            ax1.plot(
                data['LISA_A'].sample_times - mbhb['CoalescenceTime'],
                data['LISA_A'],
                label='Data LISA A',
                alpha=0.25
            )
            ax1.plot(
                data['LISA_E'].sample_times - mbhb['CoalescenceTime'],
                data['LISA_E'],
                label='Data LISA E',
                alpha=0.25
            )
            ax1.plot(
                mbhb_data['LISA_A'].sample_times - mbhb['CoalescenceTime'],
                mbhb_data['LISA_A'],
                c='tab:blue',
                label='MBHB LISA_A',
            )
            ax1.plot(
                mbhb_data['LISA_E'].sample_times - mbhb['CoalescenceTime'],
                mbhb_data['LISA_E'],
                c='tab:orange',
                label='MBHB LISA_E',
            )
            ax1.plot(
                waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
                waveform_for_removal['LISA_A'],
                c='tab:green',
                linestyle=':',
                label='Waveform LISA A'
            )
            ax1.plot(
                waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
                waveform_for_removal['LISA_E'],
                c='tab:red',
                linestyle=':',
                label='Waveform LISA E'
            )

            ax1.axvline(0, c='black', linestyle='--', alpha=0.5)
            ax1.grid()
            ax1.set_xlim(-2000, 1000)
            ax1.set_ylim(-1e-19, 1e-19)
            ax1.legend(loc='upper left')
            fig1.savefig(f"{args.testing_plots}/waveform_for_removal_zerolatency_{i}.png")
            plt.close(fig1)

            fig2, ax2 = plt.subplots(1)
            ax2.plot(
                waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
                data['LISA_A'],
                alpha=0.5,
                c='tab:blue',
                label='Original LISA A'
                )
            ax2.plot(
                waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
                data['LISA_E'],
                alpha=0.5,
                c='tab:orange',
                label='Original LISA E'
            )
            ax2.plot(
                waveform_for_removal['LISA_A'].sample_times - mbhb['CoalescenceTime'],
                subtracted['LISA_A'],
                c='tab:blue',
                label='Subtracted LISA A'
                )
            ax2.plot(
                waveform_for_removal['LISA_E'].sample_times - mbhb['CoalescenceTime'],
                subtracted['LISA_E'],
                c='tab:orange',
                label='Subtracted LISA E'
            )
            ax2.axvline(0, c='black', linestyle='--', alpha=0.5)
            ax2.grid()
            ax2.set_xlim(-2000, 1000)
            ax2.set_ylim(-1e-19, 1e-19)
            ax2.legend(loc='upper left')
            fig2.savefig(f"{args.testing_plots}/waveform_removed_zerolatency_{i}.png")
            plt.close(fig2)

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

if args.testing_plots is not None:
    fig, ax = plt.subplots()
    ax.plot(data['LISA_A'].sample_times, data['LISA_A'])
    ax.plot(data['LISA_E'].sample_times, data['LISA_E'])
    fig.savefig(f'{args.testing_plots}/data_zerolatency.png')
    plt.close(fig)

data_pp = pre_process_data_lisa_pre_merger(
    data,
    sample_rate=args.sample_rate,
    psds_for_whitening=psds_for_whitening,
    window_length=window_length,
    cutoff_time=cutoff_time,
    forward_zeroes=args.kernel_length,
)

data_f = {
    channel: data_pp[channel].to_frequencyseries()
    for channel in data_pp.keys()
}


if args.testing_plots is not None:
    data_ow_f = {
        channel: data_f[channel] * psds_for_whitening[channel]
        for channel in data_f
    }
    fig, ax = plt.subplots()
    ax.loglog(
        data_ow_f['LISA_A'].sample_frequencies,
        abs(data_ow_f['LISA_A'])
    )
    ax.loglog(
        data_ow_f['LISA_E'].sample_frequencies,
        abs(data_ow_f['LISA_E'])
    )
    fig.savefig(f'{args.testing_plots}/data_overwhitened_zerolatency.png')
    plt.close(fig)

logging.info(f"Beginning filtering with bank %s", args.bank_file)
max_snrsq = 0
snr_vals = "Problem - no SNRs found > 0"
with h5py.File(args.bank_file, 'r') as bank_file:
    for idx in tqdm(range(len(bank_file['mass1'])), disable=False):

        if args.reduce_bank_factor is not None and idx % args.reduce_bank_factor:
            # For testing: reduce the bank size by this factor to make the search quicker
            continue
        bank_wf = copy.deepcopy(waveform_params_shared)
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
    
        snr, _, times, series = get_snr_from_series(
            bank_wf,
            data_f,
            psds_for_whitening,
            window_length=window_length,
            cutoff_time=cutoff_time,
            kernel_length=args.kernel_length,
            search_time=args.search_time,
            delta_t=1. / args.sample_rate,
            plot=args.testing_plots is not None
        )

        if args.testing_plots is not None:
            fig, ax = plt.subplots()
            search_slice = slice(len(series['LISA_A'])-int(args.search_time * args.sample_rate), len(series['LISA_A']))
            for mbhb in mbhbs:
                ax.axvline(mbhb['CoalescenceTime'], c='k', linestyle='--')
            ax.plot(
                series['LISA_A'].sample_times[search_slice] + cutoff_time,
                series['LISA_A'][search_slice],
                label='SNR LISA A'
            )
            ax.plot(
                series['LISA_E'].sample_times[search_slice] + cutoff_time,
                series['LISA_E'][search_slice],
                label='SNR LISA E'
            )
            ax.plot(
                series['LISA_E'].sample_times[search_slice] + cutoff_time,
                np.sqrt(series['LISA_A'][search_slice] ** 2 + series['LISA_E'][search_slice] ** 2),
                label='Network'
            )
            ax.set_xlim([
                float(series['LISA_E'][search_slice]._epoch) + cutoff_time,
                float(series['LISA_E'][search_slice].sample_times[-1] + cutoff_time)
            ])

            ax.legend()
            fig.savefig(f"{args.testing_plots}/series_{idx}_zerolatency.png")
            plt.close(fig)

        snr_qs = snr[0] ** 2 + snr[1] ** 2
        if snr_qs > max_snrsq:
            max_snrsq = snr_qs
            snr_vals = [idx, snr, max_snrsq ** 0.5, times, copy.deepcopy(bank_wf)]

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
