import os
import csv
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def get_car_start(csv_path):
    # Default to center if it can't find it
    x, y, yaw = '0.0', '0.0', '0.0'
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            for row in csv.reader(f):
                if row and row[0] == 'car_start':
                    x, y, yaw = row[1], row[2], row[3]
                    break
    return x, y, yaw


def launch_setup(context, *args, **kwargs):

    track_name = LaunchConfiguration('track_name').perform(context)
    vehicle_config = LaunchConfiguration('vehicle_config').perform(context)
    headless = LaunchConfiguration('headless').perform(context).lower() == 'true'

    # 1. Paths to packages
    pkg_gazebo = get_package_share_directory('cmh_gazebo')
    pkg_desc = get_package_share_directory('cmh_description')
    pkg_bringup = get_package_share_directory('cmh_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    track_csv = os.path.join(pkg_gazebo, 'csv', track_name + '.csv')
    car_x, car_y, car_yaw = get_car_start(track_csv)

    # 2. Path to the world file
    worlds_dir = os.path.join(pkg_gazebo, 'worlds')
    world_file = os.path.join(worlds_dir, track_name + '.sdf')
    if not os.path.exists(world_file):
        available = sorted(f[:-4] for f in os.listdir(worlds_dir) if f.endswith('.sdf'))
        raise RuntimeError(
            f"No world '{track_name}.sdf' in {worlds_dir}. Available tracks: {', '.join(available)}")

    # 3. Make the cone models and meshes (model://...) findable by Gazebo
    share_dir = os.path.join(pkg_gazebo, '..')
    model_path = os.path.join(pkg_gazebo, 'models') + ':' + share_dir
    set_env = AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', model_path)

    # 4. Start Gazebo with the track (-r: start running, -s: server only)
    gz_args = f'-r -s --headless-rendering {world_file}' if headless else f'-r {world_file}'
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': gz_args, 'on_exit_shutdown': 'true'}.items()
    )

    # 5. Process the URDF/Xacro file and pass the config YAML
    xacro_file = os.path.join(pkg_desc, 'urdf','mini_car', 'mini_car.urdf.xacro')
    yaml_config_file = os.path.join(pkg_desc, 'config', f'config{vehicle_config.capitalize()}.yaml')

    # Pass the config_file argument into the mappings dictionary
    robot_description_config = xacro.process_file(xacro_file, mappings={'config_file': yaml_config_file})
    urdf = robot_description_config.toxml()

    # 6. Node to spawn the car into Gazebo
    # We spawn it slightly above the ground (z=0.2)
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-string', urdf,
            '-name', 'cmh_car',
            '-allow_renaming', 'true',
            '-z', '0.2',
            '-x', car_x,
            '-y', car_y,
            '-Y', car_yaw
        ],
        output='screen'
    )

    # We must also start the Robot State Publisher so ROS 2 knows the car's joints
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': urdf, 'use_sim_time': True}]
    )

    # 7. Bridge Gazebo <-> ROS 2 topics, see config/gz_bridge.yaml
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': os.path.join(pkg_bringup, 'config', 'gz_bridge.yaml'),
            'use_sim_time': True,
        }],
        output='screen'
    )

    # Return the nodes you want to launch
    return [set_env, gazebo, spawn_entity, bridge, robot_state_publisher]


def generate_launch_description():
    track_arg = DeclareLaunchArgument(
        'track_name',
        default_value='small_track',
        description='Name of the track to launch (a world in cmh_gazebo/worlds)'
    )
    vehicle_config_arg = DeclareLaunchArgument(
        'vehicle_config',
        default_value='dry',
        choices=['dry', 'wet'],
        description='Vehicle parameter set from cmh_description/config'
    )
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        choices=['true', 'false'],
        description='Run Gazebo without the GUI'
    )
    return LaunchDescription([
        track_arg,
        vehicle_config_arg,
        headless_arg,
        OpaqueFunction(function=launch_setup)
    ])
