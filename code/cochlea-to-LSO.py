from SLModel import SLModel
from utils import logger
from generate_DB import load_saved_anf_as_nestgen
from consts import Constants as C, Paths as P, save_current_conf
from pathlib import Path
import brian2
import pickle
import datetime
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

brian2.seed(42)  # https://brian2.readthedocs.io/en/stable/advanced/random.html

TIME_SIMULATION = 1000

logger.info("loading saved anfs...")

SOUND = "tone_1.kHz"

anf_spikes = load_saved_anf_as_nestgen([SOUND])[SOUND]
logger.info("...loaded saved anfs!")

result = {}

angle_to_rate = {}
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
    angle_to_rate[angle] = model.analyze()


result_file = Path(P.RESULTS_DIR).joinpath(
    f"{SOUND}_{datetime.datetime.now().isoformat()[:-5]}.pic"
)

result["conf"] = save_current_conf(model)
result["angle_to_rate"] = angle_to_rate

logger.info(f"saving results to {result_file.absolute()}...")
with open(result_file, "wb") as f:
    pickle.dump(result, f)
