import os
import csv
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess,AppendEnvironmentVariable
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

def generate_launch_description():

    track_name=str(input("please specify the track name: "))
    # 1. Paths to your packages
    pkg_gazebo = get_package_share_directory('cmh_gazebo')
    pkg_desc = get_package_share_directory('cmh_description')

    track_csv = os.path.join(pkg_gazebo, 'csv', track_name +'.csv')
    car_x, car_y, car_yaw = get_car_start(track_csv)

    # 2. Path to the world file (using the one you manually migrated)
    world_file = os.path.join(pkg_gazebo, 'worlds', track_name +'.sdf')

    # 3. Start Gazebo Harmonic with your track
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_file],
        output='screen'
    )

    # 4. Process the URDF/Xacro file and pass the config YAML
    xacro_file = os.path.join(pkg_desc, 'urdf', 'car.urdf.xacro')
    yaml_config_file = os.path.join(pkg_desc, 'urdf', 'configDry.yaml')
    
    # Pass the config_file argument into the mappings dictionary
    robot_description_config = xacro.process_file(xacro_file, mappings={'config_file': yaml_config_file})
    urdf = robot_description_config.toxml()

    # 5. Node to spawn the car into Gazebo Harmonic
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
    share_dir = os.path.join(pkg_gazebo, '..')
    model_path = os.path.join(pkg_gazebo, 'models') + ':' + share_dir
    set_env = AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', model_path)

    return LaunchDescription([
        set_env,
        gazebo,
        spawn_entity,
        
    ])
