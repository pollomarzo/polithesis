from os import makedirs

from brian2 import Inf, SpikeMonitor, clip, ms, plot, run, show
from brian2hears import (
    IRCAM_LISTEN,
    FilterbankGroup,
    FunctionFilterbank,
    Gammatone,
    Sound,
    erbspace,
)
from joblib import Memory
from sorcery import dict_of

from consts import Paths
from utils.custom_sounds import Tone, ToneBurst
from utils.log import logger

from .anf_response import AnfResponse
from .consts import ANGLE_TO_IRCAM, CFMAX, CFMIN, NUM_CF

COCHLEA_KEY = f"gammatone"
CACHE_DIR = Paths.ANF_SPIKES_DIR + COCHLEA_KEY + "/"
makedirs(CACHE_DIR, exist_ok=True)

memory = Memory(location=CACHE_DIR, verbose=0)


def run_hrtf(sound: Sound | Tone | ToneBurst, angle, subj) -> Sound:
    if type(sound) is not Sound:  # assume good faith, ok to fail otherwise
        sound = sound.sound
    # convert to IRCAM angles
    angle = ANGLE_TO_IRCAM[angle]
    # We apply the chosen HRTF to the sound, the output has 2 channels
    hrtfdb = IRCAM_LISTEN(Paths.IRCAM_DIR)
    hrtfset = hrtfdb.load_subject(hrtfdb.subjects[subj])
    hrtf = hrtfset(azim=angle, elev=0)
    binaural_sound: Sound = hrtf(sound)
    return binaural_sound


# plot_spikes won't work much with cache...
@memory.cache
def sound_to_spikes(
    sound: Sound | Tone, angle, params: dict, plot_spikes=False
) -> AnfResponse:
    subj_number = params["subj_number"]
    noise_factor = params["noise_factor"]
    refractory_period = params["refractory_period"] * ms
    amplif_factor = params["amplif_factor"]
    logger.debug(
        f"generating spikes for {dict_of(sound,angle,plot_spikes,subj_number,noise_factor,refractory_period)}"
    )
    binaural_sound = run_hrtf(sound, angle, subj=subj_number)
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    binaural_IHC_response = {}

    logger.info("generating simulated IHC response...")
    for sound, channel in zip([binaural_sound.left, binaural_sound.right], ["L", "R"]):
        # frequencies distributed as cochlea
        # To model how hair cells in adjacent frequencies are engaged as well, but less
        gfb = Gammatone(sound, cf)
        # cochlea modeled as halfwave rectified -> 1/3 power law
        ihc = FunctionFilterbank(
            gfb, lambda x: amplif_factor * clip(x, 0, Inf) ** (1.0 / 3.0)
        )
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
        run(sound.duration)
        if plot_spikes:
            plot(M.t / ms, M.i, ".")
            show()

        binaural_IHC_response[channel] = M.spike_trains()
    logger.info("generation complete.")
    return AnfResponse(binaural_IHC_response, binaural_sound.left, binaural_sound.right)
