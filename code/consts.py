class Constants:
    class SYN_WEIGHTS:
        ANFs2SBCs = 2.0
        ANFs2GBCs = 1.0
        SBCs2MSO = 1
        SBCs2MSO_inh = [0, -30]
        SBCs2LSO = 16.0
        MNTBCs2MSO = [0, -30]
        GBCs2MNTBCs = 16.0
        MNTBCs2LSO = -2.0

    class POP_CONN:
        ANFs2SBCs = 4
        ANFs2GBCs = 20

    n_ANFs = 35000
    n_battery = len(SYN_WEIGHTS.MNTBCs2MSO)
    SBCs2MSOs = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    SBCs2LSOs = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    n_SBCs = int(n_ANFs / POP_CONN.ANFs2SBCs)
    n_GBCs = int(n_ANFs / POP_CONN.ANFs2GBCs)
    n_MSOs = n_GBCs * n_battery
    V_m = V_reset = -70  # mV
    C_m_sbc = 3
    C_m_gcb = 2
    cap_nuclei = 1  # pF

    C_mso = 1
    delays_mso = [1, 1.3, 1, 0.45, 0.44]  # ms

    time_sim = 2  # ms


class Paths:
    DATA_DIR = "../data/"
    IRCAM_DIR = DATA_DIR + "IRCAM/"
    IHF_SPIKES_DIR = DATA_DIR + "IHF_SPIKES/"
