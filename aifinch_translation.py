#!/usr/bin/env python3
# aifinch_translation.py
# Randal A. Koene, 20230215

'''
This file is used to specify and carry out the process of system identification using
data acquired with aifinch_acquisition.py, with model selection and parameter
estimation steps. The result is one or more possible AIFinch emulation representations.
'''

import aifinch_groundtruth as kgt
import aifinch_acquisition as acq

# == Layout Identification and Translation: =============================================================

class ModelSelector:
    def __init__(self):
        pass

class AIF_ModelSelector(ModelSelector):
    '''
    Model selection process.
    '''
    def __init__(self,
        level='pointneurons',):
        self.level = level

class Layout:
    def __init__(self):
        pass

class AIF_Layout(Layout):
    '''
    AI Finch layout blueprint.
    '''
    def __init__(self,):
        pass

class DeriveLayout(Layout):
    '''
    Layout derication process.
    '''
    def __init__(self,
        acquired:dict,
        selection:ModelSelector,
        layout:Layout,):
        self.acquired = acquired
        self.selection = selection
        self.layout = layout

    def model_selection(self):
        pass

    def show(self):
        pass

# == Parameter Estimation and Translation: ==============================================================

class SIT_Method:
    def __init__(self):
        pass

class SIT_FromStructuralData(SIT_Method):
    '''
    Use acquired structure data to estimate parameters.
    '''
    def __init__(self,):
        pass

class SIT_FromFunctionalData(SIT_Method):
    '''
    Use acquired functional data to estimate parameters.
    '''
    def __init__(self,):
        pass

class SIT_ParameterEstimation:
    '''
    System identification and translation method.
    '''
    def __init__(self,
        acquired:dict,
        layout:Layout,
        estimation:SIT_Method,):
        self.acquired = acquired
        self.layout = layout
        self.estimation = estimation

    def system_identification(self):
        pass

    def show(self):
        pass

# == Initialize: ========================================================================================

# Initialize system identification and translation process.
def init(acq_system: dict):
    # TODO:
    # - Either cue the default random selection and acquire dynamic data.
    # - Or make a specific cue selection and data acquisition.

    # 2. Set up the model selection and layout derivation process:
    aif_sit_ltmlayout = DeriveLayout(
        acquired=acq_system,
        selection=AIF_ModelSelector(level='compartmental',),
        layout=AIF_Layout(),)

    # 3. Set up the structure translation and parameter estimation process:
    aif_sit_ltmpars_struc = SIT_ParameterEstimation(
        acquired=acq_system,
        layout=aif_sit_ltmlayout,
        estimation=SIT_FromStructuralData(),)

    # 4. Set up the functional translation and parameter estimation process:
    aif_sit_ltmpars_dyn = SIT_ParameterEstimation(
        acquired=acq_system,
        layout=aif_sit_ltmlayout,
        estimation=SIT_FromFunctionalData(),)

    aif_sit_process = {
        'layout': { 'ltm': aif_sit_ltmlayout, },
        'parameters': { 'ltmdyn': aif_sit_ltmpars_dyn, 'ltmstruc': aif_sit_ltmpars_struc, },
    }
    return aif_sit_process

HELP='''
Usage: aifinch_translation.py [-h]

       -h         Show this usage information.

       This script carries out system identification and translation of data
       acquired from a known ground-truth system, so that models are selected
       and parameters estimated for an emulation.

       Note that emulation building and evaluation are carred out in
       aifinch_emulation.py.

       By default, this script calls class methods in aifinch_acquisition.py
       and aifinch_groundtruth.py to carry out the stages:

       1. Specification of a known ground-truth system and its behavior.
       2. Acquisition of data from the ground-truth system.
       3. System identification and translation.

'''

def parse_command_line():
    from sys import argv

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-h':
            print(HELP)
            exit(0)

if __name__ == '__main__':

    parse_command_line()

    # 1. Instantiate or import the known ground-truth and acquisition systems.
    aif_kgt_system = kgt.init(melodies_notes)
    aif_acq_system = acq.init(aif_kgt_system)

    aif_sit_process = init(aif_acq_system)

    # 5. Default System Identification and Translation run:
    aif_sit_process['layout']['ltm'].model_selection()
    aif_sit_process['parameters']['ltmstruc'].system_identification()
    aif_sit_process['layout']['ltm'].show()
    aif_sit_process['parameters']['ltmstruc'].show()
