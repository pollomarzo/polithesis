# sound localization

## outside data
just the IRCAM [HRTFs](http://recherche.ircam.fr/equipes/salles/listen/download.html)

## quick info to get you up to speed
Main entry: `generate_results.py`. You need to edit:
- `CURRENT_TEST`: include a significant string that will be the directory for these results, and a mnemonic for what you're currently checking
- a list of inputs
- a list of parameter objects (coupled with a list of models to which the params will be applied)
- the dictionary with your cochleas
Then run `generate_results.py` and wait for the results to be generated. You'll find that, inside the `results` folder, a folder with your `CURRENT_TEST` name was created, with the various models inside. In each subdirectory, you'll find a list of each result object (it's just a large dict in a binary `.pic` file) and a "report card" with an image with a collage of results.

## i killed my process during training, what to do?
maybe you ran out of memory, maybe you ran out of battery. figure out how many of your trials (trial = simulation run with a specific set of parameters, model, input and cochlea) were completed, and what you still need to run. to do this, check your results folder, read your terminal output, or find the corresponding log file inside `logs` (look for the name of the script that generated it (probably `generate_results.py` and the date)). Then run the remaining trials to complete the dataset. You can then manually run the `manually_generate_reports.py` after setting the correct folder inside (default is `CURRENT_TEST` from `generate_results.py`).



## how to run

I've explored a couple different avenues to run this code in a way that allows me to make changes, and decided that my favorite development-oriented way is using
During my exploration, I've considered using docker (what nest is distributed mostly through), but found it inefficient for my workflow; you can find a complete example in [the docker folder](docker_jup/README.md)

Instead, I ended up finding the "manual" way actually faster. I used `micromamba`; fast, single-executable, supports `bash`, `fish`, `zsh`, definitely recommended. `conda` would probably work just as well.
- install [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
- create a suitable virtual environment using the included YAML: `mamba create -n hears -f hears.yml`
- activate the created env: `mamba activate hears`