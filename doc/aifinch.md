# AI Finch - Example VBP specification for Translation study

The AI Finch example is intended to demonstrate the principles of simulation systems
created using the Virtual Brain Project framework for the study of the Translation
problem in whole brain emulation.

AI Finch is loosely based on the neuromorphology and neurophysiology of song memory
in the Zebra Finch. It is a simplified, artificial version that represents an
imagined artificial Finch, for which we can know the "ground truth" of the system.

## Overview

The basic process of study with the VBP is as follows:

1. Specify and generate a so-called known ground-truth (KGT) model. Everything
   about this model is presumed to be an accurate and faithful implementation of
   its real structure and function.

2. Specify and generate a data acquisition setup and acquisition procedure (ACQ).
   These are sets of virtual data acquisition devices that are applied to the
   KGT in a specified manenr. Acquire data from the KGT.

3. Specify and generate an experimental process of system identification to be
   applied to the data acquired from the KGT. The system identificatoin and
   translation (SIT) procedure is used to generate model system architectures
   and to estimate the parameters in those models by translating measurements
   acquired from the KGT.

4. Evaluate the resulting emulation model (EM) by collecting data from the emulation
   and by carrying out comparative performance tests and validation procedures to
   determine how well the KGT is emulated.

In this example, the process steps are carried out by corresponding scripts:

1. `aifinch_groundtruth.py`: Specify and genereate known ground-truth (KGT) model.

2. `aifinch_acquisition.py`: Specify and genereate a data acquisition setup and
   procedure, and acquire data from the KGT.

3. `aifinch_translation.py`: Specify and generate the system identification process.

4. `aifinch_emulation.py`: Implement, run, and evaluate emulation models.

## About `aifinch_groundtruth.py`

The main steps in the `aifinch_groundtruth.py` script are:

1. Define the aifinch long-term memory neuronal storage:
   This sets up an artificial set of brain regions containing neural circuitry that
   can store memory patterns. This step defines both the 3D geometric aspects of the
   brain regions involved, as well as their physiological content, its arrangement,
   and its connectivity.

2. Initialize the stored patterns for a selection of song melodies:
   This sets up the memory patterns for a set of known song melodies.

3. Specify a semi-abstract method of memory retrieval:
   This sets up a simplified process that can elicit and respond to the retrieval
   of stored memory patterns by using cues. We can do this in the AI Finch, because
   it is up to us to specify how the ground-truth system of the AI Finch works

4. Specify melody sound production:
   This connects a prosthetic process for melody delivery that can interpret retrieved
   memory pattern activity to generate melodic sound. Producing melodies from memory
   read-out creates a useful real-world connection for the example study.

5. Specify known ground-truth "God's eye" data output:
   These are a set of utilities that allow us to inspect features, states and dynamic
   characteristics of the running KGT. It can produce data that would be invisible or
   unobtainable to the data acquisition methods available in subsequent steps. The
   complete and absolute insight this offers into the KGT is the "God's eye" view and
   is principally responsible for our ability to evaluate the true performance of an
   emulation of this system.

6. Default KGT run:
   This is the test run that is carried out when no alternatives are requested or
   specified through command line input or runtime controls.

### Suggested variations to explore

Studying the effect of different characteristics of the ground-truth system on data
acquisition, system identification, and emulation performance is an essential part of
a Translation study, because these fundamentals directly affect scale separation and
robustness.

The following is a list of parameters in `aifinch_groundtruth.py` for which exploration
of variants may be promising:

- Number of principal nodes (`NUM_NODES`) in the memory network.
- Shape of brain region. This affects the density of nodes, the paths taken by
  connectivity. Geometric features that interact with the capabilities of data
  acquisition tools.
- Degree of intrinsic connectivity within the defined memory network.
- The type of the connectivity arrangement in the memory network, e.g. try alternatives
  to the `AIF_DistributedAutoAssociatve_NC()` neuronal circuit layout generator.
- Simplicity vs complexity of a song melody.
- Pattern size and pattern overlap in sequences representing melodies.
- Binary vs graded synaptic strengths in the encoding.
- (More...)

## About `aifinch_acquisition.py`

The main steps in the `aifinch_acquisition.py` script are:

1. Instantiate or import the known ground-truth system.

2. Set up functional recording tools and procedures.

3. Specify structure scanning tools and procedures.

4. Default ACQ run:
   This are the test run and test acquisition that are carried out when no alternatives
   are requested or specified through command line input or runtime controls.

### Suggested variations to explore

- Functional recording at different recording site densities and arrangements.
- Functional recording at several recording frequencies.
- Functional recording at different SNR ratios.
- Functional recording for different durations, over multiple periods of stimulation protocols.
- Structure imaging with different types of microscopes.
- Structure imaging of different block or section sizes.
- Structure imaging with different amounts of material loss between blocks or sections.
- Structure imaging with different degrees of sample errors (e.g. folds, breaks).
- Structure imaging at several xy pixel resolutions.
- Structure imaging with different degrees of optical errors (focus, contrast, SNR, etc.).

## About `aifinch_translation.py`

The main steps in the `aifinch_translation.py` script are:

1. Instantiate or import the known ground-truth and acquisition systems.

2. Set up the model selection and layout derivation process.

3. Set up the structure translation and parameter estimation process.

4. Set up the functional translation and parameter estimation process.

5. Default System Identification and Translation run.

## About `aifinch_emulation.py`

The main steps in the `aifinch_emulation.py` script are:

1. Instantiate or import the known ground-truth, acquisition systems, and system identification
   and translation process.

2. Set up the emulation.
   Use the derived layout of models and their estimated parameters to build an
   emulation of the AI Finch long term memory for songs.

3. Memory stimulation patterns for both ground-truth and emulated systems.

4. Set up knowth-truth input and output delivery.

5. Set up emulation output and output delivery.

6. Default performance evaluation comparing ground-truth and emulated behavior and output responses.
   Elicit all of the song memories in the validation data set in both the ground-truth and emulated
   AI Finch systems. Compare the resulting singing behavior and the resulting spike responses.

### Suggested variations to explore

- A better way to separate out learning and validation data sets from the set of song melodies,
  or using sample-replace methods used in ML to work with smaller data sets in both cases.
- Stimulating both KGT and EM systems with a distribution of extracellular electrodes or some
  other stimulation method (e.g. simulated optrodes) instead of assuming full patch-clamping.
- In addition to evaluating observable behavior and output responses, evaluate activity internal
  to the emulated region, how output responses are produced.

## TODO notes:

- Try to include in the specifications a clear place for embodiment and a clear place for the application
  of success criteria and making explicit use of constraints.
- Carry out minimum specifications for the deeper functions to a point where they begin to look sufficiently
  understandable to someone who is not me.
- Check the outline specifications of each to ensure that they describe enough for Thomas/Alan to take it from there.
- Make sure the documentation here is sufficient to understand how to use the scripts.
- Take insights from here, including variants to explore, to the session presentations and materials preparation.

---
Randal A. Koene, 20230215
