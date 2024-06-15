

i want to be able to do this:


```python
import Tone, Params, InhModel, PpgModel
import RealisticCochlea, PpgCochlea
inputs = [Tone(i) for i in [100,1000,10000] * Hz]

params = Params()
models = [InhModel, PpgModel]
for input in inputs:
    for cochlea in cochleas:
        # this section will be cached on disk
        anf = cochlea(input)
        for Model in models:
            model = Model(params)
            model.simulate(anf)
            results[input.key] = {
                "input": input, 
                "results": model.analyze()
            }
            input.itd_ild_plots()
```
