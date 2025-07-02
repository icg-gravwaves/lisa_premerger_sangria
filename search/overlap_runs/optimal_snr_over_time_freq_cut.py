import numpy as np
import argparse
import pycbc
import pycbc.psd
import pycbc.waveform
import pycbc.filter
from tqdm import tqdm
import h5py
from matplotlib import pyplot as plt

from pycbc.pnutils import get_inspiral_tf
from pycbc.types import MultiDetOptionAction
from pycbc.psd import interpolate

import ldc.io.hdf5 as hdfio

from utils import (
    ldc_to_bbhx
)

# Some top-level parameters
f_nyquist = 0.01
tlen = 86400 * 40
delta_f = 1. / (tlen * 2) # Note that this is not long enough to represent in the time-domain, but we won't do that!
low_freq_cutoff = max(1e-06, delta_f)
nominal_distance = 2000

parser = argparse.ArgumentParser()
parser.add_argument('--data-file', required=True)
parser.add_argument(
    '--psd-files',
    required=True,
    action=MultiDetOptionAction,
)

parser.add_argument(
    '--max-days-before',
    type=float,
    default=25,
)
parser.add_argument(
    '--max-days-after',
    type=float,
    default=5,
)
parser.add_argument(
    '--n-points',
    type=int,
    default=1200,
)

parser.add_argument(
    '--output-file',
    required=True,
    help="File to output the optimal SNRs over time"
)
parser.add_argument('--output-plot-format') # currently unused
parser.add_argument(
    '--f-lower',
    type=float,
    default=1e-6,
    help="Low frequency cutoff for calculating SNR, in Hz. Default 1e-6"
)
# Add argument for the data length with a default value (seconds)
parser.add_argument('--data-length', type=int, default=2592000)

# Add argument for reducing the bank factor
parser.add_argument('--reduce-bank-factor', type=int,
                    default=1,
                    help="Reduce the bank by a factor of this number, "
                         "useful for performing the search quickly in testing"
                         "Default: don't do this")


# Add argument for the bank file (required)
parser.add_argument('--bank-files', required=True, action=MultiDetOptionAction)e)

# Add argument for the number of days before merger (required)
parser.add_argument('--days-before-merger', required=True)


args = parser.parse_args()

if args.f_lower < delta_f:
    args.f_lower = delta_f

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

# Open the PSD, load as PyCBC object
psds = {
    f'LISA_{channel}': interpolate(
        pycbc.psd.from_txt(
            args.psd_files[channel],
            int(f_nyquist/delta_f),
            delta_f,
            low_freq_cutoff,
            is_asd_file=False
        ),
        1 / args.data_length
    )
    for channel in ['A', 'E']
}

cutoff_days = np.linspace(
    -args.max_days_before,
    args.max_days_after,
    args.n_points
)

waveform_params_shared = {
    't_obs_start': args.data_length, # This is setting the data length.
    'f_lower': args.f_lower,
    'low-frequency-cutoff': 1e-6, 
    'delta_f': 1 / args.data_length,
    'tdi': '1.5',
    't_offset': 0,
    'approximant': 'BBHX_PhenomD',
    'mode_array': [(2,2)],
    'tc': args.data_length,
}

mbhbs, _ = hdfio.load_array(args.data_file, name="sky/mbhb/cat")

def get_optimal_snr(t, signal_number):
    """
    Get the sensitive distance given the masses
    at the time-before-merger considered
    """
    signal_waveform = ldc_to_bbhx(
        mbhbs[signal_number],
        waveform_params_shared
    )

    # Calculate the time-frequency track in order
    # to convert and get the right upper frequency cutoff
    track_t, track_f = get_inspiral_tf(
        0,
        signal_waveform['mass1'],
        signal_waveform['mass2'],
        signal_waveform['spin1z'], 
        signal_waveform['spin2z'],
        args.f_lower,
        approximant='SPAtmplt'
    )
    freq = np.interp(t, track_t, track_f)

    if freq < (args.f_lower + 2 * delta_f):
        # This frequency / time before merger is too low
        # frequency, and won't give sensible results
        return np.nan
    
    sum_sigsq = 0

    wf = pycbc.waveform.get_fd_det_waveform(
        **signal_waveform,
        ifos=['LISA_A','LISA_E'],
        f_final=freq,
    )

    for channel in ['LISA_A','LISA_E']:
        sig = pycbc.filter.sigma(
            wf[channel],
            psds[channel][:len(wf[channel])],
            low_frequency_cutoff=args.f_lower,
            high_frequency_cutoff=freq
        )
        sum_sigsq += sig ** 2
    
    return np.sqrt(sum_sigsq)

with h5py.File(args.output_file,'w') as ofile:
    ofile.create_dataset(
        'cutoff_days',
        data=cutoff_days,
    )

for signal_number in np.arange(15):
    print("Signal number %d" % signal_number)
    optimal_snr_over_time = np.zeros_like(cutoff_days)
    cutoff_times = cutoff_days * 86400
    for i, t in enumerate(cutoff_times):
        optimal_snr_over_time[i] = get_optimal_snr(t, signal_number)
    plt.semilogy(
        cutoff_days,
        optimal_snr_over_time
    )
    plt.grid()
    plt.ylabel('Optimal SNR')
    plt.xlabel('Time')
    plt.savefig(f'results/TEST/optimal_snr_freq_cut_{signal_number}.png')

    with h5py.File(args.output_file, 'a') as ofile:
        ofile.create_dataset(
            f'optimal_snr_signal_{signal_number}',
            data=optimal_snr_over_time
        )

