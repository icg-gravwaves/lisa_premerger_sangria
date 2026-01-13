"""
Common utility functions for LISA pre-merger search.
"""
import numpy as np
import ldc.io.hdf5 as hdfio
from pycbc.types import TimeSeries
from ldc.waveform.lisabeta import FastBHB
from ldc.lisa import orbits
from astropy import units as un

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