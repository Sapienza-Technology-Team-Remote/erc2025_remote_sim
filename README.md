# Sapienza Technology Team Gazebo environment for ERC2025 Remote formula

## Documentation

[The documentation is available here](https://docs.google.com/document/d/13j-jUbbqSdOE2rpgMe3CeMcOyCfnu6AFhSe7TqYO01E/edit?usp=sharing)

With description of Gazebo version used and detailed workflow on how the 3D model of the marsyard was processed for the simulation.


## Install

Follow the instructions to install husarion simulation environment:
https://github.com/husarion/husarion_ugv_ros/tree/ros2-devel 

Clone and build this package:

    cd <your_workspace>/src
    git clone https://github.com/Sapienza-Technology-Team-Remote/erc2025_remote_sim.git
    cd ..
    colcon build


## Running

Run the Gazebo simulation using:

    ros2 launch erc2025_remote_sim startsimulation.launch.py 






