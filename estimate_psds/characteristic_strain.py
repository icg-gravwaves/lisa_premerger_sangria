import numpy as np
from copy import deepcopy

from pycbc.pnutils import get_inspiral_tf
from pycbc.waveform import get_fd_det_waveform

import ldc.io.hdf5 as hdfio
from ldc.common import tools as ldc_tools

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../search')))
import common_utils

import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--signal-number', type=int, required=True)
args = parser.parse_args()


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
print(f'Signal {sig_num}')
mbhb = mbhbs[sig_num]
psi, incl = ldc_tools.aziPolAngleL2PsiIncl(
    mbhb["EclipticLatitude"],
    mbhb["EclipticLongitude"],
    mbhb['InitialPolarAngleL'],
    mbhb['InitialAzimuthalAngleL']
)
# Generate the waveform with BBHx
wf = {
    't_obs_start': data_length, # This is setting the data length.
    'f_lower': 1e-6,
    'low-frequency-cutoff': 1e-6, 
    'f_final': 0.1,
    'delta_f': 1 / data_length,
    'tdi': '1.5',
    't_offset': 0,
    'cutoff_deltat': 0,
    'approximant': 'BBHX_PhenomD',
    'mode_array': [(2,2)],
}
# Update waveform params to use the ones from the bank file
wf['tc'] = data_length
wf['mass1'] = mbhb['Mass1']
wf['mass2'] = mbhb['Mass2']
wf['spin1z'] = spin_conv(mbhb['Spin1'],mbhb['PolarAngleOfSpin1'])
wf['spin2z'] = spin_conv(mbhb['Spin2'],mbhb['PolarAngleOfSpin2'])
wf['inclination'] = incl
wf['polarization'] = psi % (2 * np.pi)
wf['eclipticlatitude'] = mbhb['EclipticLatitude']
wf['eclipticlongitude'] = mbhb['EclipticLongitude']
wf['coa_phase'] = mbhb['PhaseAtCoalescence']
wf['distance'] = mbhb['Distance']      

# Generate Waveform
A_sig_psd = get_fd_det_waveform(
    ifos=['LISA_A', 'LISA_E'],
    **wf,
)
A_sig_psd = A_sig_psd['LISA_A']

lisabetawav = common_utils.generate_waveform_for_data(
    mbhb,
    0,
    365*86400,
    5,
)
from pycbc.types import TimeSeries
ts = TimeSeries(lisabetawav['LISA_A'], delta_t=5)
fs_lb_a = ts.to_frequencyseries()
ts = TimeSeries(lisabetawav['LISA_E'], delta_t=5)
fs_lb_e = ts.to_frequencyseries()

# compute characteristic strain from waveform
freqs = A_sig_psd.sample_frequencies.numpy()
amp = np.abs(A_sig_psd.numpy())
h_c = (2.0 * freqs * amp)

# And for LISA B
freqs_lb = fs_lb_a.sample_frequencies.numpy()
amp_lb_a = np.abs(fs_lb_a.numpy())
lb_a = 2 * freqs_lb * amp_lb_a
amp_lb_e = np.abs(fs_lb_e.numpy())
lb_e = 2 * freqs_lb * amp_lb_e

# save the characteristic strain psd
np.savetxt(
    f'characteristic_strain/characteristic_strain_{sig_num}_full.txt',
    list(zip(freqs, h_c))
)

np.savetxt(
    f'characteristic_strain/characteristic_strain_{sig_num}_full_lb.txt',
    list(zip(freqs_lb, lb_a, lb_e)),
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
    print(f'{days} days before merger')
    t_before = days * 86400

    # Find cut frequency
    f_cut = float(np.interp(-t_before, track_t, track_f))

    # zero out frequencies above f_cut
    mask = A_sig_psd.sample_frequencies > (f_cut + 1e-12)
    mask2 = freqs_lb > (f_cut + 1e-12)
    h_c_tbefore = deepcopy(h_c)
    h_c_tbefore[mask] = 0

    lb_a_before = deepcopy(lb_a)
    lb_a_before[mask2] = 0
    lb_e_before = deepcopy(lb_e)
    lb_e_before[mask2] = 0

    # save the characteristic strain psd
    np.savetxt(
        f'characteristic_strain/characteristic_strain_{sig_num}_{days}.txt',
        list(zip(freqs, h_c_tbefore))
    )
    np.savetxt(
        f'characteristic_strain/characteristic_strain_{sig_num}_{days}_lb.txt',
        list(zip(freqs, lb_a_before, lb_e_before)),
    )
