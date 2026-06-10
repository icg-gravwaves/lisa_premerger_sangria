import numpy as np
from copy import deepcopy
import logging

from pycbc.pnutils import get_inspiral_tf
from pycbc.waveform import get_fd_det_waveform
from pycbc import add_common_pycbc_options, init_logging

import ldc.io.hdf5 as hdfio
from ldc.common import tools as ldc_tools


import argparse

import sys
import os

search_dir = os.path.abspath("../search")

if search_dir not in sys.path:
    sys.path.insert(0, search_dir)


# Everything plotted in this notebook is done using these helper modules
from common_utils import generate_waveform_for_data

parser = argparse.ArgumentParser()
parser.add_argument('--signal-number', type=int, required=True)
add_common_pycbc_options(parser)
args = parser.parse_args()


# Initialize logging for the PyCBC library
if args.verbose is None:
    init_logging(1)
else:
    init_logging(args.verbose + 1)

input_data = '../datasets/LDC2_sangria_hm_training.hdf' # The Sangria dataset

# Approximate characteristic strain with cutoffs for each time before merger
mbhbs, _ = hdfio.load_array(input_data, name="sky/mbhb/cat")

# days before merger to use as cutoffs
cutoff_days = [0.5, 1, 4, 7, 14]
data_length = 24 * 2592000

def spin_conv(mag, pol):
    return mag*np.cos(pol)


hc_all = {}
sig_num = args.signal_number

logging.info('Generating waveform for signal %s', sig_num)
mbhb = mbhbs[sig_num]
psi, incl = ldc_tools.aziPolAngleL2PsiIncl(
    mbhb["EclipticLatitude"],
    mbhb["EclipticLongitude"],
    mbhb['InitialPolarAngleL'],
    mbhb['InitialAzimuthalAngleL']
)
# Generate the waveform
wf = {}
wf['mass1'] = mbhb['Mass1']
wf['mass2'] = mbhb['Mass2']
wf['spin1z'] = spin_conv(mbhb['Spin1'],mbhb['PolarAngleOfSpin1'])
wf['spin2z'] = spin_conv(mbhb['Spin2'],mbhb['PolarAngleOfSpin2'])

sig_ts = generate_waveform_for_data(
    mbhb,
    0,
    365.25*86400,
    5,
)
A_sig_psd = {}
for channel, sig_psd in sig_ts.items():
    A_sig_psd[channel] = sig_psd.to_frequencyseries()


# compute characteristic strain from waveform
freqs = A_sig_psd['LISA_A'].sample_frequencies.numpy()
amp_A = np.abs(A_sig_psd['LISA_A'].numpy())
amp_E = np.abs(A_sig_psd['LISA_E'].numpy())
h_c_A = (2.0 * freqs * amp_A)
h_c_E = (2.0 * freqs * amp_E)

# save the characteristic strain psd
np.savetxt(
    f'characteristic_strain/characteristic_strain_{sig_num}_full.txt',
    list(zip(freqs, h_c_A, h_c_E))
)

# map time before merger -> GW frequency using get_inspiral_tf
track_t, track_f = get_inspiral_tf(
    0.0,
    wf['mass1'],
    wf['mass2'],
    wf['spin1z'],
    wf['spin2z'],
    1e-6,
)

for i, days in enumerate(cutoff_days):
    logging.info(f'{days} days before merger')
    t_before = days * 86400

    # Find cut frequency
    f_cut = float(np.interp(-t_before, track_t, track_f))

    # zero out frequencies above f_cut
    mask = freqs > (f_cut + 1e-12)
    h_c_A_tbefore = deepcopy(h_c_A)
    h_c_A_tbefore[mask] = 0
    h_c_E_tbefore = deepcopy(h_c_E)
    h_c_E_tbefore[mask] = 0

    logging.info('Saving A channel')
    np.savetxt(
        f'characteristic_strain/characteristic_strain_{sig_num}_{days}.txt',
        list(zip(freqs, h_c_A_tbefore, h_c_E_tbefore))
    )