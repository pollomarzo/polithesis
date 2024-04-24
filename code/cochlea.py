from enum import Enum
from brian2 import *
from brian2hears import *
import nest

NUM_CF = 3500  # 3500 (3.5k cochlea ciliar -> 10 ANF for each -> 35000 ANF)
NUM_ANF_PER_HC = 10
CFMIN = 20 * Hz
CFMAX = 20 * kHz
IRCAM_DIR = "../data/IRCAM"


def spike_generator_from_sound(
    sound: Sound = Sound.tone(1 * kHz, 1 * second), plot_spikes=False
):
    hrtfdb = IRCAM_LISTEN(IRCAM_DIR)
    hrtfset = hrtfdb.load_subject(hrtfdb.subjects[0])
    # there are 24 trials per row, 187 trils total, elevation starts at -45;
    # we want elevation=0, azimuth=0
    index = 72
    # HRTF for the chosen location
    hrtf = hrtfset.hrtf[index]
    # We apply the chosen HRTF to the sound, the output has 2 channels
    hrtf_fb = hrtf.filterbank(sound)
    cf = erbspace(CFMIN, CFMAX, NUM_CF)
    # in here, we will place two nest.NodeCollection; the first will contain the ANF spikes for the left ear, the second for the right
    anfs_per_ear = []
    for sound_arr in hrtf_fb.process().T:
        sound = Sound(sound_arr)
        # frequencies distributed as cochlea
        # To model how hair cells in adjacent frequencies are engaged as well, but less
        gfb = Gammatone(sound, cf)
        # cochlea modeled as halfwave rectified -> 1/3 power law
        ihc = FunctionFilterbank(gfb, lambda x: 3 * clip(x, 0, Inf) ** (1.0 / 3.0))
        # Leaky integrate-and-fire model with noise and refractoriness
        eqs = """
        dv/dt = (I-v)/(1*ms)+0.2*xi*(2/(1*ms))**.5 : 1 (unless refractory)
        I : 1
        """
        G = FilterbankGroup(
            ihc, "I", eqs, reset="v=0", threshold="v>1", refractory=5 * ms
        )
        # Run, and raster plot of the spikes
        M = SpikeMonitor(G)
        run(sound.duration)
        if plot_spikes:
            plot(M.t / ms, M.i, ".")
            show()

        spike_trains = [e / ms for i, e in M.spike_trains().items()]

        anfs = nest.Create("spike_generator", NUM_CF * NUM_ANF_PER_HC)
        # each hair cell is innervated by NUM_ANF_PER_HC nerve fibers
        for i, e in enumerate(spike_trains):
            for j in range(NUM_ANF_PER_HC * i, NUM_ANF_PER_HC * i + NUM_ANF_PER_HC):
                nest.SetStatus(
                    anfs[j], params={"spike_times": e, "allow_offgrid_times": True}
                )
        anfs_per_ear.append(anfs)

    return anfs_per_ear
