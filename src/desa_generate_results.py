import datetime
import resource
from datetime import timedelta
from pathlib import Path
from timeit import default_timer as timer

import brian2 as b2
import brian2hears as b2h
import dill
import nest
import nest.voltage_trace
from brian2 import Hz

from cochleas.anf_utils import TC_COC_KEY, create_sound_key, load_anf_response

from cochleas.consts import ANGLES
from consts import Paths, save_current_conf
from models.BrainstemModel.BrainstemModel import BrainstemModel
from models.BrainstemModel.params import Parameters as TCParam
from utils.custom_sounds import Click, Tone, ToneBurst, WhiteNoise
from utils.log import logger, tqdm

# big result objects need big stacks
resource.setrlimit(
    resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
)

nest.set_verbosity("M_ERROR")

TIME_SIMULATION = 1000


create_execution_key = lambda i, c, p: f"{create_sound_key(i)}&{c}&{p}"
ex_key_with_time = (
    lambda *args: f"{datetime.datetime.now().isoformat()[:-7]}&{create_execution_key(*args)}"
)

CURRENT_TEST = "angle2rates3"

def create_save_result_object(
    input,
    angle_to_rate,
    model,
    param,
    cochlea_key,
    result_file,
    **kwargs,
):
    result = {}
    result["basesound"] = input
    result["angle_to_rate"] = angle_to_rate
    for key, arg in kwargs.items():
        result[key] = arg
    result["conf"] = save_current_conf(
        model, param, cochlea_key, create_sound_key(input)
    )
    logger.info(f"\tsaving results for {ex_key} to {result_file.absolute()}...")
    with open(result_file, "wb") as f:
        dill.dump(result, f)
    del result


if __name__ == "__main__":

    inputs = [Tone(i, 1000 * b2.ms) for i in [1000, 10000] * b2.Hz]
    for e in inputs:
        e.sound.level = 70 * b2h.dB

    models = [BrainstemModel, BrainstemModel, BrainstemModel]
    cochlea_key = TC_COC_KEY

    p2 = TCParam("itd_only")
    p2.cochlea[cochlea_key]['subj_number'] = 'itd_only'

    p3 = TCParam("ild_only")
    p3.cochlea[cochlea_key]['subj_number'] = 'ild_only'

    params = [p2,p3]

    num_runs = len(inputs) * len(params)
    current_run = 0
    logger.info(f"launching {num_runs} trials...")
    times = {}
    result_dir = Path(Paths.RESULTS_DIR) / CURRENT_TEST
    trials_pbar = tqdm(total=num_runs, desc="trials")

    for Model, param in zip(models, params):
        curr_ex = f"{cochlea_key}&{param.key}"
        result_paths = []
        for input in inputs:
            start = timer()
            ex_key = ex_key_with_time(input, cochlea_key, param.key)
            logger.info(
                f">>>>> now testing arch n.{current_run+1} of {num_runs}"
            )
            angle_to_rate = {}
            for angle in tqdm(ANGLES, "⮡ angles"):
                nest.ResetKernel()
                nest.SetKernelStatus(param.CONFIG.NEST_KERNEL_PARAMS)

                logger.info(f"starting trial for {angle}")
                # this section is cached on disk
                anf = load_anf_response(input, angle, cochlea_key, param.cochlea)
                logger.info("ANF loaded. Creating model...")

                model = Model(param, anf)
                logger.info("model created. starting simulation...")
                model.simulate(TIME_SIMULATION)

                model_result = model.analyze()
                logger.debug(
                    f"leftMSO is spiking at {len(model_result['L']['MSO']['times'])/TIME_SIMULATION*1000}Hz"
                )
                angle_to_rate[angle] = model_result
                logger.info("trial complete.")

            logger.info(f"saving all angles for model {ex_key}...")

            # save model results to file
            filename = f"{ex_key}.pic"
            result_file = result_dir / filename
            result_paths.append(result_file)

            end = timer()
            timetaken = timedelta(seconds=end - start)
            current_run = current_run + 1
            times[ex_key] = timetaken
            create_save_result_object(
                input,
                angle_to_rate,
                model,
                param,
                cochlea_key,
                result_file,
                filename=filename,
                simulation_time=TIME_SIMULATION,
                times={"start": start, "end": end, "timetaken": timetaken},
            )

    trials_pbar.close()
    logger.debug(times)
    logger.info({k: str(v) for k, v in times.items()})
