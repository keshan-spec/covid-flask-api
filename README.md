# How to run this API locally

The API can be run using a docker container. If you have docker installed, all you need to do is;
1. `git clone <this-repo> && cd <this-repo>`
2. `docker network create <network-name>` - Create a network for your flask api and redis db to communicate in.
3. `docker-compose up` -  This command will create the services for the flask API and a redis db for caching the API requests. Both containers will be runnning on the network you created above and specified in the `docker-compose.yml`.
4. Finally, try the API out at `127.0.0.1:5000/`

```
NOTE: If you have given a network name that is different to what I have specified in the .yml file. 
You must change it for the API to work.
```