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
from sorcery import dict_of

from analyze.report import generate_multi_inputs_single_net, generate_single_result
from cochleas.anf_utils import (
    B2_COC_KEY,
    COCHLEAS,
    DCGC_COC_KEY,
    GAMMATONE_COC_KEY,
    PPG_COC_KEY,
    DCGC_cochlea,
    b2_cochlea,
    create_sound_key,
    gammatone_cochlea,
    load_anf_response,
    ppg_cochlea,
)
from cochleas.consts import ANGLES
from consts import Paths, save_current_conf
from models.InhModel.InhModel import InhModel
from models.InhModel.params import Parameters as InhParam
from models.InhModel.PPGparams import Parameters as PPGParam
from models.InhModel.TCparams import Parameters as TCParam
from utils.custom_sounds import Click, Tone, ToneBurst, WhiteNoise
from utils.log import logger, tqdm

# big result objects need big stacks
resource.setrlimit(
    resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
)

nest.set_verbosity("M_ERROR")

TIME_SIMULATION = 200
create_execution_key = lambda i, c, m, p: f"{create_sound_key(i)}&{c}&{m}&{p}"
ex_key_with_time = (
    lambda *args: f"{datetime.datetime.now().isoformat()[:-7]}&{create_execution_key(*args)}"
)

PLOT_FINAL = True
PLOT_INTERMEDIATE = False

# CURRENT_TEST = "click_white"
# CURRENT_TEST = "correct_time_simulation"
CURRENT_TEST = "produce_for_thesis"


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


if __name__ == "__main__":
    # c = Click(duration=300 * b2.ms, peak=90 * b2h.dB)
    # w = WhiteNoise(duration=300 * b2.ms, level=90 * b2h.dB)
    inputs = [ToneBurst(frequency=i) for i in [600] * b2.Hz]
    for e in inputs:
        e.sound.level = 80 * b2h.dB

    # tcparam = TCParam("41SBCs2LSO18")
    # notes; LSO has a weird notch at 1khz, not sure what to do. might need more inhibition AND higher sbc exc. results at 100, 800Hz are very good. MSO needs a little more exc and some more MNTB i think
    # tcparam = TCParam("41SBCs2LSO20SBC2MSO19MNTB2LSO-35")
    # notes: still weird notch, LSO is too strong, basically only thing that matters. which is good, because it would be just making things worse
    # params = []
    # for noise in [60, 70]:
    #     tcparam = TCParam(f"hrtf4noise{noise}")
    #     tcparam.cochlea["TanCarney"]["omni_noise_level"] = noise
    #     params.append(tcparam)
    # p1 = PPGParam("17")
    # p1 = InhParam("onlyITD")
    p2 = TCParam("verifytancarney")
    # p2 = PPGParam("highergl+highersbc")
    # p2.SYN_WEIGHTS.SBCs2MSOipsi = 5
    # p2.SYN_WEIGHTS.SBCs2MSOcontra = 5

    # p3 = PPGParam("highergl+highersbc+higherinh")
    # p3.SYN_WEIGHTS.SBCs2MSOipsi = 5
    # p3.SYN_WEIGHTS.SBCs2MSOcontra = 5
    # p3.SYN_WEIGHTS.MNTBCs2MSO = -30
    # p3.SYN_WEIGHTS.LNTBCs2MSO = -20

    # p4 = PPGParam("highergl+highersbc+higherinh+lowercm")
    # p4.SYN_WEIGHTS.SBCs2MSOipsi = 5
    # p4.SYN_WEIGHTS.SBCs2MSOcontra = 5
    # p4.SYN_WEIGHTS.MNTBCs2MSO = -30
    # p4.SYN_WEIGHTS.LNTBCs2MSO = -20
    # p4.MEMB_CAPS.MSO = 15

    params = [p2]

    # Bushy Cells receive multiple inputs from auditory nerve fibers via specialized end-bulb synapses
    # MNTB cells typically receive a single, massive input from one GBC via the calyx of Held synapse
    # MNTB cells act as sign-inverters, converting excitatory input to precisely-timed inhibitory output

    models = [InhModel, InhModel, InhModel, InhModel, InhModel, InhModel]
    cochleas = [
        # (GAMMATONE_COC_KEY, gammatone_cochlea),
        (B2_COC_KEY, b2_cochlea),
        # (PPG_COC_KEY, ppg_cochlea),
    ]
    # cochleas = {PPG_COC_KEY: ppg_cochlea}
    # cochleas = {B2_COC_KEY: b2_cochlea}
    num_runs = len(inputs) * len(list(zip(cochleas, params)))
    current_run = 0
    logger.info(f"launching {num_runs} trials...")
    times = {}
    result_dir = Path(Paths.RESULTS_DIR) / CURRENT_TEST
    trials_pbar = tqdm(total=num_runs, desc="trials")
    for Model, param, (cochlea_key, cochlea) in zip(models, params, cochleas):
        # for cochlea_key, cochlea in cochleas.items():
        curr_ex = f"{Model.key}&{cochlea_key}&{param.key}"
        curr_result_dir = result_dir / curr_ex
        curr_result_dir.mkdir(exist_ok=True, parents=True)
        result_paths = []
        for input in inputs:
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
                logger.debug(
                    f"leftMSO is spiking at {len(model_result['L']['MSO']['times'])/TIME_SIMULATION*1000}Hz"
                )
                angle_to_rate[angle] = model_result
                logger.info("trial complete.")

            logger.info(f"saving all angles for model {ex_key}...")
            # save model results to file
            filename = f"{ex_key}.pic"
            result_file = curr_result_dir / filename
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

            if PLOT_INTERMEDIATE:
                generate_single_result(result_file)
            trials_pbar.update()

        if PLOT_FINAL:
            generate_multi_inputs_single_net(
                result_paths, cleanup=not PLOT_INTERMEDIATE, rate=True
            )
    trials_pbar.close()
    logger.debug(times)
    logger.info({k: str(v) for k, v in times.items()})
