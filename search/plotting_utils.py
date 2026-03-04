import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
from matplotlib import cm 

def calculate_plot_within(
    results,
    ax,
    start_time_offset,
    end_time_offset,
    central_time,
    marker='x',
    times_before=[0.5,1,4,7,14],
    alpha=1,
    predicted_time=True,
    filter_around_merger=None,
    color= None,
    zorder=None
):

    norm = mcolors.LogNorm(vmin=min(times_before), vmax=max(times_before))
    used_in_plot = np.ones_like(results['snr'], dtype=bool)
    # print('Using time' if predicted_time else 'Using data_end_time')
    result_times = results['time'] if predicted_time else results['data_end_time']

    # print(result_times)

    if start_time_offset is not None:
        used_in_plot = np.logical_and(
            used_in_plot,
            ((result_times - central_time) / 86400) >= start_time_offset
        )

    if end_time_offset is not None:
        used_in_plot = np.logical_and(
            used_in_plot,
            ((result_times - central_time) / 86400) <= end_time_offset
        )

    if filter_around_merger is not None:
        used_in_plot = np.logical_and(
            used_in_plot,
            abs(results['time'] - central_time) < filter_around_merger
        )

    if not any(used_in_plot):
        return 0, None

    cmap = cm.get_cmap('rainbow')
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    colors_rgba = sm.to_rgba(results['time_before'][used_in_plot])
    if color is not None:
        colors_rgba = 'k'

    ax.scatter(
        (result_times[used_in_plot] - central_time) / 86400,
        results['snr'][used_in_plot],
        marker=marker,
        facecolors='none' if marker=='o' else colors_rgba,
        edgecolors=colors_rgba if marker=='o' else None,
        alpha=alpha,
        rasterized=True,
        zorder=zorder
    )

    return max(results['snr'][used_in_plot]), sm

def plot_around_time(
    results_one=None,
    results_two=None,
    start_time_offset=20,
    end_time_offset=370,
    signal_truth_time=0,
    signal_number=None,
    truth_times=None,
    times_before=[0.5,1,4,7,14],
    predicted_time=True,
    label_one='Raw',
    label_two='Remove',
    filter_around_merger=None,
    color_one=None,
    color_two=None,
    legend_loc='upper left'
):
    width = plt.rcParams["figure.figsize"][0] * 1.25
    height = plt.rcParams["figure.figsize"][1]
    fig, ax = plt.subplots(1, figsize=(width, height),)

    max_snr = 0

    max_snr_one, sm_one = calculate_plot_within(
        results_one,
        ax,
        start_time_offset,
        end_time_offset,
        signal_truth_time,
        marker='x',
        times_before=times_before,
        predicted_time=predicted_time,
        filter_around_merger=filter_around_merger,
        color=color_one,
        zorder=20
    )
    max_snr = max(max_snr, max_snr_one)

    if results_two:
        max_snr_two, sm_two = calculate_plot_within(
            results_two,
            ax,
            start_time_offset,
            end_time_offset,
            signal_truth_time,
            times_before=times_before,
            marker='o',
            predicted_time=predicted_time,
            filter_around_merger=filter_around_merger,
            color=color_two,
            zorder=25
        )
        max_snr = max(max_snr, max_snr_two)

    if sm_one is None and sm_two is None:
        # No results here
        return fig
    sm = sm_one if sm_one is not None else sm_two
    
    # Add pink lines for when the coalescences are:
    if truth_times is not None:
        for truth_time_s in truth_times:
            ax.axvline(
                (truth_time_s - signal_truth_time) / 86400,
                c='tab:pink',
                zorder=10
            )

    # Add lines for when the data ended (if predicted)
    # when the data predicts (if not)
    if signal_truth_time != 0:
        for time_before in times_before:
            time_to_plot = time_before if predicted_time else -time_before
            ax.axvline(
                time_to_plot,
                c=sm.to_rgba(time_before),
                linestyle=':',
                zorder=15
            )

    label_start = "Forecast Merger Time" if predicted_time else "Data End Time"
    xlab = label_start + " (days)" if signal_truth_time == 0 else label_start + " offset (days)"
    ax.set_xlabel(xlab)
    ax.set_ylabel("SNR")
    cb = fig.colorbar(sm, ax=ax)
    cb.set_ticks(times_before)
    cb.set_ticklabels(times_before)
    cb.set_label('Days Before Merger', rotation=270)

    lines = []
    labels = []
    if results_one:
        lines.append(ax.scatter([], [], marker='x', facecolors='k', edgecolors=None),)
        labels.append(label_one)
    if results_two:
        lines.append(ax.scatter([], [], marker='o', facecolors='none', edgecolors='k'),)
        labels.append(label_two)
    labels.append('Coalescences')
    if truth_times is not None:
        lines.append(ax.axvline(np.nan, c='tab:pink'))

    leg = ax.legend(
        handles=lines, labels=labels, loc=legend_loc,
    )
    leg.set_zorder(50)
    ax.grid(zorder=0)

    if start_time_offset is not None:
        ax.set_xlim(left=start_time_offset)
    if end_time_offset is not None:
        ax.set_xlim(right=end_time_offset)
        
    ax.set_ylim(bottom=4)
    ax.set_ylim(top=max(max_snr * 1.1, 10))
    if signal_number is not None:
        ax.set_title(f"Signal {signal_number}: {signal_truth_time:.1f}s")
    return fig, (ax, labels, lines)