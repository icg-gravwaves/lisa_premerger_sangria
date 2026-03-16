from pycbc.types import load_frequencyseries
import numpy as np
import h5py

signals = range(15)
cutoff_days = [0.5, 1, 4, 7, 14]

hc_all = {}
hc_all_lba = {}
hc_all_lbe = {}
for sig_num in signals:
    print(f'Signal {sig_num}')

    # save the characteristic strain psd
    h_c_fs = load_frequencyseries(
        f'characteristic_strain/characteristic_strain_{sig_num}_full.txt',
    )
    h_c = h_c_fs.data
    freqs = h_c_fs.sample_frequencies

    hc_all[sig_num] = {
        0: h_c
    }

    h_c_fs_lb = np.loadtxt(
        f'characteristic_strain/characteristic_strain_{sig_num}_full_lb.txt'
    )
    freqs_lb = h_c_fs_lb[:,0]

    hc_all_lba[sig_num] = {
        0: h_c_fs_lb[:,1]
    }

    hc_all_lbe[sig_num] = {
        0: h_c_fs_lb[:,2]
    }

    for i, days in enumerate(cutoff_days):
        print(f'{days} days before merger')

        hc_all[sig_num][days] = load_frequencyseries(
            f'characteristic_strain/characteristic_strain_{sig_num}_{days}.txt',
        )

        lb_tmp = np.loadtxt(
            f'characteristic_strain/characteristic_strain_{sig_num}_{days}_lb.txt',
        )
        hc_all_lba[sig_num][days] = lb_tmp[:,1]
        hc_all_lbe[sig_num][days] = lb_tmp[:,2]

with h5py.File('characteristic_strain/collected_characteristic_strain.hdf', 'w') as f:
    f.create_dataset(
        'frequencies',
        data=hc_all[0][0.5].sample_frequencies
    )
    f.attrs['delta_f'] = h_c_fs.delta_f
    for signal_number in signals:
        grp = f.create_group(str(signal_number))
        for days in [0] + cutoff_days:
            grp.create_dataset(
                str(days).replace('.','p'),
                data=hc_all[signal_number][days].data
            )

with h5py.File('characteristic_strain/collected_characteristic_strain_lb.hdf', 'w') as f:
    f.create_dataset(
        'frequencies',
        data=freqs_lb
    )
    f.attrs['delta_f'] = freqs_lb[1]
    for signal_number in signals:
        grp = f.create_group(str(signal_number))
        for days in [0] + cutoff_days:
            grp.create_dataset(
                str(days).replace('.','p') + 'A',
                data=hc_all_lba[signal_number][days]
            )
            grp.create_dataset(
                str(days).replace('.','p') + 'E',
                data=hc_all_lbe[signal_number][days]
            )
