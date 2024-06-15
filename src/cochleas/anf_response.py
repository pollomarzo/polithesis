from dataclasses import dataclass
from brian2hears import Sound


@dataclass
class AnfResponse:
    binaural_anf_spiketrain: dict
    left: Sound
    right: Sound


@dataclass
class SoundFromAngles:
    basesound: Sound
    angle_to_response: dict[str, AnfResponse]
