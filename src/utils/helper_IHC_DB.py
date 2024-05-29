from brian2 import Hz, kHz, second, Quantity
from brian2hears import Sound, IRCAM_LISTEN
import numpy as np
from utils.cochlea import sounds_to_spikes
from utils.log import logger
from consts import Paths
from pathlib import Path
from dataclasses import dataclass
import pickle
import nest

nest.set_verbosity("M_ERROR")

SOUND_DURATION = 1 * second
SOUND_FREQUENCIES = [100 * Hz, 1 * kHz, 10 * kHz]
# i actually just listened to the sounds... :)
ANGLES = [90, 75, 60, 45, 30, 15, 0, 345, 330, 315, 300, 285, 270]
# range(90, 271, 15)
INFO_FILE_NAME = "info.txt"
INFO_HEADER = "this directory holds all computed angles for a specific sound. the pickled sound is also available. \n"


def create_base_sound_key(frequency: str | Quantity, sound_type):
    # when we move to non single frequency sounds we can just pass a descriptive string maybe
    if type(frequency) == Quantity:
        frequency = str(frequency).replace(" ", "")
    return f"{sound_type}_{frequency}"


def generate_possible_sounds():
    sounds: dict[str, Sound] = {}
    for freq in SOUND_FREQUENCIES:
        sound = Sound.tone(freq, SOUND_DURATION)
        sounds[create_base_sound_key(freq, "tone")] = sound
    # other possible sounds can be added here
    # for type_sound in ['tone', 'click', 'realistic']:...
    return sounds


@dataclass
class SavedResponse:
    binaural_IHC_response: dict
    left: Sound
    right: Sound


def generate_ANF_and_save():
    logger.info(f"generating sound database...")
    sounds = generate_possible_sounds()
    hrtfdb = IRCAM_LISTEN(Paths.IRCAM_DIR)
    hrtfset = hrtfdb.load_subject(hrtfdb.subjects[0])
    for key, sound in sounds.items():
        logger.info(f"now handling sound {key}")

        # each angle (and channel) must now be converted to ANF spiking patterns
        logger.info(
            f"creating directory to keep all possible angles "
            f"of sound {key} converted to ANF spiking patterns..."
        )
        dirpath = Path(Paths.IHF_SPIKES_DIR).joinpath(key)
        dirpath.mkdir(parents=True, exist_ok=True)
        with open(dirpath.joinpath(INFO_FILE_NAME), "w") as f:
            f.write(INFO_HEADER + str(sound) + "\n" + key + "\n")
        with open(dirpath.joinpath(key + "_basesound.pic"), "wb") as f:
            pickle.dump(sound, f)

        for angle in ANGLES:
            hrtf = hrtfset(azim=angle, elev=0)
            # We apply the chosen HRTF to the sound, the output has 2 channels
            binaural_sound: np.NDArray = hrtf.filterbank(sound).process().T
            left = Sound(binaural_sound[0])
            right = Sound(binaural_sound[1])
            logger.info(f"generated {len(sounds.keys())} pairs of inputs to IHCs...")
            filepath = dirpath.joinpath(f"{key}_{angle}deg.pic")
            binaural_IHC_response = sounds_to_spikes(binaural_sound)

            logger.info(f"saving result to {filepath}")
            saved_data = SavedResponse(binaural_IHC_response, left, right)
            with open(filepath, "wb") as f:
                pickle.dump(saved_data, f)

        logger.info(f"completed sound {key}")


def load_saved_anf_spiketrain(sound_keys: list[str] | None = None):
    """
    {
        tone_1Hz: {
            90: {
                SavedResponse: {
                    binaural_IHC_response: dict:{
                        L : ...,
                        R : ...
                    },
                    left: Sound
                    right: Sound
                }
            },
            105: {
                SavedResponse: {
                    binaural_IHC_response: dict:{
                        L : ...,
                        R : ...
                    },
                    left: Sound
                    right: Sound
                }
            },
        }
        ...
    }
    """
    # for every sound_key, you'll get a dictionary of angle->IHC
    sounds = {}
    if sound_keys is None:
        for _, dirs, _ in Path(Paths.IHF_SPIKES_DIR).walk():
            sound_dirs = dirs
    else:
        sound_dirs = sound_keys
    # build the large dict that will hold all our values
    for sound_key in sound_dirs:
        dirpath = Path(Paths.IHF_SPIKES_DIR).joinpath(sound_key)
        angle_data = {}
        # unpickle all saved ihc responses (and corresponding sounds)
        for angle_path in dirpath.glob("*deg.pic"):
            angle_filename = angle_path.name
            # get angle string from angle files
            angle = angle_filename.split("Hz_")[1].split("deg")[0]
            with open(angle_path, "rb") as f:
                saved_data: SavedResponse = pickle.load(f)
            angle_data[angle] = saved_data
        # unpickle base sound
        basesound_path = list(dirpath.glob("*basesound.pic"))
        if len(basesound_path) == 1:
            with open(basesound_path[0], "rb") as f:
                angle_data["basesound"] = pickle.load((f))
        sounds[sound_key] = angle_data
    return sounds
