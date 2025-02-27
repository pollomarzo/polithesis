import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from brian2 import Hz, kHz, ms
from brian2hears import IRCAM_LISTEN, Sound, dB, erbspace
from joblib.memory import MemorizedFunc
from sorcery import dict_of
from cochleas.consts import CFMAX, CFMIN
from collections import defaultdict
from bisect import bisect_left


from consts import Paths
from models.InhModel.params import Parameters
from utils.custom_sounds import Click, Tone, ToneBurst, WhiteNoise, Clicks
from utils.log import logger

from .anf_response import AnfResponse
from .consts import ANGLES, IRCAM_HRTF_ANGLES, NUM_ANF_PER_HC, NUM_CF
from .DCGC import COCHLEA_KEY as DCGC_COC_KEY
from .DCGC import sound_to_spikes as DCGC_cochlea
from .GammatoneCochlea import COCHLEA_KEY as GAMMATONE_COC_KEY
from .GammatoneCochlea import memory as CACHE_REAL
from .GammatoneCochlea import sound_to_spikes as gammatone_cochlea
from .PpgCochlea import COCHLEA_KEY as PPG_COC_KEY
from .PpgCochlea import memory as CACHE_PPG
from .PpgCochlea import tone_to_ppg_spikes as ppg_cochlea
from .TanCarneyCochlea import COCHLEA_KEY as TC_COC_KEY
from .TanCarneyCochlea import sound_to_spikes as tc_cochlea

# SOUND_DURATION = 1 * second
SOUND_FREQUENCIES = [100 * Hz, 1 * kHz, 10 * kHz]
INFO_FILE_NAME = "info.txt"
INFO_HEADER = "this directory holds all computed angles, for a specific sound, with a specific cochlear backend. the pickled sound is also available. for cochleas that do not use HRTF, left and right sounds are the same. \n"
COCHLEAS = {
    GAMMATONE_COC_KEY: gammatone_cochlea,
    PPG_COC_KEY: ppg_cochlea,
    TC_COC_KEY: tc_cochlea,
    DCGC_COC_KEY: DCGC_cochlea,
}


def create_sound_key(sound):
    add_info = None
    if type(sound) is Tone:
        add_info = str(sound.frequency).replace(" ", "")
        sound_type = "tone"
        level = int(sound.sound.level)
    elif type(sound) is ToneBurst:
        add_info = str(sound.frequency).replace(" ", "")
        sound_type = "toneburst"
        level = int(sound.sound.level)
    elif type(sound) is WhiteNoise:
        sound_type = "whitenoise"
        level = int(sound.sound.level)
    elif type(sound) is Click:
        sound_type = "click"
        if sound.peak is not None:
            level = sound.peak
        else:
            level = "XX"
    elif type(sound) is Clicks:
        sound_type = "clicks"
        add_info = str(sound.number).replace(" ", "")
        if sound.peak is not None:
            level = sound.peak
        else:
            level = "XX"
    else:
        raise NotImplementedError(f"sound {sound} is not a Tone")
    return f"{sound_type}{f"_{add_info}" if add_info else ""}_{level}dB"


def generate_possible_sounds():
    sounds: dict[str, Sound] = {}
    for freq in SOUND_FREQUENCIES:
        tone = Tone(freq)
        sounds[create_sound_key(tone)] = tone
    # other possible sounds can be added here
    # for type_sound in ['tone', 'click', 'realistic']:...
    return sounds


def load_anf_response(
    sound: Tone | Sound | ToneBurst | Click | Clicks | WhiteNoise,
    angle: int,
    cochlea_key: str,
    params: dict,
    ignore_cache=False,
):
    cochlea_func: MemorizedFunc = COCHLEAS[cochlea_key]
    params = params[cochlea_key]
    if not cochlea_func.check_call_in_cache(sound, angle, params):
        logger.info(f"saved ANF not found. generation will take some time...")
    if ignore_cache:
        logger.info(f"ignoring cache. generation will take some time...")
    logger.info(
        f"generating ANF for {
        dict_of(sound,angle,cochlea_key,params)}"
    )
    if ignore_cache:
        cochlea_func = cochlea_func.call  # forces execution
    try:
        anf = cochlea_func(sound, angle, params)
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
    for channel, response_ANF in anf_response.binaural_anf_spiketrain.items():
        s = []
        # make sure all ANFs have a spiking array and no zero-time spikes are present
        for i in range(NUM_CF * NUM_ANF_PER_HC):
            spiketimes = response_ANF.get(i, [] * ms)
            s.append(spiketimes[spiketimes != 0] / ms)

        anfs = nest.Create(
            "spike_generator",
            NUM_CF * NUM_ANF_PER_HC,
            params={
                "spike_times": s,
                # "spike_times": [i[i != 0] / ms for i in response_ANF.values()],
                "allow_offgrid_times": [True] * NUM_CF * NUM_ANF_PER_HC,
            },
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
    