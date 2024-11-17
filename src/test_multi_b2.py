import multiprocessing
import os
import sys

from brian2 import *
from brian2hears import dB

from cochleas.anf_utils import (
    B2_COC_KEY,
    GAMMATONE_COC_KEY,
    PPG_COC_KEY,
    load_anf_response,
)
from cochleas.consts import ANGLES
from models.InhModel.TCparams import Parameters
from utils.custom_sounds import Tone, ToneBurst

cochlea_key = B2_COC_KEY
param = Parameters()
freqs = [100, 300, 500, 1000, 5000, 10000]


coch_params = param.cochlea
# coch_params["TanCarney"]["subj_number"] = int(sys.argv[2])


def run_sim(angle):
    pid = os.getpid()
    print(f"RUNNING {pid}")
    input = Tone(500 * Hz, 1000 * ms)
    input.sound.level = 70 * dB
    anf = load_anf_response(input, angle, cochlea_key, coch_params)
    return anf


num_proc = 8


with multiprocessing.Pool(num_proc) as p:
    results = p.map(run_sim, ANGLES)
    p.close()
    p.join()
print(multiprocessing.current_process().name)
print("--------FINISHED-------------")
