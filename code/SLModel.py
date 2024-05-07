import numpy as np
from consts import Constants as C
from cochlea import spikes_to_nestgen
from utils import logger
import nest


class SLModel:
    def __init__(self, binaural_ihc):
        logger.info("creating spike generator according to input IHC response...")
        anfs_per_ear = spikes_to_nestgen(binaural_ihc)

        logger.info("creating rest of network...")
        r_ANFs = anfs_per_ear["L"]
        l_ANFs = anfs_per_ear["R"]

        r_SBCs = nest.Create(
            "iaf_cond_alpha", C.n_SBCs, params={"C_m": C.C_m_sbc, "V_reset": C.V_reset}
        )

        l_SBCs = nest.Create(
            "iaf_cond_alpha", C.n_SBCs, params={"C_m": C.C_m_sbc, "V_reset": C.V_reset}
        )

        r_GBCs = nest.Create(
            "iaf_cond_alpha", C.n_GBCs, params={"C_m": C.C_m_gcb, "V_reset": C.V_reset}
        )

        l_GBCs = nest.Create(
            "iaf_cond_alpha", C.n_GBCs, params={"C_m": C.C_m_gcb, "V_reset": C.V_reset}
        )

        r_MNTBCs = nest.Create(
            "iaf_cond_alpha", C.n_GBCs, params={"C_m": C.C_m_gcb, "V_reset": C.V_reset}
        )

        l_MNTBCs = nest.Create(
            "iaf_cond_alpha", C.n_GBCs, params={"C_m": C.C_m_gcb, "V_reset": C.V_reset}
        )

        r_MSO = nest.Create(
            "iaf_cond_alpha",
            C.n_MSOs,
            params={"C_m": C.cap_nuclei, "V_reset": C.V_reset},
        )

        l_MSO = nest.Create(
            "iaf_cond_alpha",
            C.n_MSOs,
            params={"C_m": C.cap_nuclei, "V_reset": C.V_reset},
        )

        self.r_LSO = nest.Create(
            "iaf_cond_alpha",
            C.n_GBCs,
            params={"C_m": C.cap_nuclei, "V_reset": C.V_reset},
        )

        self.l_LSO = nest.Create(
            "iaf_cond_alpha",
            C.n_GBCs,
            params={"C_m": C.cap_nuclei, "V_m": C.V_m, "V_reset": C.V_reset},
        )

        # ANFs_noise = nest.Create('poisson_generator',1,
        #                  params = {'rate':noise_rate})

        self.s_rec_r_LSO = nest.Create("spike_recorder")
        self.s_rec_l_LSO = nest.Create("spike_recorder")
        self.s_rec_r_MSO = nest.Create("spike_recorder")
        self.s_rec_l_MSO = nest.Create("spike_recorder")

        # Devices
        nest.Connect(r_MSO, self.s_rec_r_LSO, "all_to_all")
        nest.Connect(l_MSO, self.s_rec_l_LSO, "all_to_all")

        nest.Connect(self.r_LSO, self.s_rec_r_MSO, "all_to_all")
        nest.Connect(self.l_LSO, self.s_rec_l_MSO, "all_to_all")

        # ANFs to SBCs
        for i in range(C.n_SBCs):
            nest.Connect(
                r_ANFs[C.POP_CONN.ANFs2SBCs * i : C.POP_CONN.ANFs2SBCs * (i + 1)],
                r_SBCs[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.ANFs2SBCs},
            )
            nest.Connect(
                l_ANFs[C.POP_CONN.ANFs2SBCs * i : C.POP_CONN.ANFs2SBCs * (i + 1)],
                l_SBCs[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.ANFs2SBCs},
            )
        # ANFs to GBCs
        for i in range(C.n_GBCs):
            nest.Connect(
                r_ANFs[C.POP_CONN.ANFs2GBCs * i : C.POP_CONN.ANFs2GBCs * (i + 1)],
                r_GBCs[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.ANFs2GBCs},
            )
            nest.Connect(
                l_ANFs[C.POP_CONN.ANFs2GBCs * i : C.POP_CONN.ANFs2GBCs * (i + 1)],
                l_GBCs[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.ANFs2GBCs},
            )

        # GBCs to MNTBCs
        nest.Connect(
            r_GBCs,
            r_MNTBCs,
            "one_to_one",
            syn_spec={"weight": C.SYN_WEIGHTS.GBCs2MNTBCs, "delay": C.delays_mso[3]},
        )
        nest.Connect(
            l_GBCs,
            l_MNTBCs,
            "one_to_one",
            syn_spec={"weight": C.SYN_WEIGHTS.GBCs2MNTBCs, "delay": C.delays_mso[3]},
        )

        # MSO
        for i in range(C.n_MSOs):
            # From SBCs (excitation):
            nest.Connect(
                r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO,
                    "delay": C.delays_mso[0],
                },
            )  # ipsilateral
            nest.Connect(
                l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO,
                    "delay": C.delays_mso[2],
                },
            )  # contralateral
            # From LNTBCs (inhibition)
            nest.Connect(
                r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                r_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO_inh,
                    "delay": C.delays_mso[1],
                },
            )  # ipsilateral

            # From SBCs (excitation):
            nest.Connect(
                l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO,
                    "delay": C.delays_mso[0],
                },
            )  # ipsilateral
            nest.Connect(
                r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO,
                    "delay": C.delays_mso[2],
                },
            )  # contralateral
            # From LNTBCs (inhibition)
            nest.Connect(
                l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                l_MSO[i],
                "all_to_all",
                syn_spec={
                    "weight": C.SYN_WEIGHTS.SBCs2MSO_inh,
                    "delay": C.delays_mso[1],
                },
            )  # ipsilateral

        # From MNTBCs (inhibition)
        nest.Connect(
            l_MNTBCs,
            r_MSO,
            "one_to_one",
            syn_spec={
                "weight": C.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": C.delays_mso[4],
            },
        )  # contralateral
        # From MNTBCs (inhibition)
        nest.Connect(
            r_MNTBCs,
            l_MSO,
            "one_to_one",
            syn_spec={
                "weight": C.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": C.delays_mso[4],
            },
        )  # contralateral

        # LSO
        for i in range(0, C.n_GBCs):
            nest.Connect(
                r_SBCs[C.SBCs2LSOs * i : C.SBCs2LSOs * (i + 1)],
                self.r_LSO[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.SBCs2LSO},
            )
            nest.Connect(
                l_SBCs[C.SBCs2LSOs * i : C.SBCs2LSOs * (i + 1)],
                self.l_LSO[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.SBCs2LSO},
            )

        nest.Connect(
            r_MNTBCs,
            self.l_LSO,
            "one_to_one",
            syn_spec={"weight": C.SYN_WEIGHTS.MNTBCs2LSO},
        )
        nest.Connect(
            l_MNTBCs,
            self.r_LSO,
            "one_to_one",
            syn_spec={"weight": C.SYN_WEIGHTS.MNTBCs2LSO},
        )
        logger.info("model creation complete.")

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

        # ac_r_lso = np.unique(
        #     data_r["senders"][np.where((data_r["senders"] >= self.id_r_LSO1))]
        # )
        # ac_l_lso = np.unique(
        #     data_l["senders"][np.where((data_l["senders"] >= self.id_l_LSO1))]
        # )

        # MSO
        n_spikes_r_mso = len(data_r_MSO["times"])  # / (C.time_sim) * 1000
        n_spikes_l_mso = len(data_l_MSO["times"])  # / (C.time_sim) * 1000

        return (n_spikes_r_lso, n_spikes_l_lso, n_spikes_r_mso, n_spikes_l_mso)
