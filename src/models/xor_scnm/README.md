# Using XOR Simple Compartmental Netmorph scripts

1. Run `./xor_scnm_groundtruth_reservoir.py -modelfile nesvbp-xor-res-sep-targets`
   to produce a model with realistic neurites and save it on the server with the
   default model name `xor_scnm`.

2. Run `./xor_scnm_groundtruth_connectome.py` to tune and prune the reservoir into
   a connectome that is able to support the spiking XOR I/O function. This is
   saved on the server with the default model name `xor_scnm-tuned`.

3. Run `./xor_scnm_acquisition_direct.py` to run test activity on the model and
   acquire data from the virtual tissue.
