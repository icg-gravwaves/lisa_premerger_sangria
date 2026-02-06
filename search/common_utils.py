"""
Common utility functions for LISA pre-merger search.
"""
import numpy as np
import ldc.io.hdf5 as hdfio
from pycbc.types import TimeSeries
from ldc.waveform.lisabeta import FastBHB
from ldc.lisa import orbits
from astropy import units as un
import logging
import copy

from matplotlib import pyplot as plt


lisa_orbits = orbits.Orbits.type(dict({"nominal_arm_length":2.5e9*un.m,
                                       "initial_rotation":0*un.rad,
                                       "initial_position":0*un.rad,
                                       "orbit_type":"analytic"}))

def to_timeseries(waveform_dict, delta_t, epoch=0):
    return_dict = {}
    for channel, array in waveform_dict.items():
        array_ts = TimeSeries(array, delta_t=delta_t, epoch=epoch)
        return_dict[channel] = array_ts
    return return_dict

def AET(X,Y,Z, delta_t, epoch=0):
    waveform_A = (Z - X)/np.sqrt(2.0)
    waveform_E = (X - 2.0*Y + Z)/np.sqrt(6.0)
    waveform_T =(X + Y + Z)/np.sqrt(3.0)

    AET_ts = to_timeseries(
        {
            'LISA_A': waveform_A,
            'LISA_E': waveform_E,
            'LISA_T': waveform_T,
        },
        delta_t,
        epoch=epoch
    )

    return AET_ts

def load_ldc_timeseries(
    filename,
    data_group="obs/tdi",
    remove_noiseless_groups=[],
    delta_t=5.
):
    tdi_ts, _ = hdfio.load_array(filename, name=data_group)
    X = tdi_ts['X']
    Y = tdi_ts['Y']
    Z = tdi_ts['Z']

    for ng in remove_noiseless_groups:
        tdi_to_rm, _ = hdfio.load_array(filename, name=ng)
        X -= tdi_to_rm['X']
        Y -= tdi_to_rm['Y']
        Z -= tdi_to_rm['Z']

    return AET(X,Y,Z, delta_t)

def fast_tdi(lisa_orbits, mbhb, start_time, end_time, dt):

    fast_hm = FastBHB(
        "MBHB",
        approx="IMRPhenomHM",
        T=end_time,
        delta_t=dt,
        orbits=lisa_orbits,
        modes=[(2,2), (2,1), (3,3), (3,2), (4,4), (4,3)]
    )
    
    A, E, T = fast_hm.get_td_tdiaet(
        template=mbhb,
        tdi2=False
    )

    # Cut to the start/end time as appropriate
    start_idx = int(start_time / dt)
    end_idx = int(end_time / dt)

    return to_timeseries(
        {
            'LISA_A': A[start_idx:end_idx],
            'LISA_E': E[start_idx:end_idx],
            'LISA_T': T[start_idx:end_idx],
        },
        dt,
        epoch=start_time
    )

def generate_waveform_for_data(
    mbhb,
    start_time,
    end_time,
    delta_t,
):
    wave = dict(zip(mbhb.dtype.names, mbhb)) 
    wave['Cadence'] = delta_t
    return fast_tdi(
        lisa_orbits,
        wave,
        start_time,
        end_time,
        delta_t
    )

def plot_removed_waveforms(
    waveform_for_removal,
    data,
    mbhb_data,
    data_residual,
    mbhb_residual,
    coalescence_time,
    plot_file,
    plot_start_offset=86400*12,
    plot_end_offset=86400,
    mbhb_times = None
):

    plot_entirely_within_data = True

    plot_start_time = coalescence_time - plot_start_offset
    plot_end_time = coalescence_time + plot_end_offset

    eg_channel = list(data.keys())[0]
    data_start_time = data[eg_channel]._epoch
    data_end_time = data_start_time + data[eg_channel].delta_t * len(data[eg_channel])

    if data_end_time < plot_end_time:
        # data finishes before the end of the plot
        plot_entirely_within_data = False
    elif data_start_time > plot_start_time:
        # data starts after the start of the plot
        plot_entirely_within_data = False
    

    if not plot_entirely_within_data:
        logging.info('Plot time is not fully contained by the data')
        return
    
    logging.info('Plotting waveform and data before and after removal')

    logging.debug('Calculating valid datapoints')

    plot_start_idx = float(plot_start_time - data_start_time) // data[eg_channel].delta_t
    plot_end_idx = float(plot_end_time - data_start_time) // data[eg_channel].delta_t
    valid = slice(int(plot_start_idx), int(plot_end_idx))

    fig1, axes = plt.subplots(
        2, 2,
        figsize=(12,4),
        height_ratios=[3,1],
        sharex='col',
        sharey='row',
    )

    (ax1, ax3), (ax2, ax4) = axes
    channel_colours = {
        'LISA_A': 'tab:blue',
        'LISA_E': 'tab:orange',
    }
    max_residual = 0
    max_data = 0
    for channel_name in ['LISA_A', 'LISA_E']:
        channel_data = data[channel_name][valid]
        max_data = max(max_data, max(abs(channel_data)))
        subtraction_residual = mbhb_residual[channel_name][valid]
        max_residual = max(max_residual, max(abs(subtraction_residual)))
        for ax in ax1, ax3 :
            ax.plot(
                (channel_data.sample_times - coalescence_time) / 86400,
                channel_data,
                label=f'Data {channel_name}',
                c=channel_colours[channel_name],
                alpha=0.25
            )
            ax.plot(
                (mbhb_data[channel_name].sample_times[valid] - coalescence_time) / 86400,
                mbhb_data[channel_name][valid],
                c=channel_colours[channel_name],
                label=f'MBHB {channel_name}',
            )
            ax.plot(
                (waveform_for_removal[channel_name].sample_times[valid] - coalescence_time) / 86400,
                waveform_for_removal[channel_name][valid],
                c=channel_colours[channel_name],
                linestyle=':',
                label=f'Waveform {channel_name}'
            )
        for ax in ax2, ax4:
            ax.plot(
                (waveform_for_removal[channel_name].sample_times[valid] - coalescence_time) / 86400,
                subtraction_residual,
                c=channel_colours[channel_name],
            )

            ax.plot(
                (data_residual[channel_name].sample_times[valid] - coalescence_time) / 86400,
                data_residual[channel_name][valid],
                c=channel_colours[channel_name],
                alpha=0.2
            )

    # If no residuals, add a bit so that we can see a flat line within the noise
    if max_residual == 0:
        max_residual = 1e-20
    # Expand the ylims a bit around the data
    max_data = max(max_data, 5e-20)

    # Add vertical lines to show when the merger is
    for ax in ax1, ax2, ax3, ax4:
        ax.axvline(0, c='black', linestyle='--', zorder=-30)
        if mbhb_times is not None:
            for other_time in mbhb_times:
                ax.axvline(
                    (other_time - coalescence_time) / 86400,
                    c='tab:pink',
                    linestyle='--',
                    zorder=-35
                )

        ax.grid()

    # Zoom into the merger
    ax4.set_xlim(-plot_start_offset/86400, plot_end_offset/86400)
    ax2.set_xlim(-2000/86400, 1000/86400)

    # Dynamic y limits according the the signal/data range
    ax1.set_ylim(-max_data*1.1, max_data*1.1)
    ax2.set_ylim(-max_residual*1.1, max_residual*1.1)

    ax3.legend(loc='upper left')

    ax1.set_ylabel('Strain')
    ax2.set_ylabel('Residual')
    
    ax2.set_xlabel('Time relative to merger (zoomed, days)')
    ax4.set_xlabel('Time relative to merger (days)')

    fig1.savefig(plot_file)
    plt.close(fig1)

def remove_signals(
    data,
    mbhb_catalog,
    mbhb_data,
    data_end_time,
    data_start_time,
    relative_time_for_removal=[0],
    delta_t=5.,
    testing_plots=None,
):
    eg_channel = list(data.keys())[0]
    n_catalog = len(mbhb_catalog)
    if len(relative_time_for_removal) == 1:
        # if one value is provided, broadcast to all in the catalog
        offsets = relative_time_for_removal * n_catalog
    elif len(relative_time_for_removal) != n_catalog:
        raise RuntimeError(
            'Must provide singular value for relative times of removal, or use a '
        )
    else:
        offsets = relative_time_for_removal

    data_length_s = len(data[eg_channel]) * delta_t

    for i, (mbhb, offset) in enumerate(zip(mbhb_catalog, offsets)):
        coalescence_time = mbhb['CoalescenceTime']

        if (data_end_time) < (coalescence_time + offset):
            logging.info("Signal %d at %.0f not yet reached", i, coalescence_time)
            continue

        if coalescence_time < (data_start_time - data_length_s * 2):
            logging.info("Signal %d at %.0f is well before the searched time - ignore it", i, coalescence_time)
            continue
    
        logging.info("Removing signal %d at %.0f from data", i, coalescence_time)

        waveform_for_removal = generate_waveform_for_data(
            mbhb,
            data_start_time,
            data_end_time,
            delta_t,
        )

        logging.info('Removing from data')
        subtracted = {
            channel: data[channel] - waveform_for_removal[channel]
            for channel in data.keys()
        }
        subtracted_mbhb = {
            channel: mbhb_data[channel] - waveform_for_removal[channel]
            for channel in data.keys()
        }

        logging.info(
            "Waveform removed is close to MBHB data?: A channel: %s, E channel: %s ",
            np.isclose(waveform_for_removal['LISA_A'], mbhb_data['LISA_A'], rtol=1e-3).all(),
            np.isclose(waveform_for_removal['LISA_E'], mbhb_data['LISA_E'], rtol=1e-3).all()
        )

        if testing_plots is not None:
            plot_removed_waveforms(
                waveform_for_removal,
                data,
                mbhb_data,
                subtracted,
                subtracted_mbhb,
                coalescence_time=coalescence_time,
                mbhb_times=mbhb_catalog['CoalescenceTime'],
                plot_file=f"{testing_plots}/waveform_for_removal_{i}.png",
            )

        data = subtracted
        mbhb_data = subtracted_mbhb