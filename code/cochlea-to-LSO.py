from SLModel import SLModel
from utils import logger
from generate_DB import load_saved_anf_as_nestgen
from consts import Paths as P
from pathlib import Path
import brian2
import pickle
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

brian2.seed(42)

TIME_SIMULATION = 1000

logger.info("loading saved anfs...")

CURRENT_TONE = "tone_1.kHz"
anf_spikes = load_saved_anf_as_nestgen([CURRENT_TONE])[CURRENT_TONE]
logger.info("...loaded saved anfs!")

results = {}
"""
{
    90: (n_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso),
    105: (n_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso)
    ...
}
"""

logger.info("beginning to cycle through angles...")
for angle, binaural_anf in anf_spikes.items():
    nest.ResetKernel()
    logger.info(f"\tcurrent angle: {angle}")
    model = SLModel(binaural_anf)
    logger.info(f"\t\tmodel initialized. begin simulation...")
    model.simulate(TIME_SIMULATION)
    logger.info(f"\t\t...simulation complete. collecting results...")
    results[angle] = model.analyze()
    logger.info(
        f"\t\tn_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso: {str(results[angle])}"
    )


result_file = Path(P.RESULTS_DIR).joinpath(f"{CURRENT_TONE}.pic")
logger.info(f"saving results to {result_file.absolute()}...")
with open(result_file, "wb") as f:
    pickle.dump(results, f)
