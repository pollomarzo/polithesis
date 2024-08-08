import brian2hears as b2h
import brian2 as b2

DEFAULT_SOUND_DURATION = 1 * b2.second


# i considered subclassing for a bit but i don't know enough
class Tone:
    frequency: b2.Quantity
    sound: b2h.Sound

    def __init__(
        self, frequency: b2.Quantity, duration=DEFAULT_SOUND_DURATION, **kwargs
    ):
        self.frequency = frequency
        self.sound = b2h.Sound.tone(frequency, duration, **kwargs)

    # def __new__(
    #     cls, frequency, phase=0, duration=DEFAULT_SOUND_DURATION, samplerate=None
    # ):
    #     samplerate = b2h.get_samplerate(samplerate)
    #     nchannels = 1
    #     # from b2h: (thanks!)
    #     phase = np.array(phase)
    #     t = np.arange(0, duration, 1) / samplerate
    #     t.shape = (t.size, 1)  # ensures C-order (in contrast to tile(...).T )
    #     x = np.sin(phase + 2.0 * np.pi * frequency * np.tile(t, (1, nchannels)))
    #     self = super().__new__(cls, x)
    #     self.frequency = frequency
    #     return self


class ToneFromAngle(Tone):
    # x = ToneFromAngle(20, 20 * b2.Hz)
    angle: int

    def __init__(self, angle, *args):
        self.angle = angle
        super().__init__(*args)
