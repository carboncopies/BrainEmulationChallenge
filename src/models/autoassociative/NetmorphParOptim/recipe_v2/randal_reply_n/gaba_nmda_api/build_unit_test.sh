#!/bin/bash
# Builds and runs SimulationReceptorStrength.test.cpp standalone (the CMake unit-test target is commented out in
# Source/Core/CMakeLists.txt and Simulation.test.cpp does not compile against the current Simulation API).
# Needs a finished build of the tree (Build/ with the object files), here /home/johnjose/BrainGenix/wt/nes-linefix.
set -e
T=/home/johnjose/BrainGenix/wt/nes-linefix; S=${1:-/tmp/rs_unit_test}; mkdir -p $S
cd $T/Build/Source/Core
FL=$(grep "^CXX_FLAGS" CMakeFiles/BrainGenix-NES.dir/flags.make | cut -d= -f2-)
DEF=$(grep "^CXX_DEFINES" CMakeFiles/BrainGenix-NES.dir/flags.make | cut -d= -f2-)
INC=$(grep "^CXX_INCLUDES" CMakeFiles/BrainGenix-NES.dir/flags.make | cut -d= -f2-)
eval /usr/bin/c++ $DEF $INC $FL -c $T/Source/Core/Simulator/Structs/SimulationReceptorStrength.test.cpp -o $S/rs.test.o
printf '#include <gtest/gtest.h>\nint main(int c,char**v){::testing::InitGoogleTest(&c,v);return RUN_ALL_TESTS();}\n' > $S/m.cpp
eval c++ -O1 $INC -c $S/m.cpp -o $S/m.o
VP=$(ls -d $T/Build/vcpkg_installed/*/lib | head -1)
# same link line as the NES binary, without Main.cpp.o, plus gtest (libgtest_main is not installed: own main above)
sed "s# \"CMakeFiles/BrainGenix-NES.dir/Main.cpp.o\"##; s#-o [^ ]*BrainGenix-NES#-o $S/rs_test $S/rs.test.o $S/m.o#; s#\$# -L$VP -lgtest -lpthread#" CMakeFiles/BrainGenix-NES.dir/link.txt > $S/link.sh
sh $S/link.sh
$S/rs_test
