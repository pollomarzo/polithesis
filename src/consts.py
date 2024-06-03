from inspect import isfunction
from dataclasses import dataclass, asdict, is_dataclass


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
