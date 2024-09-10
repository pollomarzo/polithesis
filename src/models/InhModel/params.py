from dataclasses import dataclass, field


@dataclass
class Parameters:
    key: str = "default_params"

    cochlea: dict[str, dict[str, float]] = field(
        default_factory=lambda: (
            {
                "realistic": {
                    "subj_number": 1,
                    "noise_factor": 0.2,
                    "refractory_period": 1,  # ms
                },
                "ppg": {
                    "nest": {
                        "resolution": 0.1,
                        "rng_seed": 42,
                        "total_num_virtual_procs": 16,
                    }
                },
            }
        )
    )

    @dataclass
    class CONFIG:
        STORE_POPS: set = field(
            default_factory=lambda: set(
                ["LSO", "MSO", "ANF", "SBC", "GBC", "LNTBC", "MNTBC"]
            )
        )
        NEST_KERNEL_PARAMS: dict = field(
            default_factory=lambda: {
                "resolution": 0.1,
                "rng_seed": 42,
                "total_num_virtual_procs": 16,
            }
        )

    @dataclass
    class SYN_WEIGHTS:
        ANFs2SBCs: float = 16.0
        ANFs2GBCs: float = 8.0
        GBCs2LNTBCs: float = 16.0
        GBCs2MNTBCs: float = 16.0
        MNTBCs2MSO: float = -5.0
        MNTBCs2LSO: float = -12.0
        SBCs2LSO: float = 4.0
        SBCs2MSO: float = 1
        LNTBCs2MSO: float = -5.0

    @dataclass
    class POP_CONN:
        ANFs2SBCs: int = 4
        ANFs2GBCs: int = 20

    @dataclass
    class DELAYS:  # ms
        DELTA_IPSI: float = 0.2
        DELTA_CONTRA: float = -0.4
        GBCs2MNTBCs: float = 0.45
        GBCs2LNTBCs: float = 0.45
        SBCs2MSO_exc_ipsi: float = 2  # MSO ipsilateral excitation
        SBCs2MSO_exc_contra: float = 2  # MSO contralateral excitation
        LNTBCs2MSO_inh_ipsi: float = (
            1.44 + DELTA_IPSI
        )  # MSO ipsilateral inhibition (mirrors SBC)
        # SBCs2MSO_inh_ipsi: float = 1  # doesn't exist, MSO ipsilateral inhibition
        MNTBCs2MSO_inh_contra: float = (
            1.44 + DELTA_CONTRA
        )  # MSO contralateral inhibition

    @dataclass
    class MSO_TAUS:
        rise_ex: float = 0.2
        rise_in: float = 0.2
        decay_ex: float = 0.5
        decay_in: float = 1.5

    n_ANFs: int = 35000
    SBCs2MSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    SBCs2LSOs: int = int(POP_CONN.ANFs2GBCs / POP_CONN.ANFs2SBCs)
    n_SBCs: int = int(n_ANFs / POP_CONN.ANFs2SBCs)
    n_GBCs: int = int(n_ANFs / POP_CONN.ANFs2GBCs)
    n_MSOs: int = n_GBCs
    n_LSOs: int = n_GBCs
    n_inhMSOs: int = n_GBCs
    V_m: float = -70  # mV
    V_reset: float = V_m
    C_m_sbc: int = 1
    C_m_gcb: int = 1
    cap_nuclei: float = 1  # pF

    C_mso: float = 1

    def __post_init__(self):
        # horrible, but i need each to be an instance so that changes
        # aren't propagated to other instances of Parameters class. it truly is horrifying. sorry
        self.CONFIG = self.CONFIG()
        self.DELAYS = self.DELAYS()
        self.SYN_WEIGHTS = self.SYN_WEIGHTS()
        self.POP_CONN = self.POP_CONN()
        self.MSO_TAUS = self.MSO_TAUS()
