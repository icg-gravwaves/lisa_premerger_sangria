"""
This is a script to run the search analysis using a file as input.
"""

# Import necessary libraries
import h5py  # Library for interacting with HDF5 files
import copy  # Library for creating copies of objects
import argparse  # Library for parsing command-line arguments
import logging  # Library for logging messages
import numpy as np
from tqdm import tqdm  # Library for creating progress bars
from matplotlib import pyplot as plt


# Import specific modules from the PyCBC library
import pycbc
import pycbc.psd
from pycbc.types import MultiDetOptionAction  # Custom action for argparse

import ldc.io.hdf5 as hdfio

from inpainting_utils import (
    pre_process_data_lisa_pre_merger_inpaint,  # Function to preprocess data for LISA pre-merger
)

from utils import (
    get_snr_future_series,
    load_ldc_timeseries,
    remove_signals,
    waveform_from_bank
)

# Set up argument parser for command-line arguments
parser = argparse.ArgumentParser()
pycbc.add_common_pycbc_options(parser)

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

# Add argument for the number of days after the end of the 
# data to search for signals. Default 21
parser.add_argument('--days-to-search', type=float, default=21)

parser.add_argument(
    '--time-points-days',
    nargs='+',
    type=float,
    default=[],
    help=''
)

parser.add_argument(
    '--time-point-window',
    type=float,
    default=1800,
    help='Window arouns time-points-days (seconds) to search and report SNRs'
)

# Add argument for the data length with a default value (seconds)
parser.add_argument('--data-length', type=int, default=2592000)

parser.add_argument(
    '--remove-signals-after-coalescence',
    type=float,
    nargs='+', # Accepts one or more values
    help="Remove signals after coalescence. Provide 1 value for all MBHBs, "
         "or 15 space-separated values for individual control."
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
    'the plots should go. Default=CWD',
    default=None,
)

parser.add_argument('--zeroed-length', type=int, default=2 ** 20)

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
if args.verbose is None:
    pycbc.init_logging(1)
else:
    pycbc.init_logging(args.verbose + 1)

delta_f = 1 / (args.zeroed_length / args.sample_rate) # delta_f is not the same for zero-latency vs inpainting as we add extra zeroes to inpainting

flen = args.zeroed_length // 2 + 1

# Set the defaults required for the waveform parameters
waveform_params_shared = {
    'f_lower': args.f_lower,
    'low-frequency-cutoff': 1e-6, 
    'tdi': '1.5',
    't_offset': 0,
    'cutoff_deltat': 0,
    't_obs_start': int(args.zeroed_length / args.sample_rate + 0.5),
    'delta_f': delta_f,
    'f_final': args.sample_rate / 2 + delta_f / 2, # This is a hack to ensure we get the point at f_final returned
    'approximant':'BBHX_PhenomD',
    'mode_array':  [(2,2)],
    'length': flen,
}

future_search_time = args.days_to_search * 86400

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
del data['LISA_T']

mbhb_data = load_ldc_timeseries(
    args.data_file,
    data_group='sky/mbhb/tdi',
    delta_t=1./args.sample_rate,
)

end_idx = int(args.end_time * args.sample_rate) # seconds * hertz = unitless
start_idx = int(end_idx - args.data_length * args.sample_rate) # unitless - unitless
start_time = args.end_time - args.data_length # seconds - number of samples / (number of samples per second) = seconds

logging.info("Cutting to %.0f seconds of data", args.data_length)
logging.info(f'Data from {start_time:.0f} to {args.end_time:.0f}')

for channel in data.keys():
    data[channel] = data[channel][start_idx:end_idx]
    mbhb_data[channel] = mbhb_data[channel][start_idx:end_idx]
    
mbhbs, _ = hdfio.load_array(
        args.data_file,
        name="sky/mbhb/cat"
    )

if args.remove_signals_after_coalescence is not None and not args.remove_all_mbhbs:
    remove_signals(
        data,
        mbhbs,
        mbhb_data,
        data_end_time=args.end_time,
        data_start_time=start_time,
        relative_time_for_removal=args.remove_signals_after_coalescence,
        delta_t=1. / args.sample_rate,
        testing_plots=args.testing_plots,
    )

# Zero padding - this is vital!
for channel in data.keys():
    mean_val = np.mean(data[channel])
    data[channel] = data[channel] - mean_val
    data[channel].resize(args.zeroed_length)

psds = {
    f'LISA_{channel}': pycbc.psd.from_txt(
        args.psd_files[channel],
        flen,
        delta_f,
        delta_f,
        is_asd_file=False,
    )
    for channel in ['A','E']
}
for channel in ['LISA_A','LISA_E']:
    psds[channel] = pycbc.psd.inverse_spectrum_truncation(psds[channel], 86400, delta_f, trunc_method='hann')

logging.info("Generated PSD objects")

if args.testing_plots is not None:
    fig, ax = plt.subplots()
    ax.plot(data['LISA_A'].sample_times, data['LISA_A'])
    ax.plot(data['LISA_E'].sample_times, data['LISA_E'])
    fig.savefig(f'{args.testing_plots}/data_inpainting.png')
    plt.close(fig)

original_length = int(args.data_length * args.sample_rate)

logging.info('Pre-processing data')
logging.info('%d %d %d', args.zeroed_length, original_length, int(original_length + (future_search_time / args.sample_rate)))
#  For inpainting, this will be overwhitened
data_ow_f = pre_process_data_lisa_pre_merger_inpaint(
    data,
    sample_rate=args.sample_rate,
    psds_for_whitening=psds,
    inpaint_start=original_length,
    inpaint_end=int(original_length + (2 * 86400 * args.sample_rate))
)

if args.testing_plots is not None:
    fig, ax = plt.subplots()
    ax.loglog(
        data_ow_f['LISA_A'].sample_frequencies,
        abs(data_ow_f['LISA_A']),
        label='LISA A'
    )
    ax.loglog(
        data_ow_f['LISA_E'].sample_frequencies,
        abs(data_ow_f['LISA_E']),
        label='LISA E'
    )
    ax.legend(loc='upper left')
    fig.savefig(f'{args.testing_plots}/data_overwhitened_inpainting.png')
    plt.close(fig)

tlen = int(args.data_length * args.sample_rate)

time_points_snrs = np.zeros((len(args.time_points_days), 2), dtype=float)
time_points_times = np.zeros((len(args.time_points_days), 2), dtype=float)
time_points_template_idx = np.zeros(len(args.time_points_days), dtype=int)
time_points_data = [None] * len(args.time_points_days)

logging.info(f"Beginning filtering with bank %s", args.bank_file)

snr_vals = "Problem - no SNRs found > 0"
with h5py.File(args.bank_file, 'r') as bank_file:
    for idx in tqdm(range(len(bank_file['mass1'])), disable=False):
        if args.reduce_bank_factor is not None and idx % args.reduce_bank_factor:
            # For testing: reduce the bank size by this factor to make the search quicker
            continue
        logging.debug(idx)
        bank_wf = waveform_from_bank(
            bank_file,
            idx,
            waveform_params_shared,
            args.data_length
        )

        logging.debug('Getting SNR series')
    
        snr_future_series = get_snr_future_series(
            bank_wf,
            data_ow_f,
            psds,
            delta_t=1. / args.sample_rate,
            original_length=tlen,
            zeroed_length=args.zeroed_length,
            forward_days=args.days_to_search,
            time_points_days=args.time_points_days, # The times (in days) to report back specific SNRs
            window_seconds=args.time_point_window,
            gaps=None,
            plot=(idx == 0),
            plot_dir=args.testing_plots
        )

        for i, (time_point, result) in enumerate(zip(args.time_points_days, snr_future_series['windows'])):
            time_points_snrsq = result['snr_A'] ** 2 + result['snr_E'] ** 2
            if time_points_snrsq > (time_points_snrs[i, :] ** 2).sum():
                time_points_snrs[i, :] = [result['snr_A'], result['snr_E']]
                time_points_times[i, :] = result['times']
                time_points_template_idx[i] = idx
                time_points_data[i] = result['data']


    for i, time_point_days in enumerate(args.time_points_days):
        if time_points_snrs[i, :].sum() == 0:
            print('No SNRs above zero found for this time point')
            continue
        best_wf = waveform_from_bank(
            bank_file,
            time_points_template_idx[i],
            waveform_params_shared,
            args.data_length
        )
        print(
            time_point_days,
            [
                time_points_template_idx[i],
                tuple(time_points_snrs[i, :]),
                np.sqrt((time_points_snrs[i, :] ** 2).sum()),
                tuple(time_points_times[i, :]),
                best_wf
            ]
        )
        if args.testing_plots is not None:
            fig, ax = plt.subplots()
            snr_series_A, snr_series_E = time_points_data[i]

            for mbhb in mbhbs:
                ax.axvline(mbhb['CoalescenceTime'], c='k', linestyle='--')
            ax.plot(
                snr_series_A.sample_times,
                snr_series_A,
                label='SNR LISA A'
            )
            ax.plot(
                snr_series_E.sample_times,
                snr_series_E,
                label='SNR LISA E'
            )
            ax.plot(
                snr_series_A.sample_times,
                np.sqrt(snr_series_A ** 2 + snr_series_E ** 2),
                label='Network'
            )
            ax.set_xlim([
                float(snr_series_A._epoch),
                float(snr_series_A.sample_times[-1])
            ])

            ax.legend()
            fig.savefig(f"{args.testing_plots}/series_{time_point_days}_inpainting.png")
            plt.close(fig)

logging.info('Done!')
