from os import makedirs

from brian2 import (
    Hz,
    Inf,
    SpikeMonitor,
    clip,
    flipud,
    imshow,
    kHz,
    ms,
    plot,
    run,
    second,
    show,
)
from brian2hears import (
    DCGC,
    DRNL,
    IRCAM_LISTEN,
    FilterbankGroup,
    FunctionFilterbank,
    Gammatone,
    MiddleEar,
    Sound,
    TanCarney,
    ZhangSynapse,
    dB,
    erbspace,
    set_default_samplerate,
)
from joblib import Memory
from sorcery import dict_of

from consts import Paths
from utils.custom_sounds import Tone
from utils.log import logger, tqdm

from .anf_response import AnfResponse
from .consts import ANGLE_TO_IRCAM, CFMAX, CFMIN, NUM_CF
from .RealisticCochlea import run_hrtf

COCHLEA_KEY = f"DRNL"
CACHE_DIR = Paths.ANF_SPIKES_DIR + COCHLEA_KEY + "/"
makedirs(CACHE_DIR, exist_ok=True)

memory = Memory(location=CACHE_DIR, verbose=0)

# set_default_samplerate(50 * kHz)


# plot_spikes won't work much with cache...
@memory.cache
def sound_to_spikes(
    sound: Sound | Tone, angle, params: dict, plot_spikes=False
) -> AnfResponse:
    subj_number = params["subj_number"]
    noise_factor = params["noise_factor"]
    # noise_factor = 0
    refractory_period = params["refractory_period"] * ms
    logger.debug(
        f"genenerating spikes for {dict_of(sound,angle,plot_spikes,subj_number)}"
    )
    binaural_sound = run_hrtf(sound, angle, subj=subj_number)
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    binaural_IHC_response = {}

    logger.info("generating simulated IHC response...")
    cochleas = {
        "DRNL": [DRNL, {"lp_nl_cutoff_m": 1.1}],
        "DCGC": [DCGC, {"c1": -2.96}],
        "TanCarney": [TanCarney, None],
    }

    # sound = Sound.tone(100 * Hz, duration=1 * second).atlevel(30 * dB)
    for sound, channel in zip([binaural_sound.left, binaural_sound.right], ["L", "R"]):
        logger.debug(f"working on ear {channel}...")
        # for sound, channel in zip([sound], ["L"]):
        # frequencies distributed as cochlea
        # gfb = Gammatone(sound, cf)
        # logger.debug(gfb.samplerate)
        # mdd = MiddleEar(sound)
        # ihc = TanCarney(mdd, cf)
        # logger.debug("TanCarney initialized")
        # G = ZhangSynapse(ihc, cf)
        ihc = DCGC(sound, cf, param={"c1": -2.96})
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
    # return AnfResponse(binaural_IHC_response, binaural_sound.left, binaural_sound.right)
    return AnfResponse(binaural_IHC_response, sound, sound)
