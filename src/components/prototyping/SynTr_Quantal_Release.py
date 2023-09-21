# SynTr_Quantal_Release.py
# Randal A. Koene, 20230507

"""
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4748401/
"""


class SynTr_Quantal_Release:
    def __init__(self, N_T_init: int = 10, P_init: float = 0.5):
        """
        In CNS, the number of vesicles ready to fuse with membrane in the presence of Ca2+ and
        cause quantal release is typically between 10-100. For cerebellar MF-GC connections,
        the number is 5-10, 1 vesicle per synaptic contact.
        The release probability is characteristically 0.5.
        """
        self.N_T: int = N_T_init  # total number of quanta available for release
        self.P: float = P_init  # release probability

    def quantal_content_m(self) -> float:
        return self.N_T * self.P
