# cmh_gazebo

This package contains the Gazebo Harmonic simulation environments and 3D cone models for the Campus Motorsport Hannover Formula Student Driverless team.

## Acknowledgements & Migration
The environments and CSV layouts are based on work from the [Edinburgh University Formula Student (EUFS) open-source repository](https://gitlab.com/eufs/public/eufs_sim). 

Adjustments were made to migrate their original models (which were structured for older ROS/Gazebo versions) to our current stack. Most notably, the SDF version has been updated from `1.6` to `1.10` for compatibility with Gazebo Harmonic.

## Structure & Meshes
* The `meshes/` folder contains the `.dae` (Blender 3D) models for the cones.
* These meshes are imported into the individual cone models (`models/<model_name>/model.sdf`).

To correctly reference a mesh in the SDF, use the following syntax:
```xml
<mesh>
  <uri>model://cmh_gazebo/meshes/<mesh_name>.dae</uri>
</mesh>
```
*Note: Ensure the `GZ_SIM_RESOURCE_PATH` environment variable is set to find these models.*

## Future Goals
EUFS included `.csv` files containing coordinates for each track layout. Our next objective is to integrate a `track_generator` script to automate the generation of these `.sdf` worlds, making track creation significantly easier and more modular.