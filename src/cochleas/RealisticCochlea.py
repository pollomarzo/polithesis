from enum import Enum
from brian2 import clip, Inf, ms, Hz, kHz, plot, show, run, SpikeMonitor
from brian2hears import (
    Sound,
    Gammatone,
    FunctionFilterbank,
    FilterbankGroup,
    erbspace,
    IRCAM_LISTEN,
)
from consts import Paths
from utils.custom_sounds import Tone
from utils.log import logger
from .consts import CFMIN, CFMAX, NUM_CF, ANGLE_TO_IRCAM
from .anf_response import AnfResponse
from dataclasses import dataclass

SUBJECT_N = 2
COCHLEA_KEY = f"realistic_subj{1002 + SUBJECT_N}"


def run_hrtf(sound: Sound | Tone, angle, subj=SUBJECT_N) -> Sound:
    if type(sound) is Tone:
        sound = sound.sound
    # convert to IRCAM angles
    angle = ANGLE_TO_IRCAM[angle]
    # We apply the chosen HRTF to the sound, the output has 2 channels
    hrtfdb = IRCAM_LISTEN(Paths.IRCAM_DIR)
    hrtfset = hrtfdb.load_subject(hrtfdb.subjects[subj])
    hrtf = hrtfset(azim=angle, elev=0)
    binaural_sound: Sound = hrtf(sound)
    return binaural_sound


def sound_to_spikes(sound: Sound | Tone, angle, plot_spikes=False, noise_factor=0.2):
    binaural_sound = run_hrtf(sound, angle)
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    binaural_IHC_response = {}

    logger.info("generating simulated IHC response...")
    for sound, channel in zip([binaural_sound.left, binaural_sound.right], ["L", "R"]):
        # frequencies distributed as cochlea
        # To model how hair cells in adjacent frequencies are engaged as well, but less
        gfb = Gammatone(sound, cf)
        # cochlea modeled as halfwave rectified -> 1/3 power law
        ihc = FunctionFilterbank(gfb, lambda x: 3 * clip(x, 0, Inf) ** (1.0 / 3.0))
        # Leaky integrate-and-fire model with noise and refractoriness
        eqs = f"""
        dv/dt = (I-v)/(1*ms)+{noise_factor}*xi*(2/(1*ms))**.5 : 1 (unless refractory)
        I : 1
        """
        # You can start by thinking of xi as just a Gaussian random variable with mean 0
        # and standard deviation 1. However, it scales in an unusual way with time and this
        # gives it units of 1/sqrt(second)
        G = FilterbankGroup(
            ihc,
            "I",
            eqs,
            reset="v=0",
            threshold="v>1",
            refractory=1 * ms,
            method="euler",
        )
        # Run, and raster plot of the spikes
        M = SpikeMonitor(G)
        run(sound.duration)
        if plot_spikes:
            plot(M.t / ms, M.i, ".")
            show()

        binaural_IHC_response[channel] = M.spike_trains()
    logger.info("generation complete.")
    return AnfResponse(binaural_IHC_response, binaural_sound.left, binaural_sound.right)
