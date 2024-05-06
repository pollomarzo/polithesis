from SLModel import SLModel
from cochlea import spikes_to_nestgen
from utils import logger
from generate_DB import load_saved_anf_as_nestgen
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

result = load_saved_anf_as_nestgen(["tone_1.kHz"])
binaural_ihc = result["tone_1.kHz"]["90"]

model = SLModel(binaural_ihc)
