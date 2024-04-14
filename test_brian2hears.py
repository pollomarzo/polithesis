import matplotlib.pyplot as plt
from brian2 import *
from brian2hears import *
import nest
import nest.voltage_trace

# nest check
neuron = nest.Create("iaf_psc_alpha")
# brian2hears check
sound1 = tone(1*kHz, .1*second)
sound2 = whitenoise(.1*second)
sound = sound1+sound2
sound = sound.ramp()
# pygame check
sound.play()
cf = erbspace(20*Hz, 20*kHz, 3000)
fb = Gammatone(sound, cf)
output = fb.process()
# Half-wave rectification and compression [x]^(1/3)
ihc = FunctionFilterbank(fb, lambda x: 3*clip(x, 0, Inf)**(1.0/3.0))
# Leaky integrate-and-fire model with noise and refractoriness
eqs = '''
dv/dt = (I-v)/(1*ms)+0.2*xi*(2/(1*ms))**.5 : 1 (unless refractory)
I : 1
'''
# brian2 check
anf = FilterbankGroup(ihc, 'I', eqs, reset='v=0',
                      threshold='v>1', refractory=5*ms)
