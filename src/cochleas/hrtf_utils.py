import math

import brian2 as b2
import numpy as np
from brian2 import ms
from brian2hears import IRCAM_LISTEN, Sound, dB

from analyze import sound_analysis as SA
from consts import Paths
from utils.custom_sounds import Tone, ToneBurst
from utils.log import logger
from utils.manual_fixes_to_b2h.HeadlessDatabase import HeadlessDatabase

from .consts import ANGLE_TO_IRCAM, ITD_REMOVAL_STRAT


def sel_range(s, start=0 * ms, end=10 * ms):
    return s[start:end]


def angle_to_itd(angle, w_head: int = 22, v_sound: int = 33000):
    delta_x = w_head * np.sin(np.deg2rad(angle))
    return round(1000 * delta_x / v_sound, 2) * b2.ms


def compensate_ITD(
    binaural_sound: Sound, angle, STRAT=ITD_REMOVAL_STRAT.COMPUTED, show_ITD_plots=False
):
    left = Sound(binaural_sound.left)
    right = Sound(binaural_sound.right)
    samplerate = binaural_sound.samplerate

    s_itd = SA.itd(left, right, display=show_ITD_plots)
    logger.debug(f"current ITD is {s_itd}")
    logger.debug(f"synthetic ITD for current angle {angle} is {angle_to_itd(angle)}")

    if STRAT == ITD_REMOVAL_STRAT.ESTIMATE_FROM_HRTF:
        pass
    elif STRAT == ITD_REMOVAL_STRAT.COMPUTED:
        s_itd = angle_to_itd(angle)

    # one sound will be shifted, the other padded, but b2h does
    if s_itd < 0:
        # sound comes from left, include delay
        left = left.shifted(abs(s_itd))
        # pad right
        right = Sound.sequence(right, Sound.silence(abs(s_itd), samplerate))
    elif s_itd > 0:
        # sound comes from right, include delay
        right = right.shifted(abs(s_itd))
        # pad left
        left = Sound.sequence(left, Sound.silence(abs(s_itd), samplerate))

    corrected_itd = SA.itd(left, right, display=show_ITD_plots)
    logger.debug(f"after correction, ITD is {corrected_itd} (should be close to zero)")
    return Sound((left, right), samplerate=samplerate), corrected_itd


def calculate_lefttoright_level_diff(freq, angle):
    azimuth_rad = np.radians(angle)
    head_radius = 0.0875  # meters
    speed_of_sound = 343.0  # m/s
    # Calculate wavelength and ka (wavelength * radius)
    wavelength = speed_of_sound / (freq / b2.Hz)
    ka = 2 * np.pi * head_radius / wavelength
    # Frequency-dependent shadowing effect
    # Higher ka values (higher frequencies or larger heads) create more shadowing
    shadowing = np.minimum(20, ka * 2)  # Limited to 20 dB maximum
    # Calculate ILD based on shadowing and azimuth
    # The sin term gives directionality, shadowing term scales with frequency
    ild = shadowing * np.sin(azimuth_rad)
    # returns left - right difference
    return np.abs(ild) * dB


def synthetic_ild(sound: Tone, angle: int):
    if type(sound) is not Tone:
        logger.error(f"selected HRTF synthetic_ild, but it only supports Tones")
        raise TypeError(f"sound is {type(sound)}, while it should be {Tone}")

    diff = calculate_lefttoright_level_diff(sound.frequency, angle)
    logger.debug(f"ILD calculated as {diff}")
    left = Sound(sound.sound)
    right = Sound(sound.sound)
    if angle > 0:
        left.set_level(left.get_level() - diff)
    else:
        right.set_level(right.get_level() - diff)

    # azimuth_rad = np.radians(angle)
    # max_mask = np.abs(np.sin(azimuth_rad))
    # if angle < 0:  # Sound comes from the left
    #     # Left ear gets less masking, right ear gets more
    #     left_masking_factor = -(1 - max_mask)
    #     right_masking_factor = -max_mask
    # else:  # Sound comes from the right
    #     # Right ear gets less masking, left ear gets more
    #     left_masking_factor = max_mask
    #     right_masking_factor = 1 - max_mask

    # logger.debug(
    #     f"{angle} -> left {diff * left_masking_factor}; right {diff * right_masking_factor}"
    # )
    # logger.debug(
    #     f"original ILD: {diff}; new ILD: {diff * left_masking_factor + diff * right_masking_factor}"
    # )
    # # logger.debug(
    # #     f"left {diff} * {left_masking_factor}; right {diff} * {right_masking_factor}"
    # # )
    # left.level += diff * left_masking_factor
    # right.level += diff * right_masking_factor

    return Sound((left, right), samplerate=sound.sound.samplerate)


# def synthetic_ild(sound: Tone, angle: int):
#     if type(sound) is not Tone:
#         logger.error(f"selected HRTF synthetic_ild, but it only supports Tones")
#         raise TypeError(f"sound is {type(sound)}, while it should be {Tone}")
#     if angle is 0:
#         return Sound((sound.sound, sound.sound), samplerate=sound.sound.samplerate)
#     diff = calculate_lefttoright_level_diff(sound.frequency, angle)
#     left = Sound(sound.sound)
#     right = Sound(sound.sound)
#     if diff < 0 * dB:
#         left.level += diff
#     else:
#         right.level -= diff
#     return Sound((left, right), samplerate=sound.sound.samplerate)


def run_hrtf(sound: Sound | Tone | ToneBurst, angle, hrtf_params) -> Sound:
    subj = hrtf_params["subj_number"]
    orig_sound = sound
    if type(sound) is not Sound:  # assume good faith, ok to fail otherwise
        sound = sound.sound
    samplerate = sound.samplerate
    original_duration = sound.duration
    if subj == "itd_only":
        # delay sound to mimic time to reach ear (conservative approximation,
        # it changes among HRTFs)
        sound = Sound.sequence(
            Sound.silence(5 * ms, sound.samplerate),
            sound,
        )
        hrtfset = HeadlessDatabase(13, azim_max=90).load_subject()
        hrtf = hrtfset(azim=angle)
        binaural_sound: Sound = hrtf(sound)
    elif subj == "ild_only":
        binaural_sound: Sound = synthetic_ild(orig_sound, angle)
    else:
        hrtfdb = IRCAM_LISTEN(Paths.IRCAM_DIR)
        hrtfset = hrtfdb.load_subject(hrtfdb.subjects[subj])
        hrtf = hrtfset(azim=ANGLE_TO_IRCAM[angle], elev=0)
        binaural_sound: Sound = hrtf(sound)

    binaural_sound = binaural_sound.resized(math.floor(original_duration * samplerate))
    return binaural_sound
