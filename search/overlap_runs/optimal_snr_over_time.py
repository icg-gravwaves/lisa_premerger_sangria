"""
This is a script to run the search analysis using a file as input.
"""

# Import necessary libraries
import copy  # Library for creating copies of objects
import argparse  # Library for parsing command-line arguments
import logging  # Library for logging messages
import numpy as np
import h5py
import ldc.io.hdf5 as hdfio
from matplotlib import pyplot as plt
# Use the style file defined in the repository route
plt.style.use('../../paper.mplstyle')



# Import specific modules from the PyCBC library
from pycbc.types import MultiDetOptionAction  # Custom action for argparse
import pycbc.psd
import pycbc.filter
from pycbc import add_common_pycbc_options, init_logging

import sys, os

parent_dir = os.path.abspath("..")

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from common_utils import(
    generate_waveform_for_data,
    insert_bank_options,
    load_bank
)
from plotting_utils import get_colors, plot_optimal_snr_match

rtsumsq = lambda x: np.sqrt(sum(xi ** 2 for xi in x))

# Set up argument parser for command-line arguments
parser = argparse.ArgumentParser()
add_common_pycbc_options(parser)
parser.add_argument(
    '--psd-files',
    required=True,
    action=MultiDetOptionAction,
)

# Add argument for the data file (required)
parser.add_argument('--data-file', required=True)

# Time before and after to plot the optimal SNR and fitting factor
parser.add_argument("--days-before", type=float, default=25)
parser.add_argument('--days-after', type=float, default=5)
# How many points to calculate optimal SNR and fitting factor for
parser.add_argument('--n-points', type=int, default=1200)

# Time before merger to cut the merger and apply the zero latency filter
parser.add_argument('--premerger-days', type=float, nargs='+')

parser.add_argument(
    '--data-pad',
    type=float,
    default=15,
    help='Number of days data to add before and after the '
    'days-before/days-after argument to allow for data corruption/wraparound effects'
)

# Add argument for the lower frequency cutoff with a default value
parser.add_argument('--f-lower', type=float, default=1e-6)

# Add argument for the sample rate with a default value
parser.add_argument('--sample-rate', type=float, default=0.2)

parser.add_argument('--output-file', required=True)

parser.add_argument('--output-plot-format')
parser.add_argument('--space', default='linear', choices=['log', 'linear'])

parser.add_argument('--signal-number', type=int, choices=np.arange(15),
                    help="If given, restrict the signal number loop "
                         "to only this signal")

parser.add_argument('--calculate-fitting-factor', action='store_true')
parser.add_argument('--kernel-length', type=int, default=17280)

insert_bank_options(parser, bank_required=False)
# Parse the command-line arguments provided by the user
args = parser.parse_args()

init_logging(args.verbose)

window_length = 17280

mbhbs, _ = hdfio.load_array(args.data_file, name="sky/mbhb/cat")

seconds_before_data = (args.days_before + args.data_pad) * 86400
seconds_after_data = (args.days_after + args.data_pad) * 86400
data_length_s = seconds_before_data + seconds_after_data

flen = int(data_length_s * args.sample_rate) // 2 + 1
delta_f = 1 / data_length_s

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

if args.space == 'linear':
    cutoff_days = np.linspace(
        -args.days_after,
        args.days_before,
        args.n_points
    )
else:
    if args.days_after != 5:
        # if args.days after is not the default, warn but dont fail
        logging.warning('--days-after and ---space log are given, ignoring --days-after')

    # Use points on a log scale
    linthresh = 0.1
    n_before = int(args.n_points * args.days_before / (args.days_before + args.days_after))
    n_after = args.n_points - n_before
    print(n_before, n_after)
    cutoff_days_before = np.logspace(
        np.log10(linthresh),
        np.log10(args.days_before),
        num=n_before
    )
    cutoff_days_after = -np.logspace(
        np.log10(linthresh),
        np.log10(args.days_after),
        num=n_after
    )
    cutoff_days = np.concatenate((cutoff_days_before, cutoff_days_after))


# Make sure that the premerger days in the plot are also in the cutoff_days array
cutoff_days = np.sort(np.concatenate((
    cutoff_days,
    args.premerger_days + [0]
)))[::-1]

logging.info('Using %d points', cutoff_days.size)

with h5py.File(args.output_file,'w') as ofile:
    ofile.create_dataset(
        'cutoff_days',
        data=-cutoff_days,
    )

if args.calculate_fitting_factor:
    bank_array = load_bank(args)

premerger_colours = get_colors(values=args.premerger_days, vmin=0.5, vmax=14)
width = plt.rcParams["figure.figsize"][0]
height = plt.rcParams["figure.figsize"][1] * 1.25

for signal_number, mbhb in enumerate(mbhbs):
    if args.signal_number is not None and not signal_number == args.signal_number:
        continue
    logging.info("Signal number %d", signal_number)
    coalescence_time = mbhb['CoalescenceTime']
    logging.info('Generating signal')
    signal = generate_waveform_for_data(
        mbhb,
        coalescence_time - seconds_before_data,
        coalescence_time + seconds_after_data,
        delta_t = 1. / args.sample_rate
    )
    del signal['LISA_T']

    cut_match_over_time_all = {}
    cut_match_over_time_ts_all = {}
    logging.info('Calculating match with pre-merger cut waveforms')
    for premerger_day in args.premerger_days:
        signal_premerger = copy.deepcopy(signal)
        snrsq_cm = np.zeros_like(signal['LISA_A'].sample_times)
        for channel in signal_premerger.keys():
            start_idx = int((coalescence_time - 86400 * premerger_day - signal_premerger[channel]._epoch) * args.sample_rate)
            signal_premerger[channel][start_idx:] = 0

            snrsq_ts = abs(pycbc.filter.matched_filter(
                signal_premerger[channel],
                signal[channel],
                psd=psds_standard[channel],
                low_frequency_cutoff=delta_f,
            ))
            snrsq_ts = snrsq_ts.cyclic_time_shift(-86400 * (premerger_day + args.days_after + args.data_pad))
            snrsq_cm += np.abs(snrsq_ts._data) ** 2
        cut_match_over_time_ts = np.sqrt(snrsq_cm)

        cut_match_over_time = np.interp(
            -cutoff_days * 86400,
            signal['LISA_A'].sample_times - coalescence_time,
            cut_match_over_time_ts
        )
        cut_match_over_time_all[premerger_day] = cut_match_over_time
        cut_match_over_time_ts_all[premerger_day] = cut_match_over_time_ts
    
    logging.info('Calculating Optimal SNR')
    optimal_snr_over_time = np.zeros_like(cutoff_days)
    for i, cutoff_day in enumerate(cutoff_days):
        cutoff_s = cutoff_day * 86400
        signal_cutoff = copy.deepcopy(signal)
        snrsq_optimal = 0
        for channel in signal_cutoff.keys():
            to_zero = signal_cutoff[channel].sample_times > (coalescence_time - cutoff_s)
            signal_cutoff[channel]._data[to_zero] = 0
            snrsq_optimal += pycbc.filter.sigmasq(
                signal_cutoff[channel],
                psd=psds_standard[channel],
                low_frequency_cutoff=delta_f,
            )
        optimal_snr_over_time[i] = np.sqrt(snrsq_optimal)

    with h5py.File(args.output_file,'a') as ofile:
        signal_grp = ofile.create_group(
            f'signal_{signal_number:d}',
        )
        signal_grp.create_dataset(
            'optimal_snr',
            data=optimal_snr_over_time,
        )
        for premerger_day in args.premerger_days:
            signal_grp.create_dataset(
                f'match_cut_{premerger_day:.0f}_days',
                data=cut_match_over_time_all[premerger_day]
            )


    if args.output_plot_format is not None:
        logging.info('Plotting')
        fig, _ = plot_optimal_snr_match(
            -cutoff_days,
            optimal_snr_over_time,
            cut_match_over_time_all,
            signal_number=signal_number
        )

        output_fname = args.output_plot_format.format(signal_no=signal_number)
        logging.info("Outputting to %s", output_fname)
        fig.savefig(output_fname)