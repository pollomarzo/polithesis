# plots
## interaction
using `ipywidgets` since it's by same authors. currently using select and button.
possible models are only checked once of course. styling follows CSS specs
`%matplotlib widget` magic supports widgets inside vs code so they are interactive, but `ipympl` is required
https://github.com/fomightez/3Dscatter_plot-binder?tab=readme-ov-file

# running models
## caching
on 21/08 i moved from manually handled pickle files for caching the results of the cochlea section, to joblib. the reason why i made the change is that i got stung by the fact that the manual cache was not invalidated by changes to the function, so when i tried to zero out noise, the (cached) version with noise was returned instead, rendering my result incorrect. i write this note to remember that although this meant a performance hit, it was not a significant one.
the previous code read something along these lines:
```python
def load_anf_response(tone, angle, cochlea_key):
	filepath = (
        Path(Paths.ANF_SPIKES_DIR)
        / Path(cochlea_key)
        / Path(create_sound_key(tone))
        / Path(f"{create_sound_key(tone)}_{angle}deg.pic")
    )
    if os.path.isfile(filepath):
        with open(filepath, "rb") as f:
            anf: AnfResponse = pickle.load(f)
        return anf
    else:
        logger.info(
            f"saved ANF for {dict_of(tone,angle,cochlea_key)} not found. generating... "
        )
        anf = cochlea_func(tone, angle, params)
    filepath.parent.mkdir(exist_ok=True, parents=True)
    with open(filepath, "wb") as f:
        pickle.dump(anf, f)
    logger.debug(f"anf correctly cached for next execution")
```
instead, i now just include the decorator `@memory.cache` on top the cochlea function, and cache is handled automatically. directory structure is lost as a result... too bad.
here is the performance difference

|                         | first run (cache miss) | second run (cache hit) |
| ----------------------- | ---------------------- | ---------------------- |
| manual (pickle)         | 11.795s                | 0.0177s                |
| library (joblib.Memory) | 11.729s                | 0.190s                 |
although i lost near 10x efficiency, i declare it worth it.