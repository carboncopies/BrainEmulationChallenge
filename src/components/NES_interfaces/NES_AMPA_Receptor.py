# NES_AMPA_Receptor.py
# Randal A. Koene, 20230507

"""
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4748401/
"""

import numpy as np
import json


class NES_AMPA_Receptor:
    """
    Use this class as a convenient stand-in that carries out actual instantiation
    and all method calls through the NES API.
    """

    def __init__(
        self,
        ID="0",
        Gsyn_pS_init: float = 0,
        Esyn_mV_init: float = 0,
        Vm_mV_init: float = 0,
        Isyn_pA_init: float = 0,
        tau_d_ms_init: float = 2.0,
        tau_r_ms_init: float = 0.2,
        tau_d2_ms_init: float = 3.0,
        tau_d3_ms_init: float = 4.0,
        d1_init: float = 0.5,
        d2_init: float = 0.3,
        d3_init: float = 0.2,
        x_init: float = 1.5,
        g_peak_pS_init: float = 39,
        a_norm_init: float = 1.0,
    ) -> None:
        API_call(
            "NES/AMPAR/init",
            json.dumps(
                {
                    "ID": ID,
                    "Gsyn_pS_init": Gsyn_pS_init,
                    "Esyn_mV_init": Esyn_mV_init,
                    "Vm_mV_init": Vm_mV_init,
                    "Isyn_pA_init": Isyn_pA_init,
                    "tau_d_ms_init": tau_d_ms_init,
                    "tau_r_ms_init": tau_r_ms_init,
                    "tau_d2_ms_init": tau_d2_ms_init,
                    "tau_d3_ms_init": tau_d3_ms_init,
                    "d1_init": d1_init,
                    "d2_init": d2_init,
                    "d3_init": d3_init,
                    "x_init": x_init,
                    "g_peak_pS_init": g_peak_pS_init,
                    "a_norm_init": a_norm_init,
                }
            ),
        )

    def set_psp_type(self, psp_type: str):
        API_call(
            "NES/AMPAR/set_psp_type",
            json.dumps(
                {
                    "ID": ID,
                    "psp_type": psp_type,
                }  # 'dblexp' or 'mxh'
            ),
        )

    # PROPOSAL 1: Waiting for a response can be a blocking await function as
    # shown here.
    # PROPOSAL 2: Waiting can be done in the background by making this an
    # async function and using 'await API_response()'.
    def np_Gsyn_t_pS_dbl(self, t_ms: np.ndarray) -> np.ndarray:
        API_call(
            "NES/AMPAR/np_Gsyn_t_pS_dbl",
            json.dumps(
                {
                    "ID": ID,
                    "t_ms": t_ms,
                }
            ),
        )
        resp = await_API_response("NES/AMPAR/np_Gsyn_t_pS_dbl", ID)
        if resp is None:
            raise Exception(get_API_error())
        if "error" in resp:
            raise Exception(resp["error"])
        return resp["Gsyn_t_pS"]

    # PROPOSAL 3: Instead of waiting, the API_call() function could be supplied
    # with a callback function reference, which is placed into a hash map and
    # called when a matching response is received (or timeout happens).
    def np_Gsyn_t_pS_dbl_withcallback(self, t_ms: np.ndarray) -> bool:
        API_call(
            "NES/AMPAR/np_Gsyn_t_pS_dbl",
            json.dumps(
                {
                    "ID": ID,
                    "t_ms": t_ms,
                }
            ),
            callback=self.np_Gsyn_t_pS_dbl_handle,
        )
        return True

    def np_Gsyn_t_pS_mxh(self, t_ms: np.ndarray) -> np.ndarray:
        API_call(
            "NES/AMPAR/np_Gsyn_t_pS_mxh",
            json.dumps(
                {
                    "ID": ID,
                    "t_ms": t_ms,
                }
            ),
        )
        resp = await_API_response("NES/AMPAR/np_Gsyn_t_pS_mxh", ID)
        if resp is None:
            raise Exception(get_API_error())
        if "error" in resp:
            raise Exception(resp["error"])
        return resp["Gsyn_t_pS"]

    def np_Gsyn_t_pS_mxh_withcallback(self, t_ms: np.ndarray) -> bool:
        API_call(
            "NES/AMPAR/np_Gsyn_t_pS_mxh",
            json.dumps(
                {
                    "ID": ID,
                    "t_ms": t_ms,
                }
            ),
            callback=self.np_Gsyn_t_pS_mxh_handle,
        )
        return True
