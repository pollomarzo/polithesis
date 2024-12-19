"""
This is a patched version of a brian2hearsfile: sound samplerate is in Hz,
but scipy cannot handle units, so the Hz have to go before being processed
by scipy.
"""

import numpy as np
import scipy.signal as signal
from brian2 import Hz
from brian2hears.filtering.filterbank import RestructureFilterbank
from brian2hears.filtering.linearfilterbank import LinearFilterbank


class MiddleEar(LinearFilterbank):
    """
    Implements the middle ear model from Tan & Carney (2003) (linear filter
    with two pole pairs and one double zero). The gain is normalized for the
    response of the analog filter at 1000Hz as in the model of Tan & Carney
    (their actual C code does however result in a slightly different
    normalization, the difference in overall level is about 0.33dB (to get
    exactly the same output as in their model, set the ``gain`` parameter to
    0.962512703689).

    Tan, Q., and L. H. Carney.
    "A Phenomenological Model for the Responses of Auditory-nerve Fibers.
    II. Nonlinear Tuning with a Frequency Glide".
    The Journal of the Acoustical Society of America 114 (2003): 2007.
    """

    def __init__(self, source, gain=1, **kwds):
        # Automatically duplicate mono input to fit the desired output shape
        gain = np.atleast_1d(gain)
        if len(gain) != source.nchannels and len(gain) != 1:
            if source.nchannels != 1:
                raise ValueError(
                    "Can only automatically duplicate source "
                    "channels for mono sources, use "
                    "RestructureFilterbank."
                )
            source = RestructureFilterbank(source, len(gain))
        samplerate = source.samplerate
        zeros = np.array([-200, -200])
        poles = np.array([-250 + 400j, -250 - 400j, -2000 + 6000j, -2000 - 6000j])
        # use an arbitrary gain here, will be normalized afterwards
        b, a = signal.zpk2tf(zeros, poles * 2 * np.pi, 1.5e9)
        # normalize the response at 1000Hz (of the analog filter)
        resp = np.abs(signal.freqs(b, a, [1000 * 2 * np.pi])[1])  # response magnitude
        b /= resp
        bd, ad = signal.bilinear(b, a, samplerate / Hz)
        bd = (np.tile(bd, (source.nchannels, 1)).T * gain).T
        ad = np.tile(ad, (source.nchannels, 1))
        LinearFilterbank.__init__(self, source, bd, ad, **kwds)
