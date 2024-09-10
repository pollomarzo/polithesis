import numpy as np

from cochleas.anf_utils import AnfResponse, spikes_to_nestgen
from .params import Parameters
from utils.log import logger
from ..SpikingModel import SpikingModel
from inspect import getsource
from utils.custom_sounds import Tone
import nest
from utils.CustomConnections import connect

# import nest


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
        r_LNTBCs = nest.Create(
            "iaf_cond_alpha", P.n_GBCs, params={"C_m": P.C_m_gcb, "V_reset": P.V_reset}
        )
        l_LNTBCs = nest.Create(
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
            P.n_LSOs,
            params={"C_m": P.cap_nuclei, "V_m": P.V_m, "V_reset": P.V_reset},
        )
        l_LSO = nest.Create(
            "iaf_cond_alpha",
            P.n_LSOs,
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
        self.s_rec_r_LNTBC = nest.Create("spike_recorder")
        self.s_rec_l_LNTBC = nest.Create("spike_recorder")
        self.s_rec_r_MNTBC = nest.Create("spike_recorder")
        self.s_rec_l_MNTBC = nest.Create("spike_recorder")

        # real ANFs (generators) to parrots
        connect(r_ANFs, parrot_r_ANFs, "one_to_one")
        connect(l_ANFs, parrot_l_ANFs, "one_to_one")
        # Devices
        connect(parrot_r_ANFs, self.s_rec_r_ANF, "all_to_all")
        connect(parrot_l_ANFs, self.s_rec_l_ANF, "all_to_all")
        connect(r_MSO, self.s_rec_r_MSO, "all_to_all")
        connect(l_MSO, self.s_rec_l_MSO, "all_to_all")
        connect(r_LSO, self.s_rec_r_LSO, "all_to_all")
        connect(l_LSO, self.s_rec_l_LSO, "all_to_all")
        connect(r_SBCs, self.s_rec_r_SBC, "all_to_all")
        connect(l_SBCs, self.s_rec_l_SBC, "all_to_all")
        connect(r_GBCs, self.s_rec_r_GBC, "all_to_all")
        connect(l_GBCs, self.s_rec_l_GBC, "all_to_all")
        connect(r_LNTBCs, self.s_rec_r_LNTBC, "all_to_all")
        connect(l_LNTBCs, self.s_rec_l_LNTBC, "all_to_all")
        connect(r_MNTBCs, self.s_rec_r_MNTBC, "all_to_all")
        connect(l_MNTBCs, self.s_rec_l_MNTBC, "all_to_all")

        # ANFs to SBCs
        connect(
            parrot_r_ANFs,
            r_SBCs,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            num_sources=P.POP_CONN.ANFs2SBCs,
        )
        connect(
            parrot_l_ANFs,
            l_SBCs,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            num_sources=P.POP_CONN.ANFs2SBCs,
        )

        # ANFs to GBCs
        connect(
            parrot_r_ANFs,
            r_GBCs,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            num_sources=P.POP_CONN.ANFs2GBCs,
        )

        connect(
            parrot_l_ANFs,
            l_GBCs,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            num_sources=P.POP_CONN.ANFs2GBCs,
        )

        # GBCs to LNTBCs
        connect(
            r_GBCs,
            r_LNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2LNTBCs,
                "delay": P.DELAYS.GBCs2LNTBCs,
            },
        )
        connect(
            l_GBCs,
            l_LNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2LNTBCs,
                "delay": P.DELAYS.GBCs2LNTBCs,
            },
        )
        # GBCs to MNTBCs
        connect(
            r_GBCs,
            l_MNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2MNTBCs,
                "delay": P.DELAYS.GBCs2MNTBCs,
            },
        )
        connect(
            l_GBCs,
            r_MNTBCs,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2MNTBCs,
                "delay": P.DELAYS.GBCs2MNTBCs,
            },
        )

        # MSO
        # From SBCs (excitation):
        # r_MSO
        #       ipsi
        connect(
            r_SBCs,
            r_MSO,
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
            },
            num_sources=P.SBCs2MSOs,
        )
        #       contra
        connect(
            l_SBCs,
            r_MSO,
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_contra,
            },
            num_sources=P.SBCs2MSOs,
        )
        # l_MSO
        #       ipsi
        connect(
            l_SBCs,
            l_MSO,
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
            },
            num_sources=P.SBCs2MSOs,
        )
        #       contra
        connect(
            r_SBCs,
            l_MSO,
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_contra,
            },
            num_sources=P.SBCs2MSOs,
        )
        # From LNTBCs (inhibition), ipsi
        connect(
            r_LNTBCs,
            r_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.LNTBCs2MSO,
                "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
            },
        )
        # From MNTBCs (inhibition) contra
        connect(
            r_MNTBCs,
            r_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )
        # From LNTBCs (inhibition) ipsi
        connect(
            l_LNTBCs,
            l_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.LNTBCs2MSO,
                "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
            },
        )
        # From MNTBCs (inhibition) contra
        connect(
            l_MNTBCs,
            l_MSO,
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )

        # LSO
        connect(
            r_SBCs,
            r_LSO,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            num_sources=P.SBCs2LSOs,
        )
        connect(
            l_SBCs,
            l_LSO,
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            num_sources=P.SBCs2LSOs,
        )

        connect(
            r_MNTBCs,
            r_LSO,
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )
        connect(
            l_MNTBCs,
            l_LSO,
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )

    def simulate(self, time: float | int):
        nest.Simulate(time)

    def analyze(self):
        result = {"L": {}, "R": {}}
        for pop_name, pop_data_l, pop_data_r in zip(
            ["ANF", "LSO", "MSO", "GBC", "SBC", "LNTBC", "MNTBC"],
            [
                self.s_rec_l_ANF.get("events"),
                self.s_rec_l_LSO.get("events"),
                self.s_rec_l_MSO.get("events"),
                self.s_rec_l_GBC.get("events"),
                self.s_rec_l_SBC.get("events"),
                self.s_rec_l_LNTBC.get("events"),
                self.s_rec_l_MNTBC.get("events"),
            ],
            [
                self.s_rec_r_ANF.get("events"),
                self.s_rec_r_LSO.get("events"),
                self.s_rec_r_MSO.get("events"),
                self.s_rec_r_GBC.get("events"),
                self.s_rec_r_SBC.get("events"),
                self.s_rec_r_LNTBC.get("events"),
                self.s_rec_r_MNTBC.get("events"),
            ],
        ):
            if (
                pop_name in self.params.CONFIG.STORE_POPS
                or self.params.CONFIG.STORE_POPS == []
            ):
                result["L"][pop_name] = pop_data_l
                result["R"][pop_name] = pop_data_r

        return result
