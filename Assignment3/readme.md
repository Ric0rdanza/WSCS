1. run `docker pull nginx` to create a nginx image
2. run `docker build ./push_to_docker_auth`, checking its image id with command `docker images`, and rename the image `docker tag [image id] auth:latest`
3. run `docker build ./push_to_docker_url`, checking its image id with command `docker images`, and rename the image `docker tag [image id] main:latest`
4. create a bridge network `docker network create my_net`
5. start all three images in the created network, Nginx: `docker run --name nginx --network my_net --network-alias Nginx -p 5000:80 -d nginx`, Authorization: `docker run --name auth --network my_net --network-alias Auth -p 5001:8000 -d auth`, Url_shortener: `docker run --name main --network my_net --network-alias Main -p 5002:8000 -d main`
6. open a CLI of nginx container created, and copy `./conf.d/default.conf` into `/etc/nginx/conf.d/` and run command `nginx -s reload`
