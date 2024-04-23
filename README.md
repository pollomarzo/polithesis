# sound localization

## how to run

I've explored a couple different avenues to run this code in a way that allows me to make changes, and decided that my favorite development-oriented way is using
During my exploration, I've considered using docker (what nest is distributed mostly through), but found it inefficient for my workflow; you can find a complete example in [the docker folder](docker_jup/README.md)

Instead, I ended up finding the "manual" way actually faster. I used `micromamba`; fast, single-executable, supports `bash`, `fish`, `zsh`, definitely recommended. `conda` would probably work just as well.
- install [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
- create a suitable virtual environment using the included YAML: `mamba create -n hears -f hears.yml`
- activate the created env: `mamba activate hears`