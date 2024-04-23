import matplotlib.pyplot as plt
from brian2 import *
from brian2hears import *
from SLModel import SLModel
from cochlea import spike_generator_from_sound
import nest
import nest.voltage_trace

nest.set_verbosity("M_ERROR")

print("generating spikes...")
generators = spike_generator_from_sound()

print("creating model...")
model = SLModel([generators, generators])  # params
model.simulate(1)
