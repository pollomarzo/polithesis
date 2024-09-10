from collections import defaultdict
import brian2hears as b2h
import brian2 as b2
import numpy as np
from cochleas.anf_response import AnfResponse
from utils.log import logger
from scipy.interpolate import interp1d
import math
import scipy.stats as stats
from utils.custom_sounds import Tone
from joblib import Memory
from sorcery import dict_of
from os import makedirs
from .consts import NUM_CF as N_IHCs, CFMIN, CFMAX
from consts import Paths


n_ANFs = int(N_IHCs * 10)
# cochlea array of frequencies
coch_freqs = np.round(
    np.logspace(
        np.log(CFMIN / b2.Hz), np.log(CFMAX / b2.Hz), num=N_IHCs, base=np.exp(1)
    ),
    2,
)
# [nr. of spikes], num of spikes for each pulse packet (PPG parameter)
ild_values = [
    10,
    50,
    100,
]
# [ms] Standard Deviation in PPG spikes for each pulse-packet (PPG parameter)
sdev = 0.1
x_values = np.array([-90, 0, 90])
w_head = 22  # [cm]
v_sound = 33000  # [cm/s]

r_angle_to_level = interp1d(x_values, ild_values, kind="linear")
l_angle_to_level = interp1d(x_values[::-1], ild_values, kind="linear")
COCHLEA_KEY = "ppg"
CACHE_DIR = Paths.ANF_SPIKES_DIR + COCHLEA_KEY + "/"
makedirs(CACHE_DIR, exist_ok=True)

memory = Memory(location=CACHE_DIR, verbose=0)


def create_spectro(tone, time_sim):
    channel_x = np.where(coch_freqs >= tone)[0][0]
    spectro = np.zeros((3500, time_sim))
    amplitudes = np.round(
        stats.norm.pdf(np.linspace(-1, 1, 21), 0, 1.0 / (math.sqrt(2 * math.pi) * 1)), 2
    )  # gaussian profile of amplitudes, with peak_amplitude = 1 for channel_x

    if True:
        if channel_x < 10:  # truncation of the gaussian profile of amplitudes
            spectro[channel_x : channel_x + 10 + 1, :] = amplitudes[10:].reshape(
                11, 1
            ) * np.ones((11, time_sim))
            spectro[0 : channel_x + 1, :] = amplitudes[10 - channel_x : 11].reshape(
                channel_x + 1, 1
            ) * np.ones((channel_x + 1, time_sim))
        elif channel_x > 3489:  # truncation of the gaussian profile of amplitudes
            spectro[channel_x - 10 : channel_x + 1] = amplitudes[:11].reshape(
                11, 1
            ) * np.ones((11, time_sim))
            spectro[channel_x:] = amplitudes[10 : 10 + 3500 - channel_x].reshape(
                3500 - channel_x, 1
            ) * np.ones((3500 - channel_x, time_sim))
        else:
            spectro[channel_x - 10 : channel_x + 10 + 1, :] = amplitudes.reshape(
                21, 1
            ) * np.ones((21, time_sim))
    else:
        spectro[channel_x, :] = np.ones(time_sim)

    return spectro


@memory.cache
def tone_to_ppg_spikes(sound: Tone, angle: int, params: dict):
    import nest

    tone_freq = sound.frequency / b2.Hz
    time_sim = int(sound.sound.duration / b2.ms)
    nest.ResetKernel()
    nest.SetKernelStatus(params["nest"])
    gen_l = nest.Create("pulsepacket_generator", N_IHCs, params={"sdev": sdev})
    gen_r = nest.Create("pulsepacket_generator", N_IHCs, params={"sdev": sdev})

    parrot_l = nest.Create("parrot_neuron", N_IHCs)
    parrot_r = nest.Create("parrot_neuron", N_IHCs)

    s_rec_l = nest.Create("spike_recorder")
    s_rec_r = nest.Create("spike_recorder")

    nest.Connect(gen_l, parrot_l, "one_to_one")
    nest.Connect(gen_r, parrot_r, "one_to_one")

    nest.Connect(parrot_l, s_rec_l, "all_to_all")
    nest.Connect(parrot_r, s_rec_r, "all_to_all")

    delta_x = w_head * np.sin(np.deg2rad(angle))
    itd = np.round(1000 * delta_x / v_sound, 2)  # ms
    spectro = create_spectro(tone_freq, time_sim)
    # sets up the PPGs according to sound spectrum
    logger.debug("starting simulation to determine PPG based ANF spiking...")
    for t in range(time_sim):
        for f in range(0, len(spectro) - 1):
            if spectro[f][t] > 0:
                gen_l[f].set(
                    pulse_times=np.around(
                        np.arange(1 + itd, time_sim + itd + 1, 1000 / coch_freqs[f]), 2
                    )
                )
                gen_r[f].set(
                    pulse_times=np.arange(1, time_sim + 1, 1000 / coch_freqs[f])
                )

                if t in np.around(np.arange(0, time_sim, 1000 / coch_freqs[f]), 0):
                    gen_l[f].set(activity=int(spectro[f][t] * l_angle_to_level(angle)))
                    gen_r[f].set(activity=int(spectro[f][t] * r_angle_to_level(angle)))
                # ANF_noise to parrots
                # nest.Connect(ANFs_noise, r_ANFs[10 * r : 10 * (r + 1)], "all_to_all")
                # nest.Connect(ANFs_noise, l_ANFs[10 * r : 10 * (r + 1)], "all_to_all")
        if t % 100 == 0:
            logger.debug(f"ANF simulation: step n. {t}")
        nest.Simulate(1)

    spiketrains = {"L": {}, "R": {}}
    logger.debug(f"shifting spiketrain IDs into [1,n_ANFs] range of IDs...")
    old2new_id = {
        "L": {i: e for e, i in enumerate([i.get("global_id") for i in parrot_l])},
        "R": {i: e for e, i in enumerate([i.get("global_id") for i in parrot_r])},
    }
    logger.debug(f"created translation")

    for side, events in {
        "L": s_rec_l.get("events"),
        "R": s_rec_r.get("events"),
    }.items():
        spiketrains[side] = defaultdict(list)
        for old_id, data in zip(events["senders"], events["times"]):
            new_id = old2new_id[side][old_id]
            spiketrains[side][new_id].append(data * b2.ms)
    logger.debug(f"spiketrains completed")

    nest.ResetKernel()
    return AnfResponse(spiketrains, sound.sound, sound.sound)
