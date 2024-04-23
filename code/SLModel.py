import numpy as np
import nest
from consts import Constants as C


class SLModel:
    def __init__(self, inputs):
        r_ANFs = inputs[0]
        l_ANFs = inputs[1]

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

        r_LSO = nest.Create(
            "iaf_cond_alpha",
            C.n_GBCs,
            params={"C_m": C.cap_nuclei, "V_reset": C.V_reset},
        )

        l_LSO = nest.Create(
            "iaf_cond_alpha",
            C.n_GBCs,
            params={"C_m": C.cap_nuclei, "V_m": C.V_m, "V_reset": C.V_reset},
        )

        # ANFs_noise = nest.Create('poisson_generator',1,
        #                  params = {'rate':noise_rate})

        s_rec_r = nest.Create("spike_recorder")
        s_rec_l = nest.Create("spike_recorder")

        # Connections

        # Devices
        nest.Connect(r_ANFs, s_rec_r, "all_to_all")
        nest.Connect(l_ANFs, s_rec_l, "all_to_all")

        nest.Connect(r_SBCs, s_rec_r, "all_to_all")
        nest.Connect(l_SBCs, s_rec_l, "all_to_all")

        nest.Connect(r_GBCs, s_rec_r, "all_to_all")
        nest.Connect(l_GBCs, s_rec_l, "all_to_all")

        nest.Connect(r_MNTBCs, s_rec_r, "all_to_all")
        nest.Connect(l_MNTBCs, s_rec_l, "all_to_all")

        nest.Connect(r_MSO, s_rec_r, "all_to_all")
        nest.Connect(l_MSO, s_rec_l, "all_to_all")

        nest.Connect(r_LSO, s_rec_r, "all_to_all")
        nest.Connect(l_LSO, s_rec_l, "all_to_all")

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
        for i in range(C.n_GBCs):
            for j in range(C.n_battery):

                # Right MSO
                # From SBCs (excitation):
                nest.Connect(
                    r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    r_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO,
                        "delay": C.delays_mso[0],
                    },
                )  # ipsilateral
                nest.Connect(
                    l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    r_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO,
                        "delay": C.delays_mso[2],
                    },
                )  # contralateral
                # From LNTBCs (inhibition)
                nest.Connect(
                    r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    r_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO_inh[j],
                        "delay": C.delays_mso[1],
                    },
                )  # ipsilateral
                # From MNTBCs (inhibition)
                nest.Connect(
                    l_MNTBCs[i],
                    r_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.MNTBCs2MSO[j],
                        "delay": C.delays_mso[4],
                    },
                )  # contralateral

                # Left MSO
                # From SBCs (excitation):
                nest.Connect(
                    l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    l_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO,
                        "delay": C.delays_mso[0],
                    },
                )  # ipsilateral
                nest.Connect(
                    r_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    l_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO,
                        "delay": C.delays_mso[2],
                    },
                )  # contralateral
                # From LNTBCs (inhibition)
                nest.Connect(
                    l_SBCs[C.SBCs2MSOs * i : C.SBCs2MSOs * (i + 1)],
                    l_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.SBCs2MSO_inh[j],
                        "delay": C.delays_mso[1],
                    },
                )  # ipsilateral
                # From MNTBCs (inhibition)
                nest.Connect(
                    r_MNTBCs[i],
                    l_MSO[i * C.n_battery + j],
                    "all_to_all",
                    syn_spec={
                        "weight": C.SYN_WEIGHTS.MNTBCs2MSO[j],
                        "delay": C.delays_mso[4],
                    },
                )  # contralateral

        # LSO
        for i in range(0, C.n_GBCs):
            nest.Connect(
                r_SBCs[C.SBCs2LSOs * i : C.SBCs2LSOs * (i + 1)],
                r_LSO[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.SBCs2LSO},
            )
            nest.Connect(
                l_SBCs[C.SBCs2LSOs * i : C.SBCs2LSOs * (i + 1)],
                l_LSO[i],
                "all_to_all",
                syn_spec={"weight": C.SYN_WEIGHTS.SBCs2LSO},
            )

        nest.Connect(
            r_MNTBCs, l_LSO, "one_to_one", syn_spec={"weight": C.SYN_WEIGHTS.MNTBCs2LSO}
        )
        nest.Connect(
            l_MNTBCs, r_LSO, "one_to_one", syn_spec={"weight": C.SYN_WEIGHTS.MNTBCs2LSO}
        )

    def simulate(self, time: float | int):
        nest.Simulate(time)
