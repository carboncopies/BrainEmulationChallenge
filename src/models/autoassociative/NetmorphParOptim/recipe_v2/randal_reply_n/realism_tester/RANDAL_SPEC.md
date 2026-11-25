Come to think of it, now that we are modifying parts of the NES API and
potentially also aspects of Netmorph, what we should really do is build a
"realism-tester" (which could be integrated in NES or be a Python tool that
we apply to data about models created). For any given type of example (e.g.
something that should be CA3-like, or Drosophila mushroom body-like, or
V1-like, etc) we would provide a list of important realism checks, such as:

- Proportions of different cells present.
- Numbers of cells per volume.
- Average density of cells per cell type.
- Average total dendrite length (over all segments, all branches) per cell
type.
- Average total axon length (over all segments, all branches) per cell type.
- Average and max spherical range of dendrites per cell type (how far do
they reach).
- Average and max spherical range of axons per cell type (how far do they
reach).
- Average number of target cells innervated (connected to) per cell type,
and per target cell type.
- Average number of source cells (connected from) per cell type, and per
source cell type.
- Average number of synapses on axons and dendrites per cell type.
- 3D heat map data for the density of axon and dendrite volume in a given
3D location of the model volume (this would highlight where axons/dendrite
are sparse vs where they might be all balling together).

(I'm not totally sure we should be checking averages or medians, perhaps
both.)

We can calculate the numbers for all of those given the 3D model created
(either from morphology data directly from Netmorph or morphology data from
NES after the model was converted).
We can compare those numbers with numbers (statistics) from literature for
the biological equivalents of the regions our examples are attempting to
represent. Where the specific numbers can be found, great, where not, we
can use numbers from (similar) tissue of the same animal, or we can try to
derive reasonable estimates (which could be a separate step of building
this testing app).
It would be very nice if the app can show its results in a browser page, so
that its convenient to inspect them (including the heat map and comments
about it).

