# How to run this API locally

1. `git clone <this-repo> && cd <this-repo>`
2. `docker build -t covid-api .` Build the docker image using the Dockerfile.
3. `docker run -d -p 5000:5000 covid-api` This runs the container in the background (run `docker ps` to see all running containers) and exposes the port 5000 to the host's port 5000.
4. Finally, try the API out at `127.0.0.1:5000/`