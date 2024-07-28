from pathlib import Path
from utils.custom_sounds import Tone
from models.InhModel.InhModel import InhModel
from models.InhModel.params import Parameters as InhParam
from consts import Paths, save_current_conf
from utils.log import logger
import brian2 as b2, brian2hears as b2h
from brian2 import Hz
from cochleas.anf_utils import load_anf_response, COCHLEAS, create_sound_key
from cochleas.consts import ANGLES
from sorcery import dict_of
import dill
import datetime
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

b2.seed(42)  # https://brian2.readthedocs.io/en/stable/advanced/random.html

TIME_SIMULATION = 1000
create_execution_key = lambda i, c, m, p: f"{create_sound_key(i)}&{c}&{m}&{p}"
ex_key_with_time = (
    lambda *args: f"{create_execution_key(*args)}&{datetime.datetime.now().isoformat()[:-7]}"
)


if __name__ == "__main__":
    inputs = [Tone(i) for i in [100, 1000, 10000] * Hz]
    for i in inputs:
        i.sound.level = 70 * b2h.dB

    params_modified = InhParam()
    # Pecka et al, Glycinergic Inhibition, https://doi.org/10.1523/JNEUROSCI.1660-08.2008
    params_modified.SYN_WEIGHTS.SBCs2MSO_inh = 0
    params_modified.SYN_WEIGHTS.MNTBCs2MSO = 0
    params_modified.key = "no_inh_MSO"

    params = [InhParam()]  # , PpgParam()]
    # params = [params_modified, InhParam()]  # , PpgParam()]
    models = [InhModel]  # , PpgModel]
    # models = [InhModel, InhModel]  # , PpgModel]
    cochleas = COCHLEAS
    result = {}
    num_runs = len(inputs) * len(cochleas) * len(params)
    current_run = 0
    logger.info(f"launching {num_runs} trials...")
    for input in inputs:
        for cochlea_key, cochlea in cochleas.items():
            for Model, parameters in zip(models, params):
                ex_key = ex_key_with_time(input, cochlea_key, Model.key, parameters.key)
                logger.info(
                    f">>>>> now testing arch n.{current_run} of {num_runs}, with key {ex_key}"
                )
                result = {
                    "basesound": input,
                }
                angle_to_rate = {}
                for angle in ANGLES:
                    nest.ResetKernel()
                    logger.info(f"starting trial for {dict_of(ex_key,angle)}")
                    # this section is cached on disk
                    anf = load_anf_response(input, angle, cochlea_key)
                    logger.info("anf loaded. Creating model...")

                    model = Model(parameters, anf)
                    logger.info("model created. starting simulation...")
                    model.simulate(TIME_SIMULATION)

                    model_result = model.analyze()
                    angle_to_rate[angle] = model_result
                    logger.info("trial complete.")

                logger.info(f"saving all angles for model {ex_key}...")
                # save model results to file
                result_file = Path(Paths.RESULTS_DIR).joinpath(f"{ex_key}.pic")

                result["conf"] = save_current_conf(
                    model, parameters, cochlea_key, create_sound_key(input)
                )
                result["angle_to_rate"] = angle_to_rate

                logger.info(
                    f"\tsaving results for {ex_key} to {result_file.absolute()}..."
                )
                with open(result_file, "wb") as f:
                    dill.dump(result, f)

                current_run = current_run + 1
