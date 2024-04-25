from SLModel import SLModel
from cochlea import IHC_to_ANF
from utils import logger
from generate_DB import load_saved_ihcs
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

result = load_saved_ihcs(["tone_1.kHz"])
binaural_ihc = result["tone_1.kHz"]["90"]

model = SLModel(binaural_ihc)
