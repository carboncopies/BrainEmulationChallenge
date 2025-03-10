# WBE Challenge Example Models

WBE Challenge evaluation is focused on determining the success score and necessary improvements
when applying a method to interpreting and translating brain data for neuronal circuit
reconstruction with the objective that cognitive functions implemented in the original
tissue are preserved and operational in a corresponding emulation.

The challenge provides a few examples for which the ground-truth system is publicly available,
so that participants can explore and practice, clearly seeing how differences between an emulation and
the ground-truth are evaluated and presented.

The actual data sets provided for participation at a specific level of the challenge are
auto-generated by the NES/VBP-based WBE Challenge platform such that examples of core functional
capabilities of neuronal circuits as found in animal and human brains are included within each
ground-truth system. The meaningful, intended operational function of the ground-truth system
generated is therefore known on the side of the WBE Challenge team. It is up to the challenge
taker and their method of analysis and translation to reconstruction from the provided brain data
in such a way that the underlying operational functions are preserved. As the most important part
of the evaluation of a challenge submission, the presence of those operational functions is
tested using authoritative validation data, as applied in the ground-truth system. Resulting
circuit behavior is compared.

Structural validation metrics compare the high resolution connectome discovered and implemented
in the emulation with the ultrastructure of the ground-truth system, returning similarity scores,
as well as a detailed list of graph edits that would be needed to give the emulation the
ground-truth system structure. This may help participants identify which types of features are
particularly difficult for their applied methods to extract correctly.

Additional functional metrics are applied to test the fidelity of reconstruction at a more
granular scale, such as the reconstruction of individual neurons, although that is not necessarily
as important to the success criteria of the WBE Challenge.

## Practice ground-truth examples

The following subsections describe example ground-truth systems that are provided to the public
in order to practice how to apply analysis, translation and reconstruction methods in the
context of the WBE Challenge.

1. Use the associated data sets to derive a functional neuronal model that aims to emulate operational
   functions of the ground-truth system.
2. Submit the resulting model and receive the resulting Challenge report.
3. Explore indicated differences (if there are any) between the ground-truth system and the emulation.
   Consider how differences detailed in the report may be used to improve the results of your methods.

Successive levels of the WBE Challenge are designed using a specific set of simplifications that
set up laboratory conditions intended to limit the number of variables that need to be taken into
account. The data sets provided at each level are therefore accompanied by a description of the
characteristics of the "brain tissue", in terms of included and excluded features.

We greatly appreciate feedback about the Challenge protocol, data sets provided, and more. Like
the reconstruction methods tested, the Challenge itself is improvable, a process that will be greatly
accelerated through feedback by the community.

### Spiking neuron XOR logic circuit

A logic circuit composed of 5 spiking principal neurons and 2 spiking interneurons, the output of
which generates a spike when a spike is presented at one but not both input neurons simultaneously.

This practice ground-truth system includes interaction between neurons with excitatory AMPA
synapses and interneurons with inhibitory GABA synapses onto target cells and relies on tuned
connection strengths for proper operation.

[Link to XOR practice system page](./practice-models/xor)

### T-maze 7 place field auto-associative ECIII-inspired attractors

A population of principal neurons with recurrent conenctions that is also connected to a population
of interneurons with synaptic connection strengths operating as an attractor network where synapic
connection strengths embed 7 different reactivatable patterns composed of "place cells" that
refer to 7 positions in an experimental T-maze.

This practice ground-truth system contains a neuronal circuit reminiscent of models of
place cell populations involved in rodent spatial navigation.

[Link to auto-associative system page](./practice-model/auto-associative)

### One-shot sustained activity short-term buffer using after-depolarization

A population of principal neurons that experience after-depolarization (in addition to after-hyperpolarization)
in the presence of rhythmic modulation (e.g at theta frequency), plus a population of interneurons providing
recurrent inhibition. Neuron populations with these properties have been shown to exhibit sustained
activity for a limited time-interval.

This practice ground-truth system contains a neuronal circuit that is able to receive a pattern of input exceeding
spiking thresholds that is maintained through multiple cycles of intrinsic reactivation. Neural behavior of
this sort has been putatively implicated in short-term buffering of patterns of activity following a single
presentation of input, independent of synaptic modification or mutual synaptic connections. After-depolarization
is exhibited by many pyramidal neurons in the neocortex (...add citation...).

[Link to ADP system page](./practice-model/ADP)


## Operational neuronal circuit components used in auto-generated ground-truth systems from which Challenge data sets are produced

The following subsections describe neuronal circuits that achieve cognitively meaningful operations
and are used as components within auto-generated ground-truth systems that produce sample "brain data"
at levels of the WBE Challenge.

### Single-neuron dendritic-computation

While evidence for neural systems in the human brain that depend strongly or entirely on the use of
dendritic computation are not as plentiful as examples in animal brains, such as the the frog and
(...put citation here...), dendritic computation is potentially essential for precise binaural
triangulation of the source-location of sound, as in the human auditory system. For this reason,
several levels of the WBE Challenge include operational components with explicit detail used in
dendritic computation.

[Link to Challenge level that may include this component](./level/something)

### Retrievable pattern memory through attractors of neuronal population activity

Recurrent network topology supports static attractors for retrieved pattern activity from
partial context cues.

[Link to Challenge level that may include this component](./level/something)

### Spontaneous recruitment as reservoir computing in an interconnected population of neurons

Mixed auto- and heteroassociative properties of reservoir computing are putatively considered as
a way for cortical neuronal networks to work with dynamic attractor information encountered in
real-world scenarios. Neurons in this core operational component support attractors at multiple
spatial and temporal scales.

[Link to Challenge level that may include this component](./level/something)

### Feature detector composition through simple- to complex-cell layering

A fundamental approach to accomplishing sophisticated feats of recognition or output
production in neuronal networks is layered composition beginning with simple feature
detector cells, the output of which combines to create more complex detectors at
successive layers. Such multi-layer operational neuronal circuits are found, for example,
in the mammalian visual system.

[Link to Challenge level that may include this component](./level/something)

### Cell-specific receptive fields in auto- and hetero-associative newtorks

As in place cell networks of hippocampal CA3 and CA1 regions, and grid cell-like behavior, the
basic operations of neurons in these populations apply to select subdomains of possible
input, i.e. their specific receptive fields.

[Link to Challenge level that may include this component](./level/something)

### Sustained activity of cortical pyramidal neurons

Specific types of neurons can exhibit after-depolarization and may enter periods of
sustained rhythmic activity that can maintain activation in spiking (non-bursting) fashion
for a limited time-interval.

[Link to Challenge level that may include this component](./level/something)

### Columnar processing

Layered populations of neurons with short-range local connectivity and long-range
connections beyond the local region can form processing columns (e.g. neocortical
minicolumns) that are able to carry out operations unifying information from two or
more streams of activity.

[Link to Challenge level that may include this component](./level/something)

### Synchronized rhythmic modulation

As exhibited and observed through extracellular recording, rhythmic modulation of overall
population activity can lead to synchronized patterns of spikes and their propagation
through multiple stages of a neuronal circuit.

[Link to Challenge level that may include this component](./level/something)

### Rhythmic interaction at specific phase offsets

Maintaining specific phase offsets between the rhythmic activity of neurons in
connected layers or regions can enable a precise sequence of stage-wise neuronal
processing.

[Link to Challenge level that may include this component](./level/something)
