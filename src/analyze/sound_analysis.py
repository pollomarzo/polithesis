from brian2 import Hz, kHz, second, Quantity, ms
from brian2hears import Sound, IRCAM_LISTEN
import numpy as np
import matplotlib.pyplot as plt
from utils.log import logger
from sorcery import (
    dict_of,
)

"""
to calculate ITDs, i need to know when a sound starts. this means when it goes from silence (hence background noise) to signal, which is not obvious!
to achieve this, i consider the first _SILENCE_PROFILE_TIME period, and find its maximum value: the signal will then start from the first sound different larger than this one.
this is not a very robust solution, but the easiest one i could think of.
"""
_SILENCE_PROFILE_TIME = 4 * ms


def _first_outside_max_variance(sound: Sound):
    max_variance = np.max(np.abs(np.array(sound[0 * ms : _SILENCE_PROFILE_TIME]))) * 5
    first_idx = np.argmax(abs(sound) > max_variance)
    return [first_idx, np.array(sound)[first_idx], sound.times[first_idx]]


def itd(left: Sound, right: Sound, display=False):
    logger.debug(f"calculating ITD between following sounds...")
    logger.debug(dict_of(left, right))

    left_start_idx, left_start_freq, left_start_time = _first_outside_max_variance(left)
    right_start_idx, right_start_freq, right_start_time = _first_outside_max_variance(
        right
    )
    logger.info(dict_of(left_start_time, right_start_time))
    itd = left_start_time - right_start_time
    logger.info(f"calculated ITD of ${itd}. check graphical output for confirmation.")

    if display:
        plt.subplot(211)
        plotted_range_start = left_start_time - 1 * ms
        plotted_range_end = left_start_time + 3 * ms
        plotted_left = left[plotted_range_start:plotted_range_end]

        plt.plot(plotted_left.times + plotted_range_start, plotted_left, ".-")
        plt.axvline(left_start_time / second, color="red")

        if right_start_time < left_start_time:
            highlight = left[right_start_time:left_start_time]
            plt.plot(highlight.times + right_start_time, highlight, "r.")

        plt.subplot(212)
        plotted_right = right[plotted_range_start:plotted_range_end]

        plt.plot(plotted_right.times + plotted_range_start, plotted_right, ".-")
        plt.axvline(right_start_time / second, color="red")

        if left_start_time < right_start_time:
            highlight = right[left_start_time:right_start_time]
            plt.plot(highlight.times + left_start_time, highlight, "r.")

        plt.show()

    return itd


def spectrum(sound: Sound):
    SAMPLERATE = sound.samplerate
    SOUND_DURATION = sound.duration
    sp = np.abs(np.fft.fft(np.array(sound.flatten()))) ** 2
    freqs = np.abs(
        np.fft.fftfreq(len(sound), SOUND_DURATION / SAMPLERATE * Hz)
    )  # *Hz to make units work
    sp[sp < 1e-20] = 1e-20  # no zeros because we take logs
    sp = 10 * np.log10(sp)
    return (sp, freqs)


def ild(left: Sound, right: Sound, orig: Sound, display=False):
    logger.debug(f"calculating ILD between following sounds...")
    logger.debug(dict_of(left, right))
    if left.samplerate != right.samplerate:
        raise TypeError(
            f"sounds have different samplerate! {left.samplerate} != {right.samplerate}"
        )
    if left.duration != right.duration:
        raise TypeError(
            f"sounds have different duration! {left.duration} != {right.duration}"
        )

    right_sp, right_freq = spectrum(right)
    left_sp, left_freq = spectrum(left)
    orig_sp, orig_freq = spectrum(orig)

    # diff = left_sp - right_sp
    diff = np.max(np.abs(np.array(left))) - np.max(np.abs(np.array(right)))

    if display:
        ymax = max(np.max(left_sp), np.max(right_sp), np.max(orig_sp))
        ylim = (-200, ymax * 1.25)
        fig, axs = plt.subplots(2, 2)
        for plot_n, [sp, freq, title] in enumerate(
            [
                [orig_sp, orig_freq, "orig"],
                [left_sp, left_freq, "left"],
                [diff, left_freq, "diff"],
                [right_sp, right_freq, "right"],
            ]
        ):
            ax = axs[plot_n // 2, plot_n % 2]
            ax.set_title(title)
            ax.set_ylabel("Power (dB/Hz)")
            ax.grid()
            ax.plot(freq, sp)
            plt.setp(ax, ylim=ylim)
        plt.tight_layout()
        # plt.subplots_adjust(hspace=0.6)
        plt.show()
    return (diff, right_freq)
