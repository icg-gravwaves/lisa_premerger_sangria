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
    get_snr_series,
    get_snr_point
)
rtsumsq = lambda x: np.sqrt(sum(xi ** 2 for xi in x))

# Set up argument parser for command-line arguments
parser = argparse.ArgumentParser()

parser.add_argument(
    '--psd-files',
    required=True,
    action=MultiDetOptionAction,
)

# Add argument for the bank file (required)
parser.add_argument('--bank-files', required=True, action=MultiDetOptionAction)

# Add argument for the data file (required)
parser.add_argument('--data-file', required=True)

# Add argument for the number of days before merger (required)
parser.add_argument('--days-before-merger', required=True)

parser.add_argument("--days-before", type=float, default=25)

# Add argument for the kernel length with a default value
parser.add_argument('--kernel-length', type=int, default=17280)

# Add argument for the data length with a default value (seconds)
parser.add_argument('--data-length', type=int, default=2592000)

# Add argument for the lower frequency cutoff with a default value
parser.add_argument('--f-lower', type=float, default=1e-6)

# Add argument for the sample rate with a default value
parser.add_argument('--sample-rate', type=float, default=0.2)

parser.add_argument('--output-file', required=True)

parser.add_argument('--output-plot')

parser.add_argument('--n-points', type=int, default=1200)

parser.add_argument('--days-after', type=float, default=5)

parser.add_argument('--signal-number', type=int, choices=np.arange(15))

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

bank_dtype=np.dtype([
    ('mass1', np.float64),
    ('mass2', np.float64),
    ('spin1z', np.float64),
    ('spin2z', np.float64),
    ('eclipticlatitude', np.float64),
    ('eclipticlongitude', np.float64),
    ('inclination', np.float64),
    ('polarization', np.float64)
])

def load_bank(filename):
    with h5py.File(filename,'r') as bank_file:
        n_templates = bank_file['mass1'].size

    bank_array = np.zeros(n_templates, dtype=bank_dtype)
    with h5py.File(filename,'r') as bank_file:
        for k in bank_dtype.names:
            bank_array[k] = bank_file[k][:]
    return bank_array

bank_array = load_bank(args.bank_files[args.days_before_merger])

bank_array = bank_array[::args.reduce_bank_factor]

cutoff_days = np.linspace(
    -args.days_after,
    args.days_before,
    args.n_points
)[::-1]

with h5py.File(args.output_file,'w') as ofile:
    ofile.create_dataset(
        'cutoff_days',
        data=-cutoff_days[::-1],
    )

logging.info("Signal number %d", args.signal_number)
snr_over_time = np.zeros_like(cutoff_days)
fitting_factor_over_time = np.zeros_like(cutoff_days)
optimal_snr_over_time = np.zeros_like(cutoff_days)
signal_waveform = ldc_to_bbhx(
    mbhbs[args.signal_number],
    waveform_params_shared
)

gen_data_length = (2 * args.data_length + args.days_before + args.days_after + 0.1) * 86400
generate_waveform = copy.deepcopy(signal_waveform)
generate_waveform.update({
    't_obs_start': gen_data_length,
    'delta_f': 1 / gen_data_length,
    'tc': gen_data_length,
})

outs = pycbc.waveform.get_fd_det_waveform(
    ifos=['LISA_A','LISA_E'],
    **generate_waveform
)

fig, ax = plt.subplots()
data_t = {}
for channel in outs:
    data_t[channel] = outs[channel].to_timeseries()
    data_t[channel] = data_t[channel].cyclic_time_shift(
        -args.days_after * 86400
    )
    data_t[channel]._epoch = -gen_data_length + args.days_after * 86400
    ax.plot(
        data_t[channel].sample_times / 86400,
        data_t[channel],
        label=channel
    )
    ax.legend()
# ax.set_xlim(-0.2, 0.05)
ax.grid()
fig.savefig('test.png')

# data = generate_waveform_lisa_pre_merger(
#     signal_waveform,
#     psds_for_whitening,
#     sample_rate=args.sample_rate,
#     window_length=window_length,
#     cutoff_time=cutoff_s,
#     forward_zeroes=args.kernel_length,
# )

logging.info("Calculating optimal SNR over time")
for i, cutoff_day in enumerate(tqdm(cutoff_days)):
    end_time = cutoff_day * 86400
    # end_idx = 
    # start_idx = 
    # data_processed = 

    optimal_snr = get_optimal_snr(
        signal_waveform,
        psds_for_whitening,
        end_time,
        window_length=window_length,
        delta_t=1. / args.sample_rate,
        kernel_length=args.kernel_length,
    )

    optimal_snr_over_time[i] = rtsumsq(optimal_snr)

    data = generate_waveform_lisa_pre_merger(
        signal_waveform,
        psds_for_whitening,
        sample_rate=args.sample_rate,
        window_length=window_length,
        cutoff_time=cutoff_s,
        forward_zeroes=args.kernel_length,
    )

    snr_max = 0
    for bank_idx in range(bank_array.size):
        if bank_idx > 0: continue
        bank_wf = copy.deepcopy(waveform_params_shared)
        bank_wf.update({
            k: bank_array[k][bank_idx]
            for k in bank_dtype.names
        })

        snr = get_snr_point(
            bank_wf,
            data,
            psds_for_whitening,
            delta_t=1. / args.sample_rate,
            window_length=window_length,
            cutoff_time=cutoff_s,
            kernel_length=args.kernel_length,
        )

        snr_max = max(
            snr_max,
            np.sqrt(snr[0] ** 2 + snr[1] ** 2)
        )

    snr_over_time[i] = snr_max


logging.info(
    "Updating zero cutoff time and later to be the full signal"
)

optimal_snr_over_time[cutoff_days <= 0] = rtsumsq(get_full_optimal_snr(
    signal_waveform,
    psds_standard
))

with h5py.File(args.output_file,'a') as ofile:
    ofile.create_dataset(
        f'optimal_snr_signal_{args.signal_number}',
        data=optimal_snr_over_time[::-1],
    )

if args.output_plot is not None:
    fig, ax = plt.subplots()
    ax.plot(
        -cutoff_days,
        optimal_snr_over_time,
        label='Optimal'
    )
    ax.plot(
        -cutoff_days,
        snr_over_time,
        label='SNR'
    )
    ax.semilogy()
    ax.legend()
    ax.set_title(f'SNR vs time, signal {args.signal_number}')
    ax.grid()
    ax.set_xlabel('Cutoff time')
    ax.set_ylabel('SNR')
    fig.savefig(args.output_plot)