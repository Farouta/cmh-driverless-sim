FROM ros:humble
SHELL ["/bin/bash", "-c"]

ENV CONTAINER_PORT=8765
EXPOSE ${CONTAINER_PORT}

# Install necessary system and ROS packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
    sudo \
    python3-rosdep \
    python3-pip \
    python3-colcon-common-extensions \
    libignition-common3-dev \
    libfmt-dev \
    libgoogle-glog-dev \
    libceres-dev \
    libjsoncpp-dev \
    ros-humble-ackermann-msgs  \
    ros-humble-geodesy \
    ros-humble-foxglove-bridge \
    ros-humble-xacro \
    ros-humble-joy \
    ros-humble-velodyne-driver \
    && apt-get clean \
    && apt-get install -y python3-skimage

# Install python packages
RUN pip3 install xacro tqdm pytest-cov setuptools==68

# Initialize rosdep
RUN rosdep init || true && rosdep update

# Set the default working directory
WORKDIR /workspace

# Set default command
CMD ["/bin/bash"]
