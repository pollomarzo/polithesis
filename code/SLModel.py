import numpy as np
from consts import Parameters
from cochlea import spikes_to_nestgen
from utils import logger
from SpikingModel import SpikingModel
from inspect import getsource
import nest


class SLModel(SpikingModel):
    name = "Simple model v1.0"

    def __init__(self, parameters, binaural_ihc):
        self.params = parameters
        logger.info("creating spike generator according to input IHC response...")
        anfs_per_ear = spikes_to_nestgen(binaural_ihc)
        self.create_network(parameters, anfs_per_ear)
        logger.info("creating rest of network...")
        logger.info("model creation complete.")

    def describe_model(self):
        return {"name": self.name, "networkdef": getsource(self.create_network)}

    def create_network(self, P: Parameters, anfs_per_ear):
        r_ANFs = anfs_per_ear["L"]
        l_ANFs = anfs_per_ear["R"]

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
            "iaf_cond_alpha",
            P.n_MSOs,
            params={"C_m": P.cap_nuclei, "V_reset": P.V_reset},
        )
        l_MSO = nest.Create(
            "iaf_cond_alpha",
            P.n_MSOs,
            params={"C_m": P.cap_nuclei, "V_reset": P.V_reset},
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
                r_ANFs[P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)],
                r_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
            nest.Connect(
                l_ANFs[P.POP_CONN.ANFs2SBCs * i : P.POP_CONN.ANFs2SBCs * (i + 1)],
                l_SBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            )
        # ANFs to GBCs
        for i in range(P.n_GBCs):
            nest.Connect(
                r_ANFs[P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)],
                r_GBCs[i],
                "all_to_all",
                syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            )
            nest.Connect(
                l_ANFs[P.POP_CONN.ANFs2GBCs * i : P.POP_CONN.ANFs2GBCs * (i + 1)],
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
            )  # ipsilateral
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
