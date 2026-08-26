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

    sm = get_sm(vmin=min(times_before), vmax=max(times_before))
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
    label_two='Removed',
    filter_around_merger=None,
    color_one=None,
    color_two=None,
    legend_loc='upper left',
    marker_one='x',
    marker_two='o',
    width_factor=1,
    height_factor=1,
    alpha_one=1,
    alpha_two=1,
    title=None
):
    width = plt.rcParams["figure.figsize"][0] * width_factor
    height = plt.rcParams["figure.figsize"][1] * height_factor
    fig, ax = plt.subplots(1, figsize=(width, height),)

    max_snr = 0

    max_snr_one, sm_one = calculate_plot_within(
        results_one,
        ax,
        start_time_offset,
        end_time_offset,
        signal_truth_time,
        marker=marker_one,
        times_before=times_before,
        predicted_time=predicted_time,
        filter_around_merger=filter_around_merger,
        color=color_one,
        alpha=alpha_one,
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
            marker=marker_two,
            predicted_time=predicted_time,
            filter_around_merger=filter_around_merger,
            color=color_two,
            zorder=25,
            alpha=alpha_two
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
        lines.append(ax.scatter(
            [],
            [],
            marker=marker_one,
            facecolors='none' if marker_one=='o' else 'k',
            edgecolors='k' if marker_one=='o' else None,
            ),)
        labels.append(label_one)
    if results_two:
        lines.append(ax.scatter(
            [],
            [],
            marker=marker_two,
            facecolors='none' if marker_two=='o' else 'k',
            edgecolors='k' if marker_two=='o' else None,
        ),)
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
    if signal_number is not None and title != 'off':
        ax.set_title(f"Signal {signal_number}: {signal_truth_time/86400:.2f} days")
    return fig, (ax, labels, lines)


def get_sm(vmin, vmax):
    norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)
    return cm.ScalarMappable(
        norm=norm,
        cmap='rainbow'
    )

def get_colors(values=None, vmax=None, vmin=None):
    """
    Get the colors used for plotting
    """
    if vmin is None:
        # Use minimum of values
        vmin = min(values)
    if vmax is None:
        # Use maximum of values
        vmax = max(values)

    sm = get_sm(vmin=vmin, vmax=vmax)

    return {
        value: sm.to_rgba(value)
        for value in values
    }

def plot_optimal_snr_match(
    cutoff_days,
    optimal_snr_data,
    match_cut_results,
    signal_number=None,
    title=None,
):
    min_days = cutoff_days.min()
    max_days = cutoff_days.max()
    premerger_days = match_cut_results.keys()
    premerger_colours = get_colors(values=premerger_days, vmin=0.5, vmax=14)
    width = plt.rcParams["figure.figsize"][0]
    height = plt.rcParams["figure.figsize"][1] * 1.25

    fig, ax = plt.subplots(1, figsize=(width, height),)
    opt_line, = ax.plot(
        cutoff_days,
        optimal_snr_data,
        label='Optimal',
        c='k'
    )
    ax2 = ax.twinx()
    ax2.axhline(1, linestyle=':', c='k', zorder=0)

    lines1 = [opt_line]
    for premerger_day in premerger_days:
        line1, = ax.plot(
            cutoff_days,
            match_cut_results[premerger_day],
            label=f'{premerger_day:.0f} days',
            c=premerger_colours[premerger_day]
        )
        lines1.append(line1)
        ax2.plot(
            cutoff_days,
            match_cut_results[premerger_day] / optimal_snr_data,
            linestyle=':',
            c=premerger_colours[premerger_day],
        )

    ax.semilogy()
    ax.grid()
    ax.set_xlabel('Cutoff time relative to merger (days)')
    ax.set_ylim(bottom=5e-3)

    ax.set_xlim(min_days, max_days)
    ax.set_ylabel('SNR')

    ax2.set_ylim(0,1.05)
    ax2.set_ylabel('Match')
    leg = ax2.legend(handles=lines1, loc='upper left')
    # leg.get_frame().set_alpha(1)
    leg.set_zorder(10)
    line_ff, = ax2.plot([],[],linestyle=':', c='k')
    leg2 = ax2.legend([line_ff], ['Match'], loc='lower right')
    leg2.set_zorder(10)
    # leg2.get_frame().set_alpha(1)
    ax2.add_artist(leg)
    if title != 'off':
        ax.set_title(f'Optimal SNR & Match vs time, Signal {signal_number}')
    return fig, (ax, ax2)


def plot_residual_snr(
    signal_number,
    mbhb,
    data,
    mbhb_data,
    data_residual,
    mbhb_residual,
    residual_data_snrs,
    generated,
    title=True,
    plot_bounds = (-2000, 1000),
    truth_times_s=None,
):
    
    width = plt.rcParams["figure.figsize"][0]
    height = plt.rcParams["figure.figsize"][1] * 1.25
    coalescence_time = mbhb['CoalescenceTime']
    max_residual = 0
    max_data = 0

    times = data['LISA_A'].sample_times - coalescence_time
    within_plot = np.logical_and(
        times >= plot_bounds[0],
        times <= plot_bounds[1]
    )
    
    # Cut the data to only the time around the coalescence
    fig, axes = plt.subplots(
        3,
        sharex='col',
        height_ratios=[3, 1, 1],
        figsize=(width, height),
    )
    ax1, ax2, ax3 = axes
    
    channel_colours = {
        'LISA_A': 'tab:blue',
        'LISA_E': 'tab:orange',
    }
    generated_colours = {
        'LISA_A': 'tab:green',
        'LISA_E': 'tab:red',
    }
    for channel in data.keys():
        channel_str = channel.split('_')[-1]
        max_data = max(max_data, max(abs(data[channel][within_plot])))
        max_residual = max(max_residual, max(abs(data_residual[channel][within_plot])))
        # max_snr = max(max_snr, max(snr[channel][within_plot]))
        mean_data = np.mean(data[channel][within_plot])
        ax1.plot(
            times[within_plot],
            data[channel][within_plot] - mean_data,
            label=f'Data {channel_str}',
            linestyle='-',
            c=channel_colours[channel],
            alpha=0.4
        )
        ax1.plot(
            times[within_plot],
            mbhb_data[channel][within_plot],
            label=f'MBHB {channel_str}',
            linestyle='--',
            c=channel_colours[channel]
        )
        ax1.plot(
            times[within_plot],
            generated[channel][within_plot],
            label=f'Generated {channel_str}',
            linestyle=':',
            c=generated_colours[channel]
        )
        ax2.plot(
            times[within_plot],
            data_residual[channel][within_plot] - mean_data,
            label=f'Data {channel_str}',
            linestyle='-',
            c=channel_colours[channel],
            alpha=0.4
        )
        ax2.plot(
            times[within_plot],
            mbhb_residual[channel][within_plot],
            label=f'MBHB {channel_str}',
            linestyle='--',
            c=generated_colours[channel]
        )
        ax3.plot(
            times[within_plot],
            residual_data_snrs[signal_number][channel],
            label=f'SNR {channel_str}',
            linestyle='-',
            c=channel_colours[channel],
        )
    if truth_times_s is not None:
        for truth_time_s in truth_times_s:
            ax1.axvline((truth_time_s - coalescence_time), zorder=-100, c='tab:pink')
            ax2.axvline((truth_time_s - coalescence_time), zorder=-100, c='tab:pink')
            ax3.axvline((truth_time_s - coalescence_time), zorder=-100, c='tab:pink')
        
    ax2.set_xlim(-2000, 1000)
    ax1.set_ylim(-1.1 * max_data, 1.1 * max_data)
    ax2.set_ylim(-1.1 * max_residual, 1.1 * max_residual)
    ax3.set_ylim(0,10)
    ax1.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    ax2.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    ax3.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    ax1.set_ylabel('Strain')
    ax2.set_ylabel('Residual')
    ax3.set_ylabel('Residual\nSNR')
    ax1.grid()
    ax2.grid()
    ax3.grid()

    if title:
        axes[0].set_title(f'Signal {signal_number}')

    axes[-1].set_xlabel('Time relative to merger, s')

    fig.subplots_adjust(hspace=0.1, right=0.8, top=0.93, bottom=0.08)

    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)

    fig.canvas.draw() 

    for ax in [ax1, ax2]:
        ot = ax.yaxis.get_offset_text()
        offset_str = ot.get_text()
        ot.set_visible(False)
        
        if offset_str:
            ax.text(
                0.02, 0.96, offset_str,
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize='small',
                fontweight='bold',
                # Adding a white background helps if it overlaps data
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0)
            )

    return fig