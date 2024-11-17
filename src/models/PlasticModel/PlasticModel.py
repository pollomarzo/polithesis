from inspect import getsource

import nest
import numpy as np

from cochleas.anf_utils import AnfResponse, spikes_to_nestgen
from utils.custom_sounds import Tone
from utils.CustomConnections import connect
from utils.log import logger, tqdm

from ..SpikingModel import SpikingModel
from .params import Parameters


class InhModel(SpikingModel):
    name = "Plastc model, mso iaf_cond_beta"
    key = "plastic"
    RESULTS_VERSION_NUMBER = (
        3
        # 2 -> include ICC;
        # 3 -> include LSO, MSO, ICC global IDs
    )

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
        self.pops = {"L": {"ANF": anfs_per_ear["L"]}, "R": {"ANF": anfs_per_ear["R"]}}
        self.recs = {"L": {}, "R": {}}
        for side in ["L", "R"]:
            self.pops[side]["ANF"] = anfs_per_ear[side]
            self.pops[side]["parrot_ANF"] = nest.Create(
                "parrot_neuron", len(self.pops[side]["ANF"])
            )
            self.pops[side]["SBC"] = nest.Create(
                "iaf_cond_alpha",
                P.n_SBCs,
                params={
                    "C_m": P.MEMB_CAPS.SBC,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.SBC,
                },
            )
            self.pops[side]["GBC"] = nest.Create(
                "iaf_cond_alpha",
                P.n_GBCs,
                params={
                    "C_m": P.MEMB_CAPS.GBC,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.GBC,
                },
            )
            self.pops[side]["LNTBC"] = nest.Create(
                "iaf_cond_alpha",
                P.n_GBCs,
                params={
                    "C_m": P.MEMB_CAPS.GBC,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.LNTBC,
                },
            )
            self.pops[side]["MNTBC"] = nest.Create(
                "iaf_cond_alpha",
                P.n_GBCs,
                params={
                    "C_m": P.MEMB_CAPS.GBC,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.MNTBC,
                },
            )
            self.pops[side]["MSO"] = nest.Create(
                "iaf_cond_beta",
                P.n_MSOs,
                params={
                    "C_m": P.MEMB_CAPS.MSO,
                    "tau_rise_ex": P.MSO_TAUS.rise_ex,
                    "tau_rise_in": P.MSO_TAUS.rise_in,
                    "tau_decay_ex": P.MSO_TAUS.decay_ex,
                    "tau_decay_in": P.MSO_TAUS.decay_in,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.MSO,
                },
            )
            self.pops[side]["LSO"] = nest.Create(
                "iaf_cond_alpha",
                P.n_LSOs,
                params={
                    "C_m": P.MEMB_CAPS.LSO,
                    "V_m": P.V_m,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.LSO,
                },
            )
            self.pops[side]["ICC"] = nest.Create(
                "iaf_cond_alpha",
                P.n_LSOs,
                params={
                    "C_m": P.MEMB_CAPS.ICC,
                    "V_m": P.V_m,
                    "V_reset": P.V_reset,
                    "g_L": P.G_LEAK.ICC,
                },
            )
        for side in ["L", "R"]:
            for pop in self.pops[side].keys():
                self.recs[side][pop] = nest.Create("spike_recorder")
                connect(self.pops[side][pop], self.recs[side][pop], "all_to_all")

        # real ANFs (generators) to parrots
        connect(self.pops["R"]["ANF"], self.pops["R"]["parrot_ANF"], "one_to_one")
        connect(self.pops["L"]["ANF"], self.pops["L"]["parrot_ANF"], "one_to_one")
        # Devices
        connect(self.pops["R"]["parrot_ANF"], self.recs["R"]["ANF"], "all_to_all")
        connect(self.pops["L"]["parrot_ANF"], self.recs["L"]["ANF"], "all_to_all")
        connect(self.pops["R"]["MSO"], self.recs["R"]["MSO"], "all_to_all")
        connect(self.pops["L"]["MSO"], self.recs["L"]["MSO"], "all_to_all")
        connect(self.pops["R"]["LSO"], self.recs["R"]["LSO"], "all_to_all")
        connect(self.pops["L"]["LSO"], self.recs["L"]["LSO"], "all_to_all")
        connect(self.pops["R"]["SBC"], self.recs["R"]["SBC"], "all_to_all")
        connect(self.pops["L"]["SBC"], self.recs["L"]["SBC"], "all_to_all")
        connect(self.pops["R"]["GBC"], self.recs["R"]["GBC"], "all_to_all")
        connect(self.pops["L"]["GBC"], self.recs["L"]["GBC"], "all_to_all")
        connect(self.pops["R"]["LNTBC"], self.recs["R"]["LNTBC"], "all_to_all")
        connect(self.pops["L"]["LNTBC"], self.recs["L"]["LNTBC"], "all_to_all")
        connect(self.pops["R"]["MNTBC"], self.recs["R"]["MNTBC"], "all_to_all")
        connect(self.pops["L"]["MNTBC"], self.recs["L"]["MNTBC"], "all_to_all")
        connect(self.pops["R"]["ICC"], self.recs["R"]["ICC"], "all_to_all")
        connect(self.pops["L"]["ICC"], self.recs["L"]["ICC"], "all_to_all")

        # ANFs to SBCs
        connect(
            self.pops["R"]["parrot_ANF"],
            self.pops["R"]["SBC"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            num_sources=P.POP_CONN.ANFs2SBCs,
        )
        connect(
            self.pops["L"]["parrot_ANF"],
            self.pops["L"]["SBC"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2SBCs},
            num_sources=P.POP_CONN.ANFs2SBCs,
        )

        # ANFs to GBCs
        connect(
            self.pops["R"]["parrot_ANF"],
            self.pops["R"]["GBC"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            num_sources=P.POP_CONN.ANFs2GBCs,
        )

        connect(
            self.pops["L"]["parrot_ANF"],
            self.pops["L"]["GBC"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.ANFs2GBCs},
            num_sources=P.POP_CONN.ANFs2GBCs,
        )

        # GBCs to LNTBCs
        connect(
            self.pops["R"]["GBC"],
            self.pops["R"]["LNTBC"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2LNTBCs,
                "delay": P.DELAYS.GBCs2LNTBCs,
            },
        )
        connect(
            self.pops["L"]["GBC"],
            self.pops["L"]["LNTBC"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2LNTBCs,
                "delay": P.DELAYS.GBCs2LNTBCs,
            },
        )
        # GBCs to MNTBCs
        connect(
            self.pops["R"]["GBC"],
            self.pops["L"]["MNTBC"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.GBCs2MNTBCs,
                "delay": P.DELAYS.GBCs2MNTBCs,
            },
        )
        connect(
            self.pops["L"]["GBC"],
            self.pops["R"]["MNTBC"],
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
            self.pops["R"]["SBC"],
            self.pops["R"]["MSO"],
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
            },
            num_sources=P.SBCs2MSOs,
        )
        #       contra
        connect(
            self.pops["L"]["SBC"],
            self.pops["R"]["MSO"],
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
            self.pops["L"]["SBC"],
            self.pops["L"]["MSO"],
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_ipsi,
            },
            num_sources=P.SBCs2MSOs,
        )
        #       contra
        connect(
            self.pops["R"]["SBC"],
            self.pops["L"]["MSO"],
            "x_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.SBCs2MSO,
                "delay": P.DELAYS.SBCs2MSO_exc_contra,
            },
            num_sources=P.SBCs2MSOs,
        )
        # From LNTBCs (inhibition), ipsi
        connect(
            self.pops["R"]["LNTBC"],
            self.pops["R"]["MSO"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.LNTBCs2MSO,
                "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
            },
        )
        # From MNTBCs (inhibition) contra
        connect(
            self.pops["R"]["MNTBC"],
            self.pops["R"]["MSO"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )
        # From LNTBCs (inhibition) ipsi
        connect(
            self.pops["L"]["LNTBC"],
            self.pops["L"]["MSO"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.LNTBCs2MSO,
                "delay": P.DELAYS.LNTBCs2MSO_inh_ipsi,
            },
        )
        # From MNTBCs (inhibition) contra
        connect(
            self.pops["L"]["MNTBC"],
            self.pops["L"]["MSO"],
            "one_to_one",
            syn_spec={
                "weight": P.SYN_WEIGHTS.MNTBCs2MSO,
                "delay": P.DELAYS.MNTBCs2MSO_inh_contra,
            },
        )

        # LSO
        connect(
            self.pops["R"]["SBC"],
            self.pops["R"]["LSO"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            num_sources=P.SBCs2LSOs,
        )
        connect(
            self.pops["L"]["SBC"],
            self.pops["L"]["LSO"],
            "x_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.SBCs2LSO},
            num_sources=P.SBCs2LSOs,
        )

        connect(
            self.pops["R"]["MNTBC"],
            self.pops["R"]["LSO"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )
        connect(
            self.pops["L"]["MNTBC"],
            self.pops["L"]["LSO"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MNTBCs2LSO},
        )
        connect(
            self.pops["R"]["MSO"],
            self.pops["R"]["ICC"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MSO2ICC},
        )
        connect(
            self.pops["L"]["LSO"],
            self.pops["R"]["ICC"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.LSO2ICC},
        )
        connect(
            self.pops["L"]["MSO"],
            self.pops["L"]["ICC"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.MSO2ICC},
        )
        connect(
            self.pops["R"]["LSO"],
            self.pops["L"]["ICC"],
            "one_to_one",
            syn_spec={"weight": P.SYN_WEIGHTS.LSO2ICC},
        )

    def simulate(self, time: float | int):
        # split in time chunks
        TIME_PER_CHUNK_TQDM = 100
        chunks = time // TIME_PER_CHUNK_TQDM
        for chunk in tqdm(
            [*list(range(chunks)), time - chunks * TIME_PER_CHUNK_TQDM],
            desc="  ⮡ simulation",
        ):
            nest.Simulate(chunk)

    def analyze(self):
        result = {"L": {}, "R": {}, "version": self.RESULTS_VERSION_NUMBER}
        for side in self.recs.keys():
            for pop_name, pop_data in self.recs[side].items():
                if (
                    pop_name in self.params.CONFIG.STORE_POPS
                    or not self.params.CONFIG.STORE_POPS
                ):
                    result[side][pop_name] = {
                        **pop_data.get("events"),
                        "global_ids": self.pops[side][pop_name].get("global_id"),
                    }

        return result
