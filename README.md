# sound localization

## how to run

I've explored a couple different avenues to run this code in a way that allows me to make changes, and decided that my favorite development-oriented way is using
During my exploration, I've considered using docker (what nest is distributed mostly through), but found it inefficient for my workflow; you can find a complete example in [the docker folder](docker_jup/README.md)

- install [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
- follow nest instructions `mamba install nest-simulator brian2`
- (https://www.anaconda.com/blog/using-pip-in-a-conda-environment)
- activate mamba env
- `pip install brian2hears` (still counts as mamba env, check out pip show brian2hears) maybe move to [yaml format](https://github.com/mamba-org/mamba/issues/1899)
