import numpy as np

from cochleas.anf_utils import AnfResponse, spikes_to_nestgen
from .params import Parameters
from utils.log import logger
from ..SpikingModel import SpikingModel
from inspect import getsource
from utils.custom_sounds import Tone
import nest


class InhModel(SpikingModel):
    name = "Inhibitory model, mso iaf_cond_beta"
    key = "inh_model"

    def __init__(self, params: Parameters, anf: AnfResponse):
        self.params = params
        logger.debug("creating spike generator according to input IHC response...")
        anfs_per_ear = spikes_to_nestgen(anf)
        self.anf = anf
        logger.debug("creating rest of network...")
        self.create_network(params, anfs_per_ear)
        logger.debug("model creation complete.")

    def describe_model(self):
        return {"name": self.name, "networkdef": getsource(self.create_network)}

    def create_network(self, P: Parameters, anfs_per_ear):
        l_ANFs = anfs_per_ear["L"]
        r_ANFs = anfs_per_ear["R"]
        parrot_l_ANFs = nest.Create("parrot_neuron", len(l_ANFs))
        parrot_r_ANFs = nest.Create("parrot_neuron", len(r_ANFs))

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

        self.s_rec_r_ANF = nest.Create("spike_recorder")
        self.s_rec_l_ANF = nest.Create("spike_recorder")
        self.s_rec_r_LSO = nest.Create("spike_recorder")
        self.s_rec_l_LSO = nest.Create("spike_recorder")
        self.s_rec_r_MSO = nest.Create("spike_recorder")
        self.s_rec_l_MSO = nest.Create("spike_recorder")
        self.s_rec_r_SBC = nest.Create("spike_recorder")
        self.s_rec_l_SBC = nest.Create("spike_recorder")
        self.s_rec_r_GBC = nest.Create("spike_recorder")
        self.s_rec_l_GBC = nest.Create("spike_recorder")
        self.s_rec_r_MNTBC = nest.Create("spike_recorder")
        self.s_rec_l_MNTBC = nest.Create("spike_recorder")

        # real ANFs (generators) to parrots
        nest.Connect(r_ANFs, parrot_r_ANFs, "one_to_one")
        nest.Connect(l_ANFs, parrot_l_ANFs, "one_to_one")
        # Devices
        nest.Connect(parrot_r_ANFs, self.s_rec_r_ANF, "all_to_all")
        nest.Connect(parrot_l_ANFs, self.s_rec_l_ANF, "all_to_all")
        nest.Connect(r_MSO, self.s_rec_r_MSO, "all_to_all")
        nest.Connect(l_MSO, self.s_rec_l_MSO, "all_to_all")
        nest.Connect(r_LSO, self.s_rec_r_LSO, "all_to_all")
        nest.Connect(l_LSO, self.s_rec_l_LSO, "all_to_all")
        nest.Connect(r_SBCs, self.s_rec_r_SBC, "all_to_all")
        nest.Connect(l_SBCs, self.s_rec_l_SBC, "all_to_all")
        nest.Connect(r_GBCs, self.s_rec_r_GBC, "all_to_all")
        nest.Connect(l_GBCs, self.s_rec_l_GBC, "all_to_all")
        nest.Connect(r_MNTBCs, self.s_rec_r_MNTBC, "all_to_all")
        nest.Connect(l_MNTBCs, self.s_rec_l_MNTBC, "all_to_all")

        # ANFs to SBCs
        for i in range(P.n_SBCs):
            nest.Connect(
                parrot_r_ANFs[
                    P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)
                ],
                r_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
            nest.Connect(
                parrot_l_ANFs[
                    P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)
                ],
                l_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
        # ANFs to GBCs
        for i in range(P.n_GBCs):
            nest.Connect(
                parrot_r_ANFs[
                    P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)
                ],
                r_GBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            )
            nest.Connect(
                parrot_l_ANFs[
                    P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)
                ],
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

    def simulate(self, time: float | int):
        nest.Simulate(time)

    def analyze(self):
        # LSO
        # n_spikes_r_lso = len(data_r_LSO["times"])  # / (C.time_sim) * 1000
        # n_spikes_l_lso = len(data_l_LSO["times"])  # / (C.time_sim) * 1000

        result = {"L": {}, "R": {}}
        for pop_name, pop_data_l, pop_data_r in zip(
            ["ANF", "LSO", "MSO", "GBC", "SBC", "MNTBC"],
            [
                self.s_rec_l_ANF.get("events"),
                self.s_rec_l_LSO.get("events"),
                self.s_rec_l_MSO.get("events"),
                self.s_rec_l_GBC.get("events"),
                self.s_rec_l_SBC.get("events"),
                self.s_rec_l_MNTBC.get("events"),
            ],
            [
                self.s_rec_r_ANF.get("events"),
                self.s_rec_r_LSO.get("events"),
                self.s_rec_r_MSO.get("events"),
                self.s_rec_r_GBC.get("events"),
                self.s_rec_r_SBC.get("events"),
                self.s_rec_r_MNTBC.get("events"),
            ],
        ):
            if pop_name in self.params.CONFIG.STORE_POPS:
                result["L"][pop_name] = pop_data_l
                result["R"][pop_name] = pop_data_r

        return result
