from SLModel import SLModel
from utils import logger
from generate_DB import load_saved_anf_as_nestgen
from consts import Paths, save_current_conf, Parameters
from pathlib import Path
import brian2
import dill
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


logger.info("beginning to cycle through angles...")
params_normal = Parameters()
params_modified = Parameters()
# Pecka et al, Glycinergic Inhibition, https://doi.org/10.1523/JNEUROSCI.1660-08.2008
params_modified.SYN_WEIGHTS.SBCs2MSO_inh = 0
params_modified.SYN_WEIGHTS.MNTBCs2MSO = 0

for params, model_key, model_desc in zip(
    [params_normal, params_modified],
    ["default", "no_inh"],
    [SLModel.name, "inhibition to MSO turned off"],
):
    logger.info(f"\tnow working on model {model_key}")
    result = {}
    angle_to_rate = {}
    """
    {
        90: {n_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso},
        105: {n_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso}
        ...
    }
    """
    for angle, binaural_anf in anf_spikes.items():
        nest.ResetKernel()
        logger.info(f"\t\tcurrent angle: {angle}")
        model = SLModel(params, binaural_anf)
        model.name = model_key
        logger.info(f"\t\t\tmodel initialized. begin simulation...")
        model.simulate(TIME_SIMULATION)
        logger.info(f"\t\t\t...simulation complete. collecting results...")
        angle_to_rate[angle] = model.analyze()

    result_file = Path(Paths.RESULTS_DIR).joinpath(
        f"{SOUND}-{model_key}-{datetime.datetime.now().isoformat()[:-5]}.pic"
    )

    result["conf"] = save_current_conf(model, params)
    result["angle_to_rate"] = angle_to_rate

    logger.info(f"\tsaving results for {model_key} to {result_file.absolute()}...")
    with open(result_file, "wb") as f:
        dill.dump(result, f)
