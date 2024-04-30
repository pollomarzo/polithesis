"""
generates a series of files with spike trains PICKLED


"""

from brian2 import Hz, kHz, second, Quantity
from brian2hears import Sound, IRCAM_LISTEN
import numpy as np
from cochlea import sounds_to_IHC
from utils import logger
from consts import Paths as P
from pathlib import Path
import pickle
import nest

nest.set_verbosity("M_ERROR")

SOUND_DURATION = 1 * second
SOUND_FREQUENCIES = [100 * Hz, 1 * kHz, 10 * kHz]
# i actually just listened to the sounds... :)
ANGLES = range(90, 271, 15)
INFO_FILE_NAME = "info.txt"
INFO_HEADER = "this directory holds all computed angles for a specific sound: \n"


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


def generate_ANF_and_save():
    logger.info(f"generating sound database...")
    sounds = generate_possible_sounds()
    hrtfdb = IRCAM_LISTEN(P.IRCAM_DIR)
    hrtfset = hrtfdb.load_subject(hrtfdb.subjects[0])
    for key, sound in sounds.items():
        logger.info(f"now handling sound {key}")

        # each angle (and channel) must now be converted to ANF spiking patterns
        logger.info(
            f"creating directory to keep all possible angles "
            "of sound {key} converted to ANF spiking patterns..."
        )
        dirpath = Path(P.IHF_SPIKES_DIR).joinpath(key)
        dirpath.mkdir(parents=True, exist_ok=True)
        with open(dirpath.joinpath(INFO_FILE_NAME), "w") as f:
            f.write(INFO_HEADER + str(sound) + "\n")

        for angle in ANGLES:
            hrtf = hrtfset(azim=angle, elev=0)
            # We apply the chosen HRTF to the sound, the output has 2 channels
            binaural_sound: np.NDArray = hrtf.filterbank(sound).process().T
            logger.info(f"generated {len(sounds.keys())} pairs of inputs to IHCs...")
            filepath = dirpath.joinpath(f"{key}_{angle}deg.pic")
            binaural_IHC_response = sounds_to_IHC(
                binaural_sound, save_to_file=True, filepath=filepath
            )

        logger.info(f"completed sound {key}")


def load_saved_ihcs(sound_keys: list[str] | None = None):
    """
    {
        tone_1Hz: {
            90: {
                L : ...,
                R : ...
            },
            105: {
                L : ...,
                R : ...
            }
        }
        ...
    }
    """
    # for every sound_key, you'll get a dictionary of angle->IHC
    sounds = {}
    if sound_keys is None:
        for _, dirs, _ in Path(P.IHF_SPIKES_DIR).walk():
            sound_dirs = dirs
    else:
        sound_dirs = sound_keys
    # build the large dict that will hold all our values
    for sound_key in sound_dirs:
        dirpath = Path(P.IHF_SPIKES_DIR).joinpath(sound_key)
        angle_to_IHC = {}
        for angle_path in dirpath.glob("*.pic"):
            angle_filename = angle_path.name
            angle = angle_filename.split("Hz_")[1].split("deg")[0]
            with open(angle_path, "rb") as f:
                angle_values = pickle.load(f)
            angle_to_IHC[angle] = angle_values
        sounds[sound_key] = angle_to_IHC
    return sounds


if __name__ == "__main__":
    generate_ANF_and_save()
