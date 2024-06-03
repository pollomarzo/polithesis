# from models.SLModel import SLModel
from models.InhModel.InhModel import InhModel
from utils.log import logger
from utils.helper_IHC_DB import (
    load_saved_anf_spiketrain,
    SoundAfterHRTF,
)
from consts import Paths, save_current_conf

# from models.SLModel.params import Parameters as SLParam
from models.InhModel.params import Parameters as InhParam
from pathlib import Path
import brian2, brian2hears as b2h
import dill
import datetime
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

brian2.seed(42)  # https://brian2.readthedocs.io/en/stable/advanced/random.html

TIME_SIMULATION = 1000

logger.info("loading saved anfs...")

SOUND = "tone_1.kHz"

sound_hrtfed: SoundAfterHRTF = load_saved_anf_spiketrain(
    # all the sounds you want to load...
    [SOUND]
)[SOUND]
logger.info("...loaded saved anfs!")


logger.info("beginning to cycle through angles...")
params_normal = InhParam()
params_modified = InhParam()
# Pecka et al, Glycinergic Inhibition, https://doi.org/10.1523/JNEUROSCI.1660-08.2008
params_modified.SYN_WEIGHTS.SBCs2MSO_inh = 0
params_modified.SYN_WEIGHTS.MNTBCs2MSO = 0

for params, model_key, model_desc in zip(
    [params_normal, params_modified],
    ["default", "no_inh"],
    [InhModel.name, "inhibition to MSO turned off"],
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
    for angle, binaural_anf in sound_hrtfed.angle_to_response.items():
        nest.ResetKernel()
        logger.info(f"\t\tcurrent angle: {angle}")
        model = InhModel(params, binaural_anf.binaural_IHC_response)
        model.name = model_key
        logger.info(f"\t\t\tmodel initialized. begin simulation...")
        model.simulate(TIME_SIMULATION)
        logger.info(f"\t\t\t...simulation complete. collecting results...")
        angle_to_rate[angle] = model.analyze()

    result_file = Path(Paths.RESULTS_DIR).joinpath(
        f"{SOUND}-{model_key}-{datetime.datetime.now().isoformat()[:-5]}.pic"
    )

    result["conf"] = save_current_conf(model, params, SOUND)
    # if i wanted, i could include the actual sound, which is in sound_hrtfed.basesound
    result["angle_to_rate"] = angle_to_rate

    logger.info(f"\tsaving results for {model_key} to {result_file.absolute()}...")
    with open(result_file, "wb") as f:
        dill.dump(result, f)
