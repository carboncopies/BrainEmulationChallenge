# Simple Compartmental XOR example build notes

- Current at typical single AMPA receptor is in pA range.
- Multiple receptors or in specific conditions can get up to nA (or even uA) range.
- In hippocampus, estimates are that a single synapse can have 50-100 active
  AMPA receptors. In hippocampus, through the typical number of receptors and
  one or more synapses, typical AMPA current is several hundres pA or into the
  low nA range.
- In hippocampus, transmission from one neuron to another can involve a few to
  several hundred synapses.
- A single AMPA receptor channel has a conductance in the range of 9-10 pS.

Example: Currents through AMPA receptors from a medial temporal lobe neuron
to a hippocampal neuron.

```
  Number of synapses involved = 80
  Number of active receptors per synapse = 75
  Average conductance of a single receptor channel = 10 pS
  Average potential difference across cell boundary = (-)55 mV
  Typical current across the connection = (-)55 * 10^-3 * 80*75*10 * 10^-12 A
    = 3300000 * 10^-15 A = (-)3.3 * 10^-9 A = (-)3.3 nA
```

  Rewritten to represent magnitudes for the whole connection between the
  two neurons `(i = v * g)`:

```
  (-)3.3 nA = (-)55 mV * 60 nS
```

  The double exponential PSP response model represents the accumulation of
  charge over time and its gradual decay, causing a difference in the
  membrane potential. For the example current and conductance given, the
  firing threshold should be reached after a brief rise-time at the
  hippocampal neuron. That's a change in the membrane potential of about
  10 mV. To represent that level of change at the peak of the double
  exponential `( -exp(-tDiff / tauRise) + exp(-tDiff / tauDecay) )`, with
  a current of about 3.3 nA and conductance of about 60 nS, we need
  a constant weight scaling factor (using `v = i*r = i/g`):

```
    10 mV = w_scaling * (3.3 nA / 60 nS) * peak_doubleexp
```

  The peak of the double exponential is around 0.69

```
    w_scaling = 10*10^-3 * 60 / (3.3 * 0.69) = 0.264
```

  Combining this with the 3.3 nA gives a I_PSP_nA constant of about 0.87 nA.
  And for mV, 870 nA:

```
    10 mV = (870 nA / 60 nS) * peak_doubleexp
```

--
Randal A. Koene, 20240314