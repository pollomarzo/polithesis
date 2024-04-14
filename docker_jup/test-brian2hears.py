import matplotlib.pyplot as plt
from brian2 import *
from brian2hears import *
import nest


sound1 = tone(1*kHz, .1*second)
sound2 = whitenoise(.1*second)
neuron = nest.Create("iaf_psc_alpha")
print("is this working?")
