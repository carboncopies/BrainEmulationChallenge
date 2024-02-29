#!/bin/bash

echo "Starting BallStick E0 Demo"

echo "Deleting Old Data"
rm -r Renders

echo "Firstly, creating simulation on NES"
./bs_vbp00_groundtruth_xi_sampleprep.py

echo "Now, running data acquisition step"
./bs_vbp01_doubleblind_x_acquisition.py -RenderVisualization -RenderEM -RenderCA

# echo "Creating Visualization GIF"
# ffmpeg -i "Renders/Visualizations/%d.png" Renders/Visualizations/Spin.gif -y

echo "Done."
