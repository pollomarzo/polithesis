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

PLOT_FINAL = True
PLOT_INTERMEDIATE = False

CURRENT_TEST = "msoratetoolow"


if __name__ == "__main__":
    inputs = [Tone(i) for i in [100, 500, 800, 1000, 5000] * Hz]
    for e in inputs:
        e.sound.level = 100 * b2h.dB

    params1 = InhParam("1.2excMSO")
    params1.SYN_WEIGHTS.SBCs2MSO = 1.2

    params2 = InhParam("1.4excMSO")
    params2.SYN_WEIGHTS.SBCs2MSO = 1.2
    params3 = InhParam("0.5uFMSO")
    params3.C_mso = 0.5
    params4 = InhParam("0.1delips-0.6delcontr")
    params4.DELAYS.DELTA_IPSI = 0.1
    params4.DELAYS.DELTA_CONTRA = -0.6
    # params.cochlea["realistic"]["subj_number"] = 2
    # params.cochlea["realistic"]["noise_factor"] = 0
    # params.SYN_WEIGHTS.LNTBCs2MSO = params.SYN_WEIGHTS.MNTBCs2MSO = -3.0
    params = [params1, params2, params3, params4]

    models = [InhModel, InhModel, InhModel, InhModel]
    # cochleas = {REAL_COC_KEY: real_cochlea}
    # cochleas = {PPG_COC_KEY: ppg_cochlea}
    cochleas = COCHLEAS
    num_runs = len(inputs) * len(cochleas) * len(params)
    current_run = 0
    logger.info(f"launching {num_runs} trials...")
    times = {}
    result_dir = Path(Paths.RESULTS_DIR) / CURRENT_TEST
    trials_pbar = tqdm(total=num_runs, desc="trials")
    for Model, param in zip(models, params):
        for cochlea_key, cochlea in cochleas.items():
            curr_ex = f"{Model.key}&{cochlea_key}&{param.key}"
            curr_result_dir = result_dir / curr_ex
            curr_result_dir.mkdir(exist_ok=True, parents=True)
            result_paths = []
            for input in inputs:
                result = {
                    "basesound": input,
                }
                start = timer()
                ex_key = ex_key_with_time(input, cochlea_key, Model.key, param.key)
                logger.info(
                    f">>>>> now testing arch n.{current_run+1} of {num_runs}, with key {ex_key}"
                )
                angle_to_rate = {}
                for angle in tqdm(ANGLES, "⮡ angles"):
                    nest.ResetKernel()
                    nest.SetKernelStatus(param.CONFIG.NEST_KERNEL_PARAMS)

                    logger.info(f"starting trial for {dict_of(ex_key,angle)}")
                    # this section is cached on disk
                    anf = load_anf_response(input, angle, cochlea_key, param.cochlea)
                    logger.info("anf loaded. Creating model...")

                    model = Model(param, anf)
                    logger.info("model created. starting simulation...")
                    model.simulate(TIME_SIMULATION)

                    model_result = model.analyze()
                    angle_to_rate[angle] = model_result
                    logger.info("trial complete.")

                logger.info(f"saving all angles for model {ex_key}...")
                # save model results to file
                filename = f"{ex_key}.pic"
                result_file = curr_result_dir / filename
                result_paths.append(result_file)

                result["conf"] = save_current_conf(
                    model, param, cochlea_key, create_sound_key(input)
                )
                result["filename"] = filename
                result["angle_to_rate"] = angle_to_rate

                logger.info(
                    f"\tsaving results for {ex_key} to {result_file.absolute()}..."
                )
                end = timer()
                timetaken = timedelta(seconds=end - start)
                result["times"] = {"start": start, "end": end, "timetaken": timetaken}
                current_run = current_run + 1
                times[ex_key] = timetaken
                with open(result_file, "wb") as f:
                    dill.dump(result, f)

                del result  # result files are getting quite large, let's make sure not to keep them in memory
                if PLOT_INTERMEDIATE:
                    generate_single_result(result_file)
                trials_pbar.update()

            if PLOT_FINAL:
                generate_multi_inputs_single_net(
                    result_paths, cleanup=not PLOT_INTERMEDIATE
                )
    trials_pbar.close()
    logger.debug(times)
    logger.info({k: str(v) for k, v in times.items()})
