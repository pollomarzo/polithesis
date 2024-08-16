from dataclasses import dataclass, field


@dataclass
class Parameters:
    key = "default_params"

    @dataclass
    class CONFIG:
        STORE_POPS: set = field(
            default_factory=lambda: set(["LSO", "MSO", "ANF", "SBC", "GBC", "MNTBC"])
        )
        NEST_KERNEL_PARAMS: dict = field(
            default_factory=lambda: {"resolution": 0.1, "rng_seed": 42}
        )

    @dataclass
    class SYN_WEIGHTS:
        ANFs2SBCs: float = 16.0
        ANFs2GBCs: float = 8.0
        SBCs2MSO: float = 1
        SBCs2MSO_inh: float = -30
        SBCs2LSO: float = 8.0
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

    @dataclass
    class MSO_TAUS:
        rise_ex: float = 0.2
        rise_in: float = 0.1
        decay_ex: float = 0.5
        decay_in: float = 0.1

    n_ANFs: int = 35000
    SBCs2MSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    SBCs2LSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    n_SBCs: int = int(n_ANFs / POP_CONN.ANFs2SBCs)
    n_GBCs: int = int(n_ANFs / POP_CONN.ANFs2GBCs)
    n_MSOs: int = n_GBCs
    n_inhMSOs: int = n_GBCs
    V_m: float = -70  # mV
    V_reset: float = V_m
    C_m_sbc: int = 1
    C_m_gcb: int = 1
    cap_nuclei: float = 1  # pF

    C_mso: float = 1

    def __init__(self):
        # horrible, but i need each to be an instance so that changes
        # aren't propagated to other instances of Parameters class. it truly is horrifying. sorry
        self.CONFIG = self.CONFIG()
        self.DELAYS = self.DELAYS()
        self.SYN_WEIGHTS = self.SYN_WEIGHTS()
        self.POP_CONN = self.POP_CONN()
        self.MSO_TAUS = self.MSO_TAUS()
