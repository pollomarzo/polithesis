import datetime
from datetime import timedelta
from pathlib import Path
from timeit import default_timer as timer

import brian2 as b2
import brian2hears as b2h
import dill
import nest
import nest.voltage_trace
from brian2 import Hz
from sorcery import dict_of

from analyze.report import generate_multi_inputs_single_net, generate_single_result
from cochleas.anf_utils import COCHLEAS, create_sound_key, load_anf_response
from cochleas.consts import ANGLES
from consts import Paths, save_current_conf
from models.InhModel.InhModel import InhModel
from models.InhModel.params import Parameters as InhParam
from utils.custom_sounds import Tone
from utils.log import logger, tqdm

nest.set_verbosity("M_ERROR")

b2.seed(42)  # https://brian2.readthedocs.io/en/stable/advanced/random.html

TIME_SIMULATION = 1000
create_execution_key = lambda i, c, m, p: f"{create_sound_key(i)}&{c}&{m}&{p}"
ex_key_with_time = (
    lambda *args: f"{datetime.datetime.now().isoformat()[:-7]}&{create_execution_key(*args)}"
)


if __name__ == "__main__":
    inputs = [Tone(i) for i in [100] * Hz]
    # inputs = [Tone(i) for i in [100, 333] * Hz]
    for i, e in enumerate(inputs):
        e.sound.level = 110 * b2h.dB

    # params = InhParam("-2inh3excMSO")
    # params.SYN_WEIGHTS.LNTBCs2MSO = params.SYN_WEIGHTS.MNTBCs2MSO = -2.0
    # params.SYN_WEIGHTS.SBCs2MSO = 3
    params2 = InhParam("hrtf2")
    params2.cochlea["realistic"]["subj_number"] = 2
    params = [params2]

    models = [InhModel]
    cochleas = {REAL_COC_KEY: real_cochlea}
    # cochleas = COCHLEAS
    result = {}
    num_runs = len(inputs) * len(cochleas) * len(params)
    current_run = 0
    logger.info(f"launching {num_runs} trials...")
    times = {}
    for input in inputs:
        for cochlea_key, cochlea in cochleas.items():
            for Model, parameters in zip(models, params):
                start = timer()
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
                    nest.SetKernelStatus(parameters.CONFIG.NEST_KERNEL_PARAMS)

                    logger.info(f"starting trial for {dict_of(ex_key,angle)}")
                    # this section is cached on disk
                    anf = load_anf_response(
                        input, angle, cochlea_key, parameters.cochlea
                    )
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
                end = timer()
                times[ex_key] = timedelta(seconds=end - start)
logger.debug(times)
logger.info({k: str(v) for k, v in times.items()})
