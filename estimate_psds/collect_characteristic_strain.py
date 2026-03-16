from pycbc.types import load_frequencyseries
import h5py
import numpy as np
import logging

from pycbc import init_logging

init_logging(1)

signals = range(15)
cutoff_days = [0.5, 1, 4, 7, 14]

hc_all_A = {}
hc_all_E = {}
delta_f = {}
frequencies = {}
for sig_num in signals:
    logging.info('Loading Signal %s', sig_num)

    # save the characteristic strain psd
    logging.info('Loading Full data')
    h_c_full = np.loadtxt(
        f'characteristic_strain/characteristic_strain_{sig_num}_full.txt',
    )

    hc_all_A[sig_num] = {
        0: h_c_full[:,1],
    }
    hc_all_E[sig_num] = {
        0: h_c_full[:,2]
    }

    frequencies = h_c_full[:,0]

    for i, days in enumerate(cutoff_days):
        logging.info('%.1f days before merger', days)

        logging.info('Loading data')
        h_c_tmp = np.loadtxt(
            f'characteristic_strain/characteristic_strain_{sig_num}_{days}.txt',
        )
        hc_all_A[sig_num][days] = h_c_tmp[:,1]
        hc_all_E[sig_num][days] = h_c_tmp[:,2]


logging.info('Writing to collected hdf file')
with h5py.File('characteristic_strain/collected_characteristic_strain.hdf', 'w') as f:
    f.create_dataset(
        'frequencies',
        data=frequencies
    )
    f.attrs['delta_f'] = frequencies[1]
    for signal_number in signals:
        grp = f.create_group(str(signal_number))
        for days in [0] + cutoff_days:
            grp.create_dataset(
                str(days).replace('.','p') + '_A',
                data=hc_all_A[signal_number][days]
            )
            grp.create_dataset(
                str(days).replace('.','p') + '_E',
                data=hc_all_E[signal_number][days]
            )