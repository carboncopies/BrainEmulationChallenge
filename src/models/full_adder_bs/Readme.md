# Notes about the Full Adder BS example

BS Neurons expect to have just one soma compartment and one
axon compartment.

In order to set up the EM visualization for this example, and
the functional receptor connection, this example generates
two compartments that are not associated with a neuron
(there are two extra compartments).

A consequence is that Calcium Imaging does not work, because
Ca Imaging requires that each compartment can find its
associated neuron to read out the Ca state.
