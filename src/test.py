import brian2 as b2
import brian2hears as b2h
import nest
import numpy as np
from brian2 import *
from brian2hears import *

from cochleas.anf_utils import load_anf_response
from cochleas.GammatoneCochlea import sound_to_spikes as s2sGamm
from cochleas.TanCarneyCochlea import sound_to_spikes
from models.InhModel.params import Parameters as InhParam
from utils.custom_sounds import Tone

nest.set_verbosity("M_ERROR")

sound = Tone(100 * b2.Hz, 200 * b2.ms)
sound.sound.level = 90 * b2h.dB
ANGLE = -45
params = InhParam()
spikes_real = sound_to_spikes.call(sound, ANGLE, params.cochlea["TanCarney"], True)

spikes_tc = s2sGamm.call(sound, ANGLE, params.cochlea["gammatone"], True)
