import brian2 as b2
import numpy as np
from brian2 import ms
from brian2hears import IRCAM_LISTEN, Sound

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


def run_hrtf(sound: Sound | Tone | ToneBurst, angle, hrtf_params) -> Sound:
    subj = hrtf_params["subj_number"]
    ild_only = hrtf_params["ild_only"]

    if type(sound) is not Sound:  # assume good faith, ok to fail otherwise
        sound = sound.sound
    if subj == "headless":
        hrtfset = HeadlessDatabase(13, azim_max=90).load_subject()
        hrtf = hrtfset(azim=angle)
    else:
        hrtfdb = IRCAM_LISTEN(Paths.IRCAM_DIR)
        hrtfset = hrtfdb.load_subject(hrtfdb.subjects[subj])
        hrtf = hrtfset(azim=ANGLE_TO_IRCAM[angle], elev=0)
    binaural_sound: Sound = hrtf(sound)

    if ild_only:
        binaural_sound, compensated_itd = compensate_ITD(
            binaural_sound,
            angle,
            hrtf_params["itd_remove_strategy"],
            show_ITD_plots=hrtf_params.get("show_ITD_plots", False),
        )
    return binaural_sound
