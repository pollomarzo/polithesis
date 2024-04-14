# Running NEST from Docker

NEST is distributed in a few different ways. One of these, and maybe the most well-packaged, is a docker image, and an attached docker compose file. Using the docker version, you don't need to worry about dependencies, isolation and reproducibility: within the docker image, the packages won't ever be updated, and everything will work in the future and in any OS. In my opinion, this also makes it a bit annoying to use; I've decided not to go with this option, but I'll leave this here, since it would probably be the best way to package a final jupyter notebook for an article/thesis to ensure reproducibility.

Of course, it's also possible to run the single python script (.py) using this docker container, but it's a bit weirder than usual. I'll walk through both alternatives.

## jupyter

> TLDR: `docker compose up nest-notebook` -> obtain jupyter notebook link

Running a jupyter notebook requires setting up a jupyter server with an iPython runtime (not sure these are the right names). Since the server will need nest access, it will have a running nest simulator instance, but this is not our concern: we'll just use the base docker image given by nest. I used VSCode for a jupyter IDE.

### the jupyter server

The attached `docker-compose.yml` was first obtained directly from nest's [documentation](https://nest-simulator.readthedocs.io/en/v3.7_rc1/installation/docker.html#docker), which points you to [this repo](https://raw.githubusercontent.com/nest/nest-docker/master/docker-compose.yml).

It was then edited along with a custom `Dockerfile`, included here, which adds necessary packages to the image. When running `docker compose up nest-notebook`, you'll see that:

- the nest/nest-simulator:3.6 image is pulled from docker [hub](https://hub.docker.com/r/nest/nest-simulator)
- requirements in `requirements.txt` are installed
- jupyter notebook starts, giving a URL for the server

When run in the future, both image and requirements will be cached, and startup will be much quicker

> **NB**: this does not mean your work will be cached inside the image. On every run, a new container is created, starting from the image. Saving work is not desirable; nest keeps state, and an existing state might trip you up.

> note: the current directory is mounted at /opt/data, as in the original docker compose setup.

### running the notebook

With this, the jupyter server is ready. Just copy the URL you see in the logs, run the notebook, and paste the URL you copied in the text box where VS Code asks which jupyter server to use.

## single scripts (.py files)

> TLDR: use `%run '<script_name>.py'` inside a jupyter notebook cell

To run single scripts, the normal thing to do would be to either (1) open a bash session running in the Docker container (`docker ps` to see running containers; `docker exec <container_name> bash`) and run the script from there (`python <script_name>`), or (2) ask docker to run the script directly (`docker exec <container_name> python <script_name>`); unfortunately, `pyNest`, (aka what you get when running `pip install nest`) doesn't need to be installed for it to be run from the jupyter server, so it isn't. Just running `pip install nest` wouldn't be enough either, so here is a far simpler solution: by running the single script _from_ a jupyter notebook, the script doesn't need to be mounted at creation of the container, and it will execute within the jupyter server environment, hence with all the necessary dependencies. You can run scripts using the `run` magic (their word) directive, like `%run '<script_name>.py'`.
