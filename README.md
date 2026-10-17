# cmh-driverless-sim

Autonomous pipeline for Campus Motorsport Hannover (Formula Student Driverless 2026).

## Technology Stack
- **OS:** Ubuntu 26.04 (Resolute Raccoon)
- **Framework:** ROS 2 Lyrical Luth
- **Simulation:** Gazebo Jetty (gz sim 10), installed through the `ros_gz` vendor packages
- **Modeling Format:** SDF 1.10 & URDF (Xacro)

## Packages
| Package | Type | Contents |
|---|---|---|
| `cmh_bringup` | ament_cmake | `sim.launch.py` and the ROS-Gazebo bridge config (`config/gz_bridge.yaml`) |
| `cmh_description` | ament_cmake | Car models (`urdf/`), meshes, vehicle parameters (`config/configDry.yaml`, `configWet.yaml`) |
| `cmh_sensors` | ament_cmake | Sensor xacro macros (front camera) |
| `cmh_gazebo` | ament_cmake | Worlds, cone models, track layouts (`csv/`), track generator script |
| `cmh_autonomy` | ament_python | Our ROS 2 nodes (perception, planning, control) |

## Setup (once per machine)
This repository is the `src/` folder of a colcon workspace, e.g. `~/cmh_ws/src`.

```bash
# ROS 2 Lyrical desktop must already be installed and sourced in ~/.bashrc
sudo apt update
sudo apt install ros-lyrical-ros-gz ros-lyrical-xacro

# Install all remaining dependencies declared in the package.xml files
sudo rosdep init        # only the very first time on this machine
rosdep update
cd ~/cmh_ws
rosdep install --from-paths src --ignore-src -y --rosdistro lyrical
```

## Build
```bash
cd ~/cmh_ws
colcon build --symlink-install
source install/setup.bash   # in every new terminal
```
`--symlink-install` links Python files and launch files, so edits to them don't need a rebuild.
You still need to rebuild after adding a new node (entry point) or a new file to install.

## Run the simulation
```bash
ros2 launch cmh_bringup sim.launch.py track_name:=minimal_track
```
Launch arguments:
- `track_name:=<world>` - a world from `cmh_gazebo/worlds/` (see below). Default: `small_track`
- `vehicle_config:=dry|wet` - vehicle parameter set from `cmh_description/config/`
- `headless:=true` - run Gazebo without the GUI window

### Worlds
| World | Contents | Car start (from `csv/<world>.csv`) |
|---|---|---|
| `minimal_track` | Ground plane + 2 yellow cones. Use this for development | (-8, 8) |
| `only_car` | Empty ground plane | (1, 1) |
| `small_track` | Full EUFS small track, 71 cones | (-13, 10.3) |

The car's start pose is read from the `car_start` row of the world's CSV. The other CSVs in `csv/` (skidpad, acceleration, ...) have no world file yet.

### Drive the car by hand
```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 0.3}}"
```
`linear.x` is the speed [m/s] and `angular.z` the yaw rate [rad/s]. Gazebo's Ackermann plugin turns the yaw rate into a steering angle, so the car can only turn while it moves. It also keeps the last command, so publish an empty `Twist` (`"{}"`) to stop.

### Look at the data
- Camera: `ros2 run rqt_image_view rqt_image_view`, then pick `/camera/image_raw`
- TF tree and car model: `rviz2`, set the fixed frame to `odom`, then add the `TF` and `RobotModel` displays
- TF tree as a PDF: `ros2 run tf2_tools view_frames`

## How the simulation fits together
`sim.launch.py` starts four things:

1. **Gazebo** with the world `cmh_gazebo/worlds/<track_name>.sdf`.
2. **Car spawn** (`ros_gz_sim create`): the car model `cmh_description/urdf/mini_car/mini_car.urdf.xacro` is processed with the YAML vehicle config, then inserted into the world at the CSV start pose.
3. **`robot_state_publisher`**: reads the same car model and `/joint_states`, and publishes the car's frames on `/tf`.
4. **`ros_gz_bridge`**: copies topics between Gazebo and ROS 2, as listed in `cmh_bringup/config/gz_bridge.yaml`.

Plugins inside the car model give it its behaviour:
- **AckermannSteering**: reads `/cmd_vel`, steers and drives the wheels, and publishes `/odom` plus the `odom → base_footprint` transform.
- **JointStatePublisher**: publishes the wheel and steering joint angles on `/joint_states`.
- **Camera sensor**: publishes `/camera/image_raw` and `/camera/camera_info`.

### Topics (ROS side)
| Topic | Type | Direction | Notes |
|---|---|---|---|
| `/clock` | `rosgraph_msgs/Clock` | Gazebo → ROS | Simulation time; start nodes with `-p use_sim_time:=true` |
| `/cmd_vel` | `geometry_msgs/Twist` | ROS → Gazebo | Speed + yaw rate command |
| `/odom` | `nav_msgs/Odometry` | Gazebo → ROS | Car pose and velocity in the `odom` frame, 50 Hz |
| `/tf` | `tf2_msgs/TFMessage` | Gazebo → ROS | `odom → base_footprint` |
| `/joint_states` | `sensor_msgs/JointState` | Gazebo → ROS | Wheel and steering joints |
| `/camera/image_raw` | `sensor_msgs/Image` | Gazebo → ROS | 640×480 RGB, 30 Hz |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | Gazebo → ROS | Camera intrinsics |

### TF tree
```
odom
└── base_footprint
    └── chassis
        ├── left_steering_hinge  → left_front_wheel
        ├── right_steering_hinge → right_front_wheel
        ├── left_rear_wheel
        ├── right_rear_wheel
        └── camera_center
```
`odom → base_footprint` comes from the Ackermann plugin (the car's position in the world). Everything below `base_footprint` comes from `robot_state_publisher`.

## The car
There are two car models in `cmh_description/urdf/`:
- `mini_car/mini_car.urdf.xacro`: **used by the launch file.** Same dimensions as the real car, built from simple boxes and cylinders.
- `car.urdf.xacro`: the full car with the chassis and wheel meshes.

Both read their geometry and limits from `cmh_description/config/configDry.yaml` (or `configWet.yaml`):

| Parameter | Value | YAML key |
|---|---|---|
| Wheelbase | 1.58 m | `kinematics.l` |
| Track width | 1.4 m | `kinematics.axle_width` |
| Wheel radius | 0.2525 m | `tire.radius` |
| Max steering angle | ±0.52 rad (≈30°) | `input_ranges.steering` |
| Max speed | 30 m/s | `input_ranges.velocity.max` |
| Acceleration limits | +3 / −10 m/s² | `input_ranges.acceleration` |

Smallest turning radius ≈ wheelbase / tan(max steering) = 1.58 / tan(0.52) ≈ 2.75 m.

The camera sits on the chassis at (−0.08, 0, 0.76) m, tilted 0.1 rad down. It is defined in `cmh_sensors/urdf/monocular_camera.urdf.xacro`, and it is only created when the xacro argument `simulate_perception` is `true`. That is the default in `mini_car.urdf.xacro`.

## Cones
Cones are a visual representation only. They are `static` models, so the physics engine doesn't simulate them and they cost no simulation time. Their only collision is a flat box at the base, which is what the car bumps into if it drives into a cone.

Static cones don't fall, so place them with their base at z = 0 in new worlds. A cone placed higher will hover.

## Writing a node
Nodes live in `cmh_autonomy/cmh_autonomy/`. `simple_driver.py` is a minimal example to copy.

1. Create `cmh_autonomy/cmh_autonomy/my_node.py` with a `main()` function.
2. Register it in `cmh_autonomy/setup.py`:
   ```python
   'console_scripts': [
       'simple_driver = cmh_autonomy.simple_driver:main',
       'my_node = cmh_autonomy.my_node:main',
   ],
   ```
3. Add any new message dependencies (e.g. `<depend>sensor_msgs</depend>`) to `cmh_autonomy/package.xml`.
4. Rebuild and run it with simulation time:
   ```bash
   colcon build --symlink-install --packages-select cmh_autonomy
   source install/setup.bash
   ros2 run cmh_autonomy my_node --ros-args -p use_sim_time:=true
   ```

Run the linters and tests with `colcon test --packages-select cmh_autonomy && colcon test-result --verbose`.