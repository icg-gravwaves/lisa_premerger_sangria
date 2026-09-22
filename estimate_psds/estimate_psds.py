"""
Estimate PSDs from the LDC Sangria-HM dataset.

The estimated and smoothed PSDs are written out as .txt files which are then loaded
by `plot_psds.ipynb` (and by the search notebooks) for plotting only.
"""
import argparse
import logging
import os
from copy import deepcopy

import numpy as np
from scipy.signal import windows

from pycbc.types import TimeSeries, FrequencySeries
from pycbc.psd import interpolate
from pycbc import add_common_pycbc_options, init_logging

import ldc.io.hdf5 as hdfio
import ldc.lisa.noise.noise as ldc_noise


def smooth_section(
    psd_freqseries,
    start_frequency,
    end_frequency,
    model_y,
    model_freqs,
    psd_frequencies=None,
):
    """Bridge a frequency section of a PSD with a log-log straight line.

    The line is anchored at the actual sample frequencies in `model_freqs`
    that are nearest to `start_frequency` and `end_frequency`, so the slope
    and intercept are computed from real (positive) values rather than from
    an index that could land on 0 Hz.
    """
    if isinstance(psd_freqseries, FrequencySeries):
        psd_frequencies = np.asarray(psd_freqseries.sample_frequencies)
    elif psd_frequencies is None:
        raise ValueError('psd_frequencies must be provided when psd_freqseries is not a FrequencySeries')
    else:
        psd_frequencies = np.asarray(psd_frequencies)

    model_freqs = np.asarray(model_freqs)

    # Find the actual sample frequencies nearest to the requested bounds.
    start_idx_model = int(np.argmin(np.abs(model_freqs - start_frequency)))
    end_idx_model = int(np.argmin(np.abs(model_freqs - end_frequency)))
    start_x = model_freqs[start_idx_model]
    start_y = model_y[start_idx_model]
    end_x = model_freqs[end_idx_model]
    end_y = model_y[end_idx_model]

    if start_x <= 0 or end_x <= 0:
        raise ValueError(
            'Anchoring frequencies must be positive, got start_x=%r, end_x=%r' % (start_x, end_x)
        )

    slope = (np.log(end_y) - np.log(start_y)) / (np.log(end_x) - np.log(start_x))
    intercept = np.log(start_y) - slope * np.log(start_x)

    smoothed_section_psd = np.logical_and(
        psd_frequencies >= start_frequency,
        psd_frequencies <= end_frequency
    )
    smoothed_freqs = psd_frequencies[smoothed_section_psd]
    smoothed_y = psd_freqseries[smoothed_section_psd]

    # Get the line at the frequencies in the PSD
    line_out = np.exp(intercept) * (smoothed_freqs ** slope)

    # use a window function to combine the line and the PSD
    N = smoothed_freqs.size
    window = windows.hann(N)
    windowed_line = line_out * window
    windowed_psd = smoothed_y * (1 - window)
    fuzzy_line = windowed_line + windowed_psd

    if isinstance(psd_freqseries, FrequencySeries):
        psd_out = deepcopy(psd_freqseries.data)
    else:
        psd_out = np.array(psd_freqseries, copy=True)
    psd_out[smoothed_section_psd] = fuzzy_line

    return psd_out, fuzzy_line, line_out


def to_aet(X, Y, Z, delta_t):
    """Convert X/Y/Z TDI channels into A/E/T float32 TimeSeries.

    """
    A = ((Z - X) / np.sqrt(2.0)).astype(np.float32)
    E = ((X - 2.0 * Y + Z) / np.sqrt(6.0)).astype(np.float32)
    T = ((X + Y + Z) / np.sqrt(3.0)).astype(np.float32)
    return (
        TimeSeries(A, delta_t=delta_t),
        TimeSeries(E, delta_t=delta_t),
        TimeSeries(T, delta_t=delta_t),
    )


def estimate_channel_psd(ts, segment_duration):
    """Welch PSD for a channel, interpolated onto the full-data frequency grid."""
    psd = ts.psd(segment_duration)
    return interpolate(psd, ts.delta_f)


def main():
    parser = argparse.ArgumentParser(
        description='Estimate and smooth PSDs from the Sangria-HM dataset.'
    )
    parser.add_argument(
        '--input-data',
        default='../datasets/LDC2_sangria_hm_training.hdf',
        help='Path to the Sangria-HM hdf file',
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory in which to write the estimated / model PSD .txt files',
    )
    parser.add_argument(
        '--segment-duration',
        type=float,
        default=1576800.0,
        help='Segment duration (s) used for the Welch PSD estimate',
    )
    parser.add_argument(
        '--delta-t',
        type=float,
        default=5.0,
        help='Sampling rate of the dataset (s)',
    )
    parser.add_argument(
        '--smooth-lower',
        type=float,
        default=3e-2,
        help='Lower edge of the galactic-binary dip to smooth over (Hz)',
    )
    parser.add_argument(
        '--smooth-upper',
        type=float,
        default=9e-2,
        help='Upper edge of the galactic-binary dip to smooth over (Hz)',
    )
    add_common_pycbc_options(parser)
    args = parser.parse_args()

    if args.verbose is None:
        init_logging(1)
    else:
        init_logging(args.verbose + 1)

    os.makedirs(args.output_dir, exist_ok=True)

    input_data = args.input_data
    segment_duration = args.segment_duration
    delta_t = args.delta_t
    section_lower = args.smooth_lower
    section_upper = args.smooth_upper

    estimated_format = '{channel}_sangria_hm_PSD.txt'
    smoothed_output_format = '{channel}_sangria_hm_SMOOTHED_PSD.txt'
    model_nogb_output_format = 'model_{channel}_NOGB_PSD.txt'
    model_output_format = 'model_{channel}_PSD.txt'

    logging.info('Loading observed TDI from %s', input_data)
    tdi_ts, _ = hdfio.load_array(input_data, name="obs/tdi")
    X, Y, Z = tdi_ts['X'], tdi_ts['Y'], tdi_ts['Z']

    A_ts, E_ts, T_ts = to_aet(X, Y, Z, delta_t)
    # We no longer need the raw X/Y/Z arrays.
    del X, Y, Z, tdi_ts


    logging.info('Estimating channel PSDs (segment duration %.0f s)', segment_duration)
    A_psd = estimate_channel_psd(A_ts, segment_duration)
    E_psd = estimate_channel_psd(E_ts, segment_duration)
    T_psd = estimate_channel_psd(T_ts, segment_duration)

    # Save the raw (unsmoothed) estimates for later plotting.
    logging.info('Saving estimated PSDs')
    A_psd.save(os.path.join(args.output_dir, estimated_format.format(channel='A')))
    E_psd.save(os.path.join(args.output_dir, estimated_format.format(channel='E')))
    T_psd.save(os.path.join(args.output_dir, estimated_format.format(channel='T')))

    logging.info('Building noise-only residual by removing all signal types')
    residual_A = deepcopy(A_ts)
    residual_E = deepcopy(E_ts)

    signal_types = ['mbhb', 'vgb', 'dgb', 'igb']
    for signal_type in signal_types:
        logging.info('Removing %s contribution', signal_type)
        sig_tdi, _ = hdfio.load_array(input_data, name=f'/sky/{signal_type}/tdi')
        A_sig = ((sig_tdi['Z'] - sig_tdi['X']) / np.sqrt(2.0)).astype(np.float32)
        E_sig = ((sig_tdi['X'] - 2.0 * sig_tdi['Y'] + sig_tdi['Z']) / np.sqrt(6.0)).astype(np.float32)

        residual_A.data -= A_sig
        residual_E.data -= E_sig

        del A_sig, E_sig, sig_tdi

    logging.info('Estimating residual (noise-only) PSDs')
    residual_A_psd = estimate_channel_psd(residual_A, segment_duration)
    residual_E_psd = estimate_channel_psd(residual_E, segment_duration)

    logging.info('Saving residual (noise-only) PSDs')
    residual_A_psd.save(os.path.join(args.output_dir, 'residual_A_sangria_hm_PSD.txt'))
    residual_E_psd.save(os.path.join(args.output_dir, 'residual_E_sangria_hm_PSD.txt'))

    # The raw residuals are no longer needed once the PSDs are computed.
    del residual_A, residual_E

    logging.info('Loading Sangria noise model')
    sangria_model_freqs = A_psd.sample_frequencies

    nm_withgb = ldc_noise.get_noise_model("sangria", sangria_model_freqs, wd=True)
    sangria_model_ae_withgb = nm_withgb.psd(option="A")
    sangria_model_t_withgb = nm_withgb.psd(option="T")

    nm_nogb = ldc_noise.get_noise_model("sangria", sangria_model_freqs, wd=False)
    sangria_model_ae_nogb = nm_nogb.psd(option="A")
    sangria_model_t_nogb = nm_nogb.psd(option="T")


    logging.info("Saving Model PSDs")

    sangria_model_ae_withgb[0] = 0
    sangria_model_t_withgb[0] = 0
    np.savetxt(
        os.path.join(args.output_dir, model_output_format.format(channel='AE')),
        np.array([sangria_model_freqs, sangria_model_ae_withgb]).T,
    )

    np.savetxt(
        os.path.join(args.output_dir, model_output_format.format(channel='T')),
        np.array([sangria_model_freqs, sangria_model_t_withgb]).T,
    )


    logging.info("Saving no-GB PSDs")

    sangria_model_ae_nogb[0] = 0
    sangria_model_t_nogb[0] = 0
    np.savetxt(
        os.path.join(args.output_dir, model_nogb_output_format.format(channel='AE')),
        np.array([sangria_model_freqs, sangria_model_ae_nogb]).T,
    )

    np.savetxt(
        os.path.join(args.output_dir, model_nogb_output_format.format(channel='T')),
        np.array([sangria_model_freqs, sangria_model_t_nogb]).T,
    )


    logging.info('Smoothing the TDI dip between %.1e and %.1e Hz',
                 section_lower, section_upper)
    A_psd_smoothed, _, _ = smooth_section(
        A_psd, section_lower, section_upper,
        sangria_model_ae_withgb, sangria_model_freqs,
    )
    E_psd_smoothed, _, _ = smooth_section(
        E_psd, section_lower, section_upper,
        sangria_model_ae_withgb, sangria_model_freqs,
    )
    modelled_psd_smoothed, _, _ = smooth_section(
        sangria_model_ae_withgb, section_lower, section_upper,
        sangria_model_ae_withgb, sangria_model_freqs,
        psd_frequencies=sangria_model_freqs,
    )

    # Remove the zero-frequency NaN before saving.
    A_psd_smoothed[0] = 0
    E_psd_smoothed[0] = 0
    modelled_psd_smoothed[0] = 0


    logging.info('Saving smoothed and model PSDs')
    np.savetxt(
        os.path.join(args.output_dir, smoothed_output_format.format(channel='A')),
        np.array([sangria_model_freqs, A_psd_smoothed]).T,
    )
    np.savetxt(
        os.path.join(args.output_dir, smoothed_output_format.format(channel='E')),
        np.array([sangria_model_freqs, E_psd_smoothed]).T,
    )
    np.savetxt(
        os.path.join(args.output_dir, 'model_AE_SMOOTHED_PSD.txt'),
        np.array([sangria_model_freqs, modelled_psd_smoothed]).T,
    )

    logging.info('Done. PSD files written to %s', args.output_dir)


if __name__ == '__main__':
    main()

