import brian2 as b2
import brian2hears as b2h

DEFAULT_SOUND_DURATION = 150 * b2.ms
DEFAULT_SILENCE_DURATION = DEFAULT_BURST_SINGLE_DURATION = 50 * b2.ms
DEFAULT_BURST_REP = 3


# i considered subclassing for a bit but i don't know enough
class Tone:
    frequency: b2.Quantity
    sound: b2h.Sound

    def __init__(
        self, frequency: b2.Quantity, duration=DEFAULT_SOUND_DURATION, **kwargs
    ):
        self.frequency = frequency
        self.sound = b2h.Sound.tone(frequency, duration, **kwargs)


class ToneBurst:
    frequency: b2.Quantity
    sound: b2h.Sound
    burst_num: int

    def __init__(
        self,
        frequency: b2.Quantity,
        single_duration=DEFAULT_BURST_SINGLE_DURATION,
        burst_num=DEFAULT_BURST_REP,
        silence_duration=DEFAULT_SILENCE_DURATION,
        **kwargs,
    ):
        self.frequency = frequency
        self.burst_num = burst_num
        self.sound = b2h.Sound.sequence(
            [
                b2h.Sound.tone(frequency, single_duration, **kwargs),
                b2h.Sound.silence(silence_duration),
            ]
        ).repeat(burst_num)


class WhiteNoise:
    sound: b2h.Sound

    def __init__(self, duration=DEFAULT_SOUND_DURATION, level=None, **kwargs):
        self.sound = b2h.Sound.whitenoise(duration, **kwargs)
        if level is not None:
            self.sound.level = level


class Click:
    sound: b2h.Sound

    def __init__(self, duration=DEFAULT_SOUND_DURATION, **kwargs):
        self.peak = kwargs.get("peak", None)
        self.sound = b2h.click(duration, **kwargs)


class ToneFromAngle(Tone):
    # x = ToneFromAngle(20, 20 * b2.Hz)
    angle: int

    def __init__(self, angle, *args):
        self.angle = angle
        super().__init__(*args)
