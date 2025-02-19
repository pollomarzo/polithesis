from dataclasses import dataclass, field
from cochleas.consts import ITD_REMOVAL_STRAT

@dataclass
class Parameters:
    key: str = "default_params"

    cochlea: dict[str, dict[str, float]] = field(
        default_factory=lambda: (
            {
                "gammatone": {
                    "hrtf_params": {
                        "subj_number": 1,
                        "ild_only": False,
                        "itd_remove_strategy": ITD_REMOVAL_STRAT.COMPUTED,
                    },
                    "noise_factor": 0.3,
                    "refractory_period": 1,  # ms
                    "amplif_factor": 7,
                },
                "ppg": {
                    "nest": {
                        "resolution": 0.1,
                        "rng_seed": 42,
                        "total_num_virtual_procs": 16,
                    }
                },
                "TanCarney": {
                    "hrtf_params": {
                        "subj_number": 1,
                        "itd_remove_strategy": ITD_REMOVAL_STRAT.ESTIMATE_FROM_HRTF,
                    },
                    "cochlea_params": None,
                    "rng_seed": 42,
                    "omni_noise_level": 0,
                },
            }
        )
    )

    @dataclass
    class CONFIG:
        STORE_POPS: set = field(
            default_factory=lambda: set(
                # ["LSO", "MSO", "ANF", "SBC", "GBC", "LNTBC", "MNTBC"]
                []  # all
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
    class POP_CONN:
        ANFs2SBCs: int = 4
        ANFs2GBCs: int = 20

    @dataclass
    class DELAYS:  # ms
        # GBCs2MNTBCs: float = 0.45
        # GBCs2LNTBCs: float = 0.45
        # SBCs2MSO_exc_ipsi: float = 2
        # SBCs2MSO_exc_contra: float = 2

        # def __init__(self):
        #     self._DELTA_IPSI: float = 0.2
        #     self._DELTA_CONTRA: float = -0.4

        # @property
        # def DELTA_IPSI(self):
        #     return self._DELTA_IPSI

        # @DELTA_IPSI.setter
        # def DELTA_IPSI(self, value):
        #     self._DELTA_IPSI = value

        # @property
        # def DELTA_CONTRA(self):
        #     return self._DELTA_CONTRA

        # @DELTA_CONTRA.setter
        # def DELTA_CONTRA(self, value):
        #     self._DELTA_CONTRA = value

        # @property
        # def LNTBCs2MSO_inh_ipsi(self):
        #     return 1.44 + self.DELTA_IPSI

        # @property
        # def MNTBCs2MSO_inh_contra(self):
        #     return 1.44 + self.DELTA_CONTRA

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

    @dataclass
    class SYN_WEIGHTS:
        ANFs2SBCs: float = 35.0
        ANFs2GBCs: float = 7.0
        GBCs2LNTBCs: float = 20.0
        GBCs2MNTBCs: float = 30.0
        SBCs2LSO: float = 5.0
        MNTBCs2LSO: float = -20.0
        MNTBCs2MSO: float = -40.0
        LNTBCs2MSO: float = -40.0
        SBCs2MSO: float = 9.0

    @dataclass
    class MEMB_CAPS:
        # default: float = 250
        SBC: int = 15
        GBC: int = 15
        MNTBC: int = 15
        LNTBC: int = 15
        MSO: float = 20
        LSO: float = 30
        # default leak conductance (g_L) at 16.6667 nS gives with C_m = 1 pF:
        # Membrane time constant τ = C_m/g_L ≈ 0.06 ms
        # if C_m = 15 pF => τ ≈ 0.9 ms

    @dataclass
    class G_LEAK:
        # default: float = 16.67
        SBC: int = 40
        GBC: int = 25
        LNTBC: int = 25
        MNTBC: int = 25
        MSO: float = 80
        LSO: float = 20

    def __post_init__(self):
        # horrible, but i need each to be an instance so that changes
        # aren't propagated to other instances of Parameters class. it truly is horrifying. sorry
        self.CONFIG = self.CONFIG()
        self.DELAYS = self.DELAYS()
        self.SYN_WEIGHTS = self.SYN_WEIGHTS()
        self.POP_CONN = self.POP_CONN()
        self.MSO_TAUS = self.MSO_TAUS()
        self.MEMB_CAPS = self.MEMB_CAPS()
        self.G_LEAK = self.G_LEAK()


"""
iaf_cond_alpha default params
{'C_m': 250.0, -> always too big. try with a sensible 10pF
 'Ca': 0.0,
 'E_L': -70.0,
 'E_ex': 0.0,
 'E_in': -85.0,
 'I_e': 0.0,
 'V_m': -70.0,
 'V_reset': -60.0,
 'V_th': -55.0, -> maybe we can try -57... 'might help maintain selectivity for coincident inputs in MSO while still allowing LSO to respond to intensity differences'???
 'archiver_length': 0,
 'available': (0,),
 'beta_Ca': 0.001,
 'capacity': (0,),
 'dg_ex': 0.0,
 'dg_in': 0.0,
 'element_type': 'neuron',
 'elementsize': 688,
 'frozen': False,
 'g_L': 16.6667, -> try 166.67 to compensate for higher C_m
 'g_ex': 0.0,
 'g_in': 0.0,
 'global_id': 0,
 'instantiations': (0,),
 'local': True,
 'model': 'iaf_cond_alpha',
 'model_id': 33,
 'node_uses_wfr': False,
 'post_trace': 0.0,
 'recordables': ('g_ex', 'g_in', 't_ref_remaining', 'V_m'),
 'synaptic_elements': {},
 't_ref': 2.0,
 't_spike': -1.0,
 'tau_Ca': 10000.0,
 'tau_minus': 20.0,
 'tau_minus_triplet': 110.0,
 'tau_syn_ex': 0.2,
 'tau_syn_in': 2.0,
 'thread': -1,
 'thread_local_id': -1,
 'type_id': 'iaf_cond_alpha',
 'vp': -1}
"""
