import numpy as np
from .params import Parameters
from utils.log import logger
from ..SpikingModel import SpikingModel
from inspect import getsource
from scipy.interpolate import interp1d
import math
import scipy.stats as stats
import nest

n_IHCs = 3500
n_ANFs = int(n_IHCs * 10)
# cochlea array of frequencies
freq = np.round(np.logspace(np.log(20), np.log(20000), num=n_IHCs, base=np.exp(1)), 2)
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


def create_spectro(tone, time_sim):
    channel_x = np.where(freq >= tone)[0][0]
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


class PpgModel(SpikingModel):
    name = "Inhibitory model, mso iaf_cond_beta"
    key = ""

    def __init__(self, parameters, tone, angle):
        self.params = parameters
        self.tone = tone
        self.angle = angle
        logger.info("creating pulsepacket generator according to input IHC response...")
        generators = {
            "L": nest.Create("pulsepacket_generator", n_ANFs, params={"sdev": sdev}),
            "R": nest.Create("pulsepacket_generator", n_ANFs, params={"sdev": sdev}),
        }
        self.create_network(parameters, generators)
        logger.info("creating rest of network...")
        logger.info("model creation complete.")

    def describe_model(self):
        return {"name": self.name, "networkdef": getsource(self.create_network)}

    def create_network(self, P: Parameters, anfs_per_ear):
        self.l_ANFs = anfs_per_ear["L"]
        self.r_ANFs = anfs_per_ear["R"]

        r_SBCs = nest.Create(
            "iaf_cond_alpha", P.n_SBCs, params={"C_m": P.C_m_sbc, "V_reset": P.V_reset}
        )
        l_SBCs = nest.Create(
            "iaf_cond_alpha", P.n_SBCs, params={"C_m": P.C_m_sbc, "V_reset": P.V_reset}
        )
        r_GBCs = nest.Create(
            "iaf_cond_alpha", P.n_GBCs, params={"C_m": P.C_m_gcb, "V_reset": P.V_reset}
        )
        l_GBCs = nest.Create(
            "iaf_cond_alpha", P.n_GBCs, params={"C_m": P.C_m_gcb, "V_reset": P.V_reset}
        )
        r_MNTBCs = nest.Create(
            "iaf_cond_alpha", P.n_GBCs, params={"C_m": P.C_m_gcb, "V_reset": P.V_reset}
        )
        l_MNTBCs = nest.Create(
            "iaf_cond_alpha", P.n_GBCs, params={"C_m": P.C_m_gcb, "V_reset": P.V_reset}
        )
        r_MSO = nest.Create(
            "iaf_cond_beta",
            P.n_MSOs,
            params={
                "C_m": P.cap_nuclei,
                "tau_rise_ex": P.MSO_TAUS.rise_ex,
                "tau_rise_in": P.MSO_TAUS.rise_in,
                "tau_decay_ex": P.MSO_TAUS.decay_ex,
                "tau_decay_in": P.MSO_TAUS.decay_in,
                "V_reset": P.V_reset,
            },
        )
        l_MSO = nest.Create(
            "iaf_cond_beta",
            P.n_MSOs,
            params={
                "C_m": P.cap_nuclei,
                "tau_rise_ex": P.MSO_TAUS.rise_ex,
                "tau_rise_in": P.MSO_TAUS.rise_in,
                "tau_decay_ex": P.MSO_TAUS.decay_ex,
                "tau_decay_in": P.MSO_TAUS.decay_in,
                "V_reset": P.V_reset,
            },
        )
        r_LSO = nest.Create(
            "iaf_cond_alpha",
            P.n_GBCs,
            params={"C_m": P.cap_nuclei, "V_reset": P.V_reset},
        )
        l_LSO = nest.Create(
            "iaf_cond_alpha",
            P.n_GBCs,
            params={"C_m": P.cap_nuclei, "V_m": P.V_m, "V_reset": P.V_reset},
        )

        self.s_rec_r_LSO = nest.Create("spike_recorder")
        self.s_rec_l_LSO = nest.Create("spike_recorder")
        self.s_rec_r_MSO = nest.Create("spike_recorder")
        self.s_rec_l_MSO = nest.Create("spike_recorder")

        # Devices
        nest.Connect(r_MSO, self.s_rec_r_MSO, "all_to_all")
        nest.Connect(l_MSO, self.s_rec_l_MSO, "all_to_all")

        nest.Connect(r_LSO, self.s_rec_r_LSO, "all_to_all")
        nest.Connect(l_LSO, self.s_rec_l_LSO, "all_to_all")

        # ANFs to SBCs
        for i in range(P.n_SBCs):
            nest.Connect(
                self.r_ANFs[P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)],
                r_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
            nest.Connect(
                self.l_ANFs[P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)],
                l_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
        # ANFs to GBCs
        for i in range(P.n_GBCs):
            nest.Connect(
                self.r_ANFs[P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)],
                r_GBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            )
            nest.Connect(
                self.l_ANFs[P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)],
                l_GBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            )

        # GBCs to MNTBCs
        nest.Connect(
            r_GBCs,
            r_MNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2MNTBCs,
                "delay": P.DELAYS.GBCs2MNTBCs,
            },
        )
        nest.Connect(
            l_GBCs,
            l_MNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2MNTBCs,
                "delay": P.DELAYS.GBCs2MNTBCs,
            },
        )

        # MSO
        for i in range(P.n_MSOs):
            # r_MSO
            #   From SBCs (excitation):
            #       ipsi
            nest.Connect(
                r_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO,
                    "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
                },
            )
            #       contra
            nest.Connect(
                l_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO,
                    "delay": P.DELAYS.SBCs2MSO_exc_contra,
                },
            )
            # From LNTBCs (mirrors SBC) (inhibition), ipsi
            nest.Connect(
                r_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO_inh,
                    "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
                },
            )
            # From MNTBCs (inh) contra outside of loop

            # l_MSO
            # From SBCs (excitation):
            #       ipsi
            nest.Connect(
                l_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO,
                    "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
                },
            )
            #       contra
            nest.Connect(
                r_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO,
                    "delay": P.DELAYS.SBCs2MSO_exc_contra,
                },
            )
            # From LNTBCs (mirrors SBC) (inhibition) ipsi
            nest.Connect(
                l_SBCs[P.SBCs2MSOs * i : P.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": P.SYN_WEIGHTS.SBCs2MSO_inh,
                    "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
                },
            )
            # From MNTBCs (inh) contra outside of loop

        # From MNTBCs (inhibition) contra
        nest.Connect(
            l_MNTBCs,
            r_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )
        # From MNTBCs (inhibition) contra
        nest.Connect(
            r_MNTBCs,
            l_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )

        # LSO
        for i in range(0, P.n_GBCs):
            nest.Connect(
                r_SBCs[P.SBCs2LSOs * i : P.SBCs2LSOs * (i + 1)],
                r_LSO[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            )
            nest.Connect(
                l_SBCs[P.SBCs2LSOs * i : P.SBCs2LSOs * (i + 1)],
                l_LSO[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            )

        nest.Connect(
            r_MNTBCs,
            l_LSO,
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )
        nest.Connect(
            l_MNTBCs,
            r_LSO,
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )

    def simulate(self, time_sim: float | int):
        delta_x = w_head * np.sin(np.deg2rad(self.angle))
        itd = np.round(1000 * delta_x / v_sound, 2)  # ms
        spectro = create_spectro(self.tone, time_sim)
        # sets up the PPGs according to sound spectrum
        for t in range(time_sim):
            for f in range(0, len(spectro) - 1):
                if spectro[f][t] > 0:
                    self.r_ANFs[10 * f : 10 * (f + 1)].set(
                        pulse_times=np.arange(1, time_sim + 1, 1000 / freq[f])
                    )
                    self.l_ANFs[10 * f : 10 * (f + 1)].set(
                        pulse_times=np.around(
                            np.arange(1 + itd, time_sim + itd + 1, 1000 / freq[f]), 2
                        )
                    )

                    if t in np.around(np.arange(0, time_sim, 1000 / freq[f]), 0):
                        self.r_ANFs[10 * f : 10 * (f + 1)].set(
                            activity=int(spectro[f][t] * r_angle_to_level(self.angle))
                        )
                        self.l_ANFs[10 * f : 10 * (f + 1)].set(
                            activity=int(spectro[f][t] * l_angle_to_level(self.angle))
                        )
                    # ANF_noise to parrots
                    # nest.Connect(ANFs_noise, r_ANFs[10 * r : 10 * (r + 1)], "all_to_all")
                    # nest.Connect(ANFs_noise, l_ANFs[10 * r : 10 * (r + 1)], "all_to_all")
            nest.Simulate(1)

    def analyze(self):
        data_r_LSO = self.s_rec_r_LSO.get("events")
        data_l_LSO = self.s_rec_l_LSO.get("events")
        data_r_MSO = self.s_rec_r_MSO.get("events")
        data_l_MSO = self.s_rec_l_MSO.get("events")

        # LSO
        n_spikes_r_lso = len(data_r_LSO["times"])  # / (C.time_sim) * 1000
        n_spikes_l_lso = len(data_l_LSO["times"])  # / (C.time_sim) * 1000

        # MSO
        n_spikes_r_mso = len(data_r_MSO["times"])  # / (C.time_sim) * 1000
        n_spikes_l_mso = len(data_l_MSO["times"])  # / (C.time_sim) * 1000
        result = {
            "n_spikes_r_lso": n_spikes_r_lso,
            "n_spikes_l_lso": n_spikes_l_lso,
            "n_spikes_r_mso": n_spikes_r_mso,
            "n_spikes_l_mso": n_spikes_l_mso,
        }
        return result
