from brian2 import Hz, kHz
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
)
from .PpgCochlea import tone_to_ppg_spikes as ppg_cochlea, COCHLEA_KEY as PPG_COC_KEY
import nest

nest.set_verbosity("M_ERROR")

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


def load_anf_response(tone: Tone, angle: int, cochlea_key=PPG_COC_KEY):
    filepath = (
        Path(Paths.ANF_SPIKES_DIR)
        / Path(cochlea_key)
        / Path(create_sound_key(tone))
        / Path(f"{create_sound_key(tone)}_{angle}deg.pic")
    )
    if os.path.isfile(filepath):
        with open(filepath, "rb") as f:
            anf: AnfResponse = pickle.load(f)
        return anf
    else:
        logger.info(
            f"saved ANF for {dict_of(tone,angle,cochlea_key)} not found. generating... "
        )
        anf = COCHLEAS[cochlea_key](tone, angle)
        filepath.parent.mkdir(exist_ok=True, parents=True)
        with open(filepath, "wb") as f:
            pickle.dump(anf, f)
        logger.debug(f"anf correctly cached for next execution")
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


# def load_saved_anf_spiketrain(
#     sound_keys: list[str | Tone] | None = None,
# ) -> dict[str, SoundFromAngles]:
#     """
#     {
#         "tone_1Hz": SoundAfterHRTF(
#             basesound: Sound();
#             angle_to_response: {
#                 90: {
#                     SavedIHCResponse: {
#                         binaural_IHC_response: dict:{
#                             L : ...,
#                             R : ...
#                         },
#                         left: Sound
#                         right: Sound
#                     }
#                 },
#                 105: {
#                     SavedIHCResponse: {
#                         binaural_IHC_response: dict:{
#                             L : ...,
#                             R : ...
#                         },
#                         left: Sound
#                         right: Sound
#                     }
#                 },
#             }
#         )
#         ...
#     }
#     """
#     # for every sound_key, you'll get a dictionary of angle->IHC
#     sounds = {}
#     if sound_keys is None:
#         for _, dirs, _ in Path(Paths.ANF_SPIKES_DIR).walk():
#             sound_dirs = dirs
#     else:
#         sound_dirs = sound_keys
#     # build the large dict that will hold all our values
#     for sound in sound_dirs:
#         sound_key, hrtfed_sound = load_spiketrain_all_angles(sound)
#         sounds[sound_key] = hrtfed_sound
#     return sounds


# def load_spiketrain_all_angles(sound: Tone | str):
#     if type(sound) != str:
#         sound_key = create_sound_key(sound)
#     else:
#         sound_key = sound

#     dirpath = Path(Paths.ANF_SPIKES_DIR).joinpath(sound_key)
#     angle_data = {}
#     # unpickle all saved ihc responses (and corresponding sounds)
#     for angle_path in dirpath.glob("*deg.pic"):
#         angle_filename = angle_path.name
#         # get angle string from angle files
#         angle = angle_filename.split("Hz_")[1].split("deg")[0]
#         with open(angle_path, "rb") as f:
#             saved_data: AnfResponse = pickle.load(f)
#         angle_data[angle] = saved_data
#     # unpickle base sound
#     basesound_path = list(dirpath.glob("*basesound.pic"))
#     if len(basesound_path) == 1:
#         with open(basesound_path[0], "rb") as f:
#             basesound = pickle.load((f))
#     return (sound_key, SoundFromAngles(basesound, angle_data))


def spikes_to_nestgen(anf_response: AnfResponse):
    anfs_per_ear = {}
    for channel, response_IHC in anf_response.binaural_anf_spiketrain.items():
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
