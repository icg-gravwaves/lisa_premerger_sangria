import numpy as np
import argparse
import pycbc
import pycbc.psd
import pycbc.waveform
import pycbc.filter
from pycbc.types import MultiDetOptionAction
from tqdm import tqdm
import h5py
import logging

from pycbc import init_logging, add_common_pycbc_options
from pycbc.pnutils import get_inspiral_tf

# Some top-level parameters
f_nyquist = 0.1
nominal_distance = 200

parser = argparse.ArgumentParser()
add_common_pycbc_options(parser)
parser.add_argument(
    '--psd-files',
    required=True,
    nargs=2,
    action=MultiDetOptionAction
)
parser.add_argument(
    '--mass-range',
    nargs=2,
    type=float,
    required=True,
    help="Range of component masses to calculate, min/max"
)
parser.add_argument(
    '--log-mass-spacing',
    action='store_true',
    help="Use a range of masses separated logarithmically. Default linear.")
parser.add_argument(
    '--n-mass-points',
    type=int,
    default=1000,
    help='Number of points to use in mass spacing. Default 1000.'
)
parser.add_argument(
    '--n-sky-points',
    type=int,
    default=1000,
    help='Number of sky points to use to calculate the optimal SNR.'
)
parser.add_argument(
    '--q',
    type=float,
    default=1
)
parser.add_argument(
    '--output-file',
    required=True,
    help="File to output the times, masses and distances for plotting"
)
parser.add_argument(
    '--low-frequency-cutoff',
    type=float,
    default=1e-7,
    help="Low frequency cutoff for calculating SNR, in Hz. Default 1e-7"
)
parser.add_argument(
    '--parallelize-range',
    default='0/1'
)
parser.add_argument(
    '--times',
    nargs='+',
    type=float,
    help="Specific times to calculate, seconds."
)

args = parser.parse_args()

init_logging(args.verbose)

logging.info("Setting up PSDs")
# Set up psds of different lengths ready to analyse different
# length signals:
tlen_days_all = np.array(
    [30, 40, 60, 80, 100, 200, 365.25, 2 * 365.25, 3 * 365.25]
)
tlens = tlen_days_all * 86400
psds = {channel: {} for channel in ['A','E']}
psd_lens = np.zeros(len(tlens))
delta_fs = np.zeros(len(tlens))
for i, tlen in enumerate(tlens):
    logging.info("%d / %d: %d days", i, tlens.size, tlen / 86400)
    delta_f = 1. / (tlen * 2)
    # Open the PSD, load as PyCBC object
    for channel in ['A','E']:
        psd = pycbc.psd.from_txt(
            args.psd_files[channel],
            int(f_nyquist/delta_f),
            delta_f,
            args.low_frequency_cutoff,
            is_asd_file=False
        )
        psds[channel][tlen] = psd
        # These _should_ be the same for both channels,
        # so it doesn't matter which is saved
    psd_lens[i] = len(psd)
    delta_fs[i] = delta_f


logging.info("Loaded %d psds for various time lengths", tlens.size * 2)

if args.log_mass_spacing:
    masses = np.logspace(
        np.log10(args.mass_range[0]),
        np.log10(args.mass_range[1]),
        args.n_mass_points,
    )
else:
    masses = np.linspace(
        args.mass_range[0],
        args.mass_range[1],
        args.n_mass_points,
    )

logging.info("Set up masses")

times = np.array(args.times)

shared_waveform = {
    'ifos':['LISA_A','LISA_E','LISA_T'],
    'approximant':'BBHX_PhenomD',
    'spin1z':0,
    'spin2z':0,
    'distance':nominal_distance,
    't_offset':0,
    'tdi': '1.5',
}

def get_sensitive_distance(t, m):
    """
    Get the sensitive distance given the masses
    at the time-before-merger considered
    """
    # Calculate the time-frequency track in order
    # to convert and get the right upper frequency cutoff
    
    track_t, track_f = get_inspiral_tf(
        0, m, m, 0, 0,
        args.low_frequency_cutoff,
        approximant='SPAtmplt'
    )
    if t == 0:
        freq_upper = f_nyquist
    else:
        freq_upper = np.interp(-t, track_t, track_f)

    freq_upper = min(f_nyquist, freq_upper)
    freq_lower = np.interp(-86400 * 365.25 * 3, track_t, track_f)
    freq_lower = max(args.low_frequency_cutoff, freq_lower)

    # Using a standard seed keeps the sky points the same for
    # all points and any repeats
    np.random.seed(24601)
    sum_sigsq = 0
    n_valid = 0
    for _ in range(args.n_sky_points):
        template = {
            **shared_waveform,
            'mass1':m,
            'mass2':m,
            'f_final':freq_upper,
            'coa_phase':np.random.uniform(0, np.pi * 2),
            'inclination':np.arccos(np.random.uniform(0,1)),
            'polarization':np.random.uniform(0, np.pi * 2),
            'eclipticlatitude':np.arccos(np.random.uniform(0,1)),
            'eclipticlongitude':np.random.uniform(0, np.pi * 2),
            'f_lower':freq_lower
        }
        
        wf = pycbc.waveform.get_fd_det_waveform(
            **template,
            delta_f = delta_fs[0],
            t_obs_start=tlens[0],
            tc=tlens[0] - 43200,
        )
        psd_i = np.argmax(psd_lens >= wf['LISA_A'].data.size)
        #print(t, m, wf['LISA_A'].data.size, len(psds[tlens[psd_i]]))
        wf = pycbc.waveform.get_fd_det_waveform(
            **template,
            delta_f = delta_fs[psd_i],
            t_obs_start=tlens[psd_i],
            tc=tlens[psd_i] - 86400,
        )
        try:
            for channel in ['A','E']:
                sig = pycbc.filter.sigma(
                    wf['LISA_' + channel],
                    psds[channel][tlens[psd_i]][:len(wf['LISA_' + channel])],
                    low_frequency_cutoff=freq_lower,
                    high_frequency_cutoff=freq_upper
                )
                sum_sigsq += sig ** 2
            n_valid += 1
        except ValueError:
            continue
    
    if n_valid > 0 and sum_sigsq > 0:
        mean_sigsq = sum_sigsq / n_valid
        dist_out = np.sqrt(mean_sigsq) / 10 * (nominal_distance / 1000)
    else:
        dist_out = np.nan
    
    return dist_out

masses_all, times_all = np.meshgrid(masses, times)

masses_all = masses_all.flatten()
times_all = times_all.flatten()

ids = np.arange(len(masses_all))

part = float(args.parallelize_range.split('/')[0])
pieces = float(args.parallelize_range.split('/')[1])
imin = int(masses_all.size / float(pieces) * part)
imax = int(masses_all.size / float(pieces) * (part + 1))

np.random.seed(0)
np.random.shuffle(ids)
ids = ids[imin:imax]

logging.info("Selected %s randomly shuffled time-mass pairs", imax - imin)

masses_all = masses_all[ids]
times_all = times_all[ids]

dists = np.zeros_like(times_all)

m_t = list(zip(masses_all, times_all))
for i, (m, t) in enumerate(tqdm(m_t)):

    dists[i] = get_sensitive_distance(t, m)
    continue

logging.info("Got sensitive distances")

with h5py.File(args.output_file, 'w') as out_f:
    out_f['mass'] = masses_all.flatten()
    out_f['time'] = times_all.flatten()
    out_f['distance'] = dists
    out_f.attrs['mass_range'] = args.mass_range
    out_f.attrs['times'] = args.times
