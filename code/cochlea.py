from enum import Enum
from brian2 import *
from brian2hears import *
import numpy as np
import pickle
from consts import Paths as P
import nest

NUM_CF = 3500  # 3500 (3.5k cochlea ciliar -> 10 ANF for each -> 35000 ANF)
# of course, if you change this, you need to regenerate all created files
NUM_ANF_PER_HC = 10
CFMIN = 20 * Hz
CFMAX = 20 * kHz


def sounds_to_IHC(binaural_sound, plot_spikes=False, save_to_file=False, filepath=None):
    if save_to_file and filepath is None:
        raise Exception("Cannot save result to file with no filename.")
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    binaural_IHC_response = {}

    logger.info("generating simulated IHC response...")
    for sound_arr, channel in zip(binaural_sound, ["L", "R"]):
        sound = Sound(sound_arr)
        # frequencies distributed as cochlea
        # To model how hair cells in adjacent frequencies are engaged as well, but less
        gfb = Gammatone(sound, cf)
        # cochlea modeled as halfwave rectified -> 1/3 power law
        ihc = FunctionFilterbank(gfb, lambda x: 3 * clip(x, 0, Inf) ** (1.0 / 3.0))
        # Leaky integrate-and-fire model with noise and refractoriness
        eqs = """
        dv/dt = (I-v)/(1*ms)+0.2*xi*(2/(1*ms))**.5 : 1 (unless refractory)
        I : 1
        """
        G = FilterbankGroup(
            ihc, "I", eqs, reset="v=0", threshold="v>1", refractory=5 * ms
        )
        # Run, and raster plot of the spikes
        M = SpikeMonitor(G)
        run(sound.duration)
        if plot_spikes:
            plot(M.t / ms, M.i, ".")
            show()

        binaural_IHC_response[channel] = M.spike_trains()
    logger.info("generation complete.")

    if save_to_file:
        logger.info(f"saving result to {filepath}")
        with open(filepath, "wb") as f:
            pickle.dump(binaural_IHC_response, f)
    return binaural_IHC_response


def IHC_to_ANF(binaural_IHC_response=None, filepath=None):
    if binaural_IHC_response is None and filepath is None:
        raise Exception("'IHC_response' and 'filepath' cannot both be None")

    anfs_per_ear = {}
    if binaural_IHC_response is None:
        logger.info("loading spikes from file at " + filepath)
        with open(filepath, "rb") as f:
            binaural_IHC_response = pickle.load(f)

    for channel, response_IHC in binaural_IHC_response.items():
        anfs = nest.Create("spike_generator", NUM_CF * NUM_ANF_PER_HC)
        # each hair cell is innervated by NUM_ANF_PER_HC nerve fibers
        for ihf_idx, spike_times in response_IHC.items():
            for j in range(
                NUM_ANF_PER_HC * ihf_idx, NUM_ANF_PER_HC * ihf_idx + NUM_ANF_PER_HC
            ):
                nest.SetStatus(
                    anfs[j],
                    params={"spike_times": spike_times, "allow_offgrid_times": True},
                )
        anfs_per_ear[channel] = anfs

    return anfs_per_ear
