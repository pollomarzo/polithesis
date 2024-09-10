from brian2 import Hz, kHz, ms
from brian2hears import Sound, IRCAM_LISTEN, dB
from .anf_response import AnfResponse
import numpy as np
from sorcery import dict_of
from utils.log import logger
from consts import Paths
from pathlib import Path
import os
from dataclasses import dataclass
import pickle
from utils.custom_sounds import Tone
from .consts import NUM_CF, IRCAM_HRTF_ANGLES, ANGLES, NUM_ANF_PER_HC
from .RealisticCochlea import (
    sound_to_spikes as real_cochlea,
    COCHLEA_KEY as REAL_COC_KEY,
    memory as CACHE_REAL,
)
from .PpgCochlea import (
    tone_to_ppg_spikes as ppg_cochlea,
    COCHLEA_KEY as PPG_COC_KEY,
    memory as CACHE_PPG,
)
from joblib.memory import MemorizedFunc
from models.InhModel.params import Parameters


# SOUND_DURATION = 1 * second
SOUND_FREQUENCIES = [100 * Hz, 1 * kHz, 10 * kHz]
INFO_FILE_NAME = "info.txt"
INFO_HEADER = "this directory holds all computed angles, for a specific sound, with a specific cochlear backend. the pickled sound is also available. for cochleas that do not use HRTF, left and right sounds are the same. \n"
COCHLEAS = {REAL_COC_KEY: real_cochlea, PPG_COC_KEY: ppg_cochlea}


def create_sound_key(sound: Tone):
    # when we move to non single frequency sounds we can just pass a descriptive string maybe
    if type(sound) is Tone:
        frequency = str(sound.frequency).replace(" ", "")
        sound_type = "tone"
        level = int(sound.sound.level)
    else:
        raise NotImplementedError(f"sound {sound} is not a Tone")
    return f"{sound_type}_{frequency}_{level}dB"


def generate_possible_sounds():
    sounds: dict[str, Sound] = {}
    for freq in SOUND_FREQUENCIES:
        tone = Tone(freq)
        sounds[create_sound_key(tone)] = tone
    # other possible sounds can be added here
    # for type_sound in ['tone', 'click', 'realistic']:...
    return sounds


def load_anf_response(
    tone: Tone,
    angle: int,
    cochlea_key: str,
    params: dict,
    ignore_cache=False,
):
    cochlea_func: MemorizedFunc = COCHLEAS[cochlea_key]
    params = params[cochlea_key]
    if not cochlea_func.check_call_in_cache(tone, angle, params):
        logger.info(f"saved ANF not found. generation will take some time...")
    if ignore_cache:
        logger.info(f"ignoring cache. generation will take some time...")

    logger.info(
        f"generating ANF for {
        dict_of(tone,angle,cochlea_key,params)}"
    )
    if ignore_cache:
        cochlea_func = cochlea_func.call  # forces execution
    try:
        anf = cochlea_func(tone, angle, params)
    except TypeError as e:
        if "unexpected" in e.args[0]:
            logger.error(f"{e}, please check the signature of cochlea")
        raise e

    return anf


def generate_all_ANFs(sounds=None, cochleas=COCHLEAS.keys()):
    if sounds is None:
        sounds = generate_possible_sounds()
    result = {}
    for cochlea in cochleas:
        result[cochlea] = {}
        logger.info(f"generating sound database...")
        logger.debug(
            f"creating directory to keep all possible angles of ANF spiktrains using cochlea {cochlea}"
        )
        for sound_key, sound in sounds.items():
            result[cochlea][sound_key] = {"basesound": sound}
            logger.debug(f"now handling sound {sound_key}...")
            for angle in ANGLES:
                logger.debug(f"working on angle {angle}...")
                anf_response = load_anf_response(sound, angle, cochlea)
                logger.debug(f"generated ANF response...")
                result[cochlea][sound_key][angle] = anf_response

        logger.debug(f"completed sound {sound_key}")
    return result


def spikes_to_nestgen(anf_response: AnfResponse):
    import nest

    nest.set_verbosity("M_ERROR")
    anfs_per_ear = {}
    for channel, response_IHC in anf_response.binaural_anf_spiketrain.items():
        anfs = nest.Create("spike_generator", NUM_CF * NUM_ANF_PER_HC)
        # each hair cell is innervated by NUM_ANF_PER_HC nerve fibers
        for ihf_idx, spike_times in response_IHC.items():
            spike_times = spike_times / ms
            if ihf_idx % 3500 == 0:
                logger.debug(
                    f"current IHF index is {ihf_idx}.\n setting ANF from {NUM_ANF_PER_HC * ihf_idx} to {NUM_ANF_PER_HC * ihf_idx + NUM_ANF_PER_HC} to value (ms) {spike_times}"
                )
            for j in range(
                NUM_ANF_PER_HC * ihf_idx, NUM_ANF_PER_HC * ihf_idx + NUM_ANF_PER_HC
            ):
                nest.SetStatus(
                    anfs[j],
                    params={"spike_times": spike_times, "allow_offgrid_times": True},
                )
        anfs_per_ear[channel] = anfs

    return anfs_per_ear


class CheckThreshold:
    def __init__(self, threshold):
        self.threshold = threshold
        self.above_threshold = None

    def check(self, amount):
        if self.above_threshold == None:
            if amount > self.threshold:
                self.above_threshold = True
            else:
                self.above_threshold = False
        return self.above_threshold
