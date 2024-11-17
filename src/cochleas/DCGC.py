from os import makedirs

import numpy as np
from brian2 import Hz, Inf, SpikeMonitor, clip, kHz, ms, plot, run, show
from brian2hears import (
    DCGC,
    FilterbankGroup,
    FunctionFilterbank,
    MiddleEar,
    RestructureFilterbank,
    Sound,
    ZhangSynapse,
    erbspace,
)
from joblib import Memory
from scipy import signal
from sorcery import dict_of

from consts import Paths
from utils.custom_sounds import Tone, ToneBurst
from utils.log import logger, tqdm

from .anf_response import AnfResponse
from .consts import CFMAX, CFMIN, NUM_ANF_PER_HC, NUM_CF
from .GammatoneCochlea import run_hrtf

COCHLEA_KEY = f"DCGC"
CACHE_DIR = Paths.ANF_SPIKES_DIR + COCHLEA_KEY + "/"
makedirs(CACHE_DIR, exist_ok=True)

memory = Memory(location=CACHE_DIR, verbose=0)


@memory.cache
def sound_to_spikes(
    sound: Sound | Tone | ToneBurst, angle, params: dict, plot_spikes=False
) -> AnfResponse:
    subj_number = params["subj_number"]
    noise_factor = params["noise_factor"]
    refractory_period = params["refractory_period"] * ms
    amplif_factor = params["amplif_factor"]
    coch_par = params.get("cochlea_params", None)
    logger.debug(
        f"genenerating spikes for {dict_of(sound,angle,plot_spikes,subj_number)}"
    )
    binaural_sound = run_hrtf(sound, angle, subj=subj_number)
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    binaural_IHC_response = {}

    logger.info("generating simulated IHC response...")

    for sound, channel in zip([binaural_sound.left, binaural_sound.right], ["L", "R"]):
        logger.debug(f"working on ear {channel}...")
        if amplif_factor == "realistic":
            ampl = MiddleEar(sound)
        else:
            ampl = FunctionFilterbank(sound, lambda x: amplif_factor * x)
        ihc = RestructureFilterbank(DCGC(ampl, cf, param=coch_par), NUM_ANF_PER_HC)
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
            refractory=refractory_period,
            method="euler",
        )
        # Run, and raster plot of the spikes
        M = SpikeMonitor(G)
        for chunk in tqdm(range(10), desc="IHCsim"):
            run(sound.duration / 10)

        if plot_spikes:
            plot(M.t / ms, M.i, ".")
            show()

        binaural_IHC_response[channel] = M.spike_trains()
    logger.info("generation complete.")
    return AnfResponse(binaural_IHC_response, binaural_sound.left, binaural_sound.right)
