- *container*: a container is another process on your machine that has been isolated from all other processes on the host machine. That isolation leverages [kernel namespaces and cgroups](https://medium.com/@saschagrunert/demystifying-containers-part-i-kernel-space-2c53d6979504), features that have been in Linux for a long time
- *image*: When running a container, it uses an isolated filesystem. This custom filesystem is provided by a **container image**. Since the image contains the container's filesystem, it must include everything needed to run the application - all dependencies, configuration, scripts, binaries, etc. The image also contains other configuration for the container, such as environment variables, a default command to run, and other metadata.

## local handling
### creating image
```
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN yarn install --production
CMD ["node", "src/index.js"]
```

### building image
```
docker build -t tag_name .
```
### running container
```
docker run -dp 3000:3000 tag_name
```

### listing, stopping
```
docker ps
docker container ls
docker image ls

# ID from docker ps
docker stop <the-container-id>

docker rm <the-container-id>
```
## sharing
1. Go to [Docker Hub](https://hub.docker.com) and log in if you need to.
2. Click the **Create Repository** button.
3. Repo name, visibility (`Public`).
4. Click the **Create** button!
5. `docker login -u YOUR-USER-NAME`
6. `docker tag running_image_tag YOUR-USER-NAME/getting-started`
7. `docker push YOUR-USER-NAME/getting-started`

## specialties
### access terminal of running image
```
docker exec <container-id> cat /data.txt
```
## compose
[Docker Compose](https://docs.docker.com/compose/) is a tool that was developed to help define and share multi-container applications. With Compose, we can create a YAML file to define the services and with a single command, can spin everything up or tear it all down.

The _big_ advantage of using Compose is you can define your application stack in a file, keep it at the root of your project repo (it's now version controlled), and easily enable someone else to contribute to your project. Someone would only need to clone your repo and start the compose app.