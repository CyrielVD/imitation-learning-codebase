#!/usr/bin/env bash

export HOME="${PWD}"
export PYTHONPATH=''
source /opt/ros/melodic/setup.bash

# perform catkin make if source files have changed.
cd "${HOME}/src/sim/ros" || exit 1
make catkin_ws/devel/setup.bash
if [ ! -d python3_ros_ws ] ; then
  make install_python3_ros_ws
fi
if [ ! -d python2_ros_ws ] ; then
  make install_python2_ros_ws
fi
make python3_ros_ws/devel/setup.bash
make python2_ros_ws/devel/setup.bash
cd "${HOME}" || exit 1

# shellcheck disable=SC1090
source "${HOME}/src/sim/ros/catkin_ws/devel/setup.bash" --extend || exit 2
# shellcheck disable=SC1090
source "${HOME}/src/sim/ros/python3_ros_ws/devel/setup.bash" --extend || exit 2
# shellcheck disable=SC1090
source "${HOME}/src/sim/ros/python2_ros_ws/devel/setup.bash" --extend || exit 2

export GAZEBO_MODEL_PATH="${HOME}/src/sim/ros/gazebo/models"
export PYTHONPATH=${PYTHONPATH}:${PWD}

# potentially remove .singularity.d/libs from LD_LIBRARY_PATH
"$@"
