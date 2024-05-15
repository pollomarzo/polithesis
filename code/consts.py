from inspect import isclass, isfunction


class Parameters:
    class SYN_WEIGHTS:
        ANFs2SBCs = 2.0
        ANFs2GBCs = 1.0
        SBCs2MSO = 1
        SBCs2MSO_inh = -30
        SBCs2MSO_noinh = 0
        SBCs2LSO = 16.0
        MNTBCs2MSO = -30
        MNTBCs2MSO_noinh = 0
        GBCs2MNTBCs = 16.0
        MNTBCs2LSO = -2.0

    class POP_CONN:
        ANFs2SBCs = 4
        ANFs2GBCs = 20

    n_ANFs = 35000
    SBCs2MSOs = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    SBCs2LSOs = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    n_SBCs = int(n_ANFs / POP_CONN.ANFs2SBCs)
    n_GBCs = int(n_ANFs / POP_CONN.ANFs2GBCs)
    n_MSOs = n_GBCs
    n_inhMSOs = n_GBCs
    V_m = V_reset = -70  # mV
    C_m_sbc = 3
    C_m_gcb = 2
    cap_nuclei = 1  # pF

    C_mso = 1

    class DELAYS:  # ms
        GBCs2MNTBCs = 0.45
        SBCs2MSO_exc_ipsi = 1
        SBCs2MSO_inh_ipsi = 1.3
        SBCs2MSO_exc_contra = 1
        MNTBCs2MSO_inh_contra = 0.44
        LNTBCs2MSO_inh_ipsi = 1.3


class Paths:
    DATA_DIR = "../data/"
    IRCAM_DIR = DATA_DIR + "IRCAM/"
    IHF_SPIKES_DIR = DATA_DIR + "IHF_SPIKES/"
    RESULTS_DIR = "../results/"


def save_current_conf(model):
    conf = {}
    __explore_class(conf, "constants", Parameters)
    __explore_class(conf, "paths", Paths)
    conf["model_desc"] = model.describe_model()
    return conf


def __explore_class(conf, k, v):
    if isclass(v):
        tocheck = {}
        for kk, vv in v.__dict__.items():
            __explore_class(tocheck, kk, vv)
        conf[k] = tocheck
        return conf

    if not isfunction(v) and not str(k).startswith("__"):
        conf[k] = v
        return conf
