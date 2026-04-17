#!/bin/bash

# Define variables
CONTAINER_NAME="cmh_humble"
IMAGE_NAME="cmh_sim_env"

# Check if the container is already running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Attaching to running container $CONTAINER_NAME..."
    docker exec -it $CONTAINER_NAME bash
    exit 0
fi

# Check if the container exists but is stopped
if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
    echo "Starting stopped container $CONTAINER_NAME..."
    docker start $CONTAINER_NAME
    docker exec -it $CONTAINER_NAME bash
    exit 0
fi

# If it does not exist, run a new one
echo "Creating and starting new container $CONTAINER_NAME..."
docker run -it --net=host \
    --name $CONTAINER_NAME \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$(pwd)/cmh_workspace:/workspace" \
    $IMAGE_NAME
