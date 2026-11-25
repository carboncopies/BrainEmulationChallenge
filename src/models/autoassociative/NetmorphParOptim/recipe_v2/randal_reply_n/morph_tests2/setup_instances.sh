#!/bin/bash
# Create N separate patched NES+API instance folders (shared read-only binaries, own config/ports/output). usage: setup_instances.sh N
set -e; H=$(cd $(dirname $0); pwd); B=/home/johnjose/BrainGenix/wt/nes-linefix/Binaries; A=/home/johnjose/BrainGenix/wt/linefix-instance
for k in $(seq 0 $(($1-1))); do
  P=$((8200+10*k)); d=$H/instances/i$k; mkdir -p $d/nes $d/api $d/out $d/Source/Core/Config
  for f in $B/*; do [ "$(basename $f)" = NES.yaml ] || ln -sfn $f $d/nes/; done
  printf 'Network_NES_API_Port: %d\nNetwork_NES_API_Host: 0.0.0.0\n\nVSDA_EM_PercentOfSysteMemoryLimit: 70\nVSDA_EM_MaxVoxelArraySize: 5000\n\nOutput_BasePath: %s\n' $((P+2)) $d/out > $d/nes/NES.yaml
  ln -sfn $A/api/BrainGenix-API $d/api/BrainGenix-API; cp $A/Source/Core/Config/users.json $d/Source/Core/Config/
  printf '[Network.Service]\nPort=%d\nHost=127.0.0.1\nUseHTTPS=False\nKeyFilePath=SetYourPathHere\nCrtFilePath=SetYourPathHere\nURL=localhost\n\n[Network.RPCCallback]\nPort=%d\nHost=localhost\n\n[Network.NES]\nPort=%d\nHost=localhost\nTimeout_ms=10000\n\n[Network.EVM]\nPort=%d\nHost=localhost\nTimeout_ms=10000\n\n[Network.Neuroglancer]\nPort=%d\n' $P $((P+1)) $((P+2)) $((P+3)) $((P+4)) > $d/api/API.cfg
done
