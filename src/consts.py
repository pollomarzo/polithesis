from inspect import isfunction
from dataclasses import dataclass, asdict, is_dataclass


@dataclass
class Parameters:
    @dataclass
    class SYN_WEIGHTS:
        ANFs2SBCs: float = 2.0
        ANFs2GBCs: float = 1.0
        SBCs2MSO: float = 1
        SBCs2MSO_inh: float = -30
        SBCs2LSO: float = 16.0
        MNTBCs2MSO: float = -30
        GBCs2MNTBCs: float = 16.0
        MNTBCs2LSO: float = -2.0

    @dataclass
    class POP_CONN:
        ANFs2SBCs: int = 4
        ANFs2GBCs: int = 20

    @dataclass
    class DELAYS:  # ms
        GBCs2MNTBCs: float = 0.45
        SBCs2MSO_exc_ipsi: float = 1
        SBCs2MSO_inh_ipsi: float = 1.3
        SBCs2MSO_exc_contra: float = 1
        MNTBCs2MSO_inh_contra: float = 0.44
        LNTBCs2MSO_inh_ipsi: float = 1.3

    n_ANFs: int = 35000
    SBCs2MSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    SBCs2LSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    n_SBCs: int = int(n_ANFs / POP_CONN.ANFs2SBCs)
    n_GBCs: int = int(n_ANFs / POP_CONN.ANFs2GBCs)
    n_MSOs: int = n_GBCs
    n_inhMSOs: int = n_GBCs
    V_m: float = -70  # mV
    V_reset: float = V_m
    C_m_sbc: int = 3
    C_m_gcb: int = 2
    cap_nuclei: float = 1  # pF

    C_mso: float = 1

    def __init__(self):
        # horrible, but i need each to be an instance so that changes
        # aren't propagated to other instances of Parameters class. it truly is horrifying. sorry
        self.DELAYS = self.DELAYS()
        self.SYN_WEIGHTS = self.SYN_WEIGHTS()
        self.POP_CONN = self.POP_CONN()


@dataclass
class Paths:
    DATA_DIR: str = "../data/"
    IRCAM_DIR: str = DATA_DIR + "IRCAM/"
    IHF_SPIKES_DIR: str = DATA_DIR + "IHF_SPIKES/"
    RESULTS_DIR: str = "../results/"


def save_current_conf(model, params, sound_key, paths=Paths()):
    conf = {}
    __explore_dataclass(conf, "parameters", params)
    __explore_dataclass(conf, "paths", paths)
    conf["model_desc"] = model.describe_model()
    conf["sound_key"] = sound_key
    return conf


def __explore_dataclass(conf, k, v):
    if is_dataclass(v):
        p = asdict(v)
        for kk, vv in v.__dict__.items():
            __explore_dataclass(p, kk, vv)
        conf[k] = p
        return conf

    if not isfunction(v) and not str(k).startswith("__"):
        conf[k] = v
        return conf
