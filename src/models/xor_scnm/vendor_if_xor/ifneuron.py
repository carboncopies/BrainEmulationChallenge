# Vendored from IFneuron-model/In_Domain/In_Domain_Data_Generation/IFneuron.py
# (Integrate-and-fire neuron for XOR black-box SUB.)

import numpy as np
import scipy.stats as stats
from typing import List, Tuple, Optional, Dict


def dblexp(amp: float, tau_rise: float, tau_decay: float, tdiff: float) -> float:
    if tdiff < 0:
        return 0.0
    return amp * (-np.exp(-tdiff / tau_rise) + np.exp(-tdiff / tau_decay))


class IFneuron:
    def __init__(self, id: str):
        self.id = id
        self.t_directstim_ms: List[float] = []
        self.t_directstim_ms_orig: List[float] = []
        self.Vm_mV: float = -60.0
        self.Vrest_mV: float = -60.0
        self.Vact_mV: float = -50.0
        self.Vahp_mV: float = -20.0
        self.tau_AHP_ms: float = 30.0
        self.tau_PSPr: float = 5.0
        self.tau_PSPd: float = 25.0
        self.vPSP: float = 20.0
        self.tau_spont_mean_stdev_ms: Tuple[float, float] = (0, 0)
        self.t_spont_next: float = -1
        self.dt_spont_dist: Optional[stats.rv_continuous] = None
        self.receptors: List[Tuple["IFneuron", float]] = []
        self.t_ms: float = 0
        self._has_spiked: bool = False
        self.in_absref: bool = False
        self.t_act_ms: List[float] = []
        self._dt_act_ms: Optional[float] = None
        self.t_recorded_ms: List[float] = []
        self.Vm_recorded: List[float] = []

    def attach_direct_stim(self, t_ms: float):
        self.t_directstim_ms.append(t_ms)

    def set_spontaneous_activity(self, mean_stdev: Tuple[float, float]):
        self.tau_spont_mean_stdev_ms = mean_stdev
        mu, sigma = self.tau_spont_mean_stdev_ms
        if mu == 0 or sigma == 0:
            self.dt_spont_dist = None
            return
        a, b = 0, 2 * mu
        self.dt_spont_dist = stats.truncnorm(
            (a - mu) / sigma, (b - mu) / sigma, loc=mu, scale=sigma
        )

    def record(self, t_ms: float):
        self.t_recorded_ms.append(t_ms)
        self.Vm_recorded.append(self.Vm_mV)

    def has_spiked(self) -> bool:
        self._has_spiked = len(self.t_act_ms) > 0
        return self._has_spiked

    def dt_act_ms(self, t_ms: float) -> float:
        if self._has_spiked:
            self._dt_act_ms = t_ms - self.t_act_ms[-1]
            return self._dt_act_ms
        return 1e9

    def vSpike_t(self, t_ms: float) -> float:
        if not self._has_spiked:
            return 0.0
        self.in_absref = self._dt_act_ms <= 1.0
        if self.in_absref:
            return 60.0
        return 0.0

    def vAHP_t(self, t_ms: float) -> float:
        if not self._has_spiked or self.in_absref:
            return 0.0
        return self.Vahp_mV * np.exp(-self._dt_act_ms / self.tau_AHP_ms)

    def vPSP_t(self, t_ms: float) -> float:
        vPSPt = 0.0
        for src_cell, weight in self.receptors:
            if src_cell.has_spiked():
                dtPSP = src_cell.dt_act_ms(t_ms)
                vPSPt += dblexp(weight * self.vPSP, self.tau_PSPr, self.tau_PSPd, dtPSP)
        return vPSPt

    def update_Vm(self, t_ms: float, recording: bool):
        if self.has_spiked():
            self.dt_act_ms(t_ms)
        vSpike_t = self.vSpike_t(t_ms)
        vAHP_t = self.vAHP_t(t_ms)
        vPSP_t = self.vPSP_t(t_ms)
        self.Vm_mV = self.Vrest_mV + vSpike_t + vAHP_t + vPSP_t
        if recording:
            self.record(t_ms)

    def detect_threshold(self, t_ms: float):
        if not self.in_absref and self.Vm_mV >= self.Vact_mV:
            self.t_act_ms.append(t_ms)

    def spontaneous_activity(self, t_ms: float):
        if self.in_absref:
            return
        mu = self.tau_spont_mean_stdev_ms[0]
        if mu == 0:
            return
        if t_ms >= self.t_spont_next:
            if self.t_spont_next >= 0:
                self.t_act_ms.append(t_ms)
            dt_spont = float(self.dt_spont_dist.rvs(1)[0])
            self.t_spont_next = t_ms + dt_spont

    def update(self, t_ms: float, recording: bool = False):
        tdiff_ms = t_ms - self.t_ms
        if tdiff_ms < 0:
            return
        if self.t_directstim_ms and self.t_directstim_ms[0] <= t_ms:
            tfire_ms = self.t_directstim_ms.pop(0)
            self.t_act_ms.append(tfire_ms)
        self.update_Vm(t_ms, recording)
        self.detect_threshold(t_ms)
        self.spontaneous_activity(t_ms)
        self.t_ms = t_ms

    def get_recording(self) -> Dict[str, List[float]]:
        return {"Vm": self.Vm_recorded}
