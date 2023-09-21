#!/usr/bin/env python3
# aifinch_emulation.py
# Randal A. Koene, 20230215

"""
This file is used to run, validate and test AIFinch emulations that were
generated with aifinch_translation.py.
"""
import aifinch_groundtruth as kgt
import aifinch_acquisition as acq
import aifinch_translation as sit

# == EM Model Building: =================================================================================


class BuildEmulation:
    """
    Use the derived layout of models and their estimated parameters to build an emulation.
    """

    def __init__(
        self,
        sit_result: dict,
    ):
        self.sit_result = sit_result
        # TODO:
        # - Much more!


# == Evaluation Methods: ================================================================================


class EvaluateBehavior:
    """
    Evaluate behavioral performance, comparing behavior of a ground-truth system with that of
    an emulated system.
    """

    def __init__(
        self,
        kgt_behavior: Region,
        em_behavior: Region,
    ):
        self.kgt_behavior = kgt_behavior
        self.em_behavior = em_behavior

    def show():
        pass


class EvaluateOutputActivity:
    """
    Evaluate neuronal response performance, comparing responses of a ground-truth system with that of
    an emulated system.
    """

    def __init__(
        self,
        kgt_resp: Region,
        em_resp: Region,
    ):
        self.kgt_resp = kgt_resp
        self.em_resp = em_resp

    def show():
        pass


# == Initialize: ========================================================================================


def init(kgt_system: dict, sit_process: dict):
    # TODO:
    # - Either cue the default random selection, acquire dynamic data, carry out
    #   model selection and system identification.
    # - Or make a specific cue selection with data acquisition, carry out a
    #   specific model selection process and system identification method.

    # 2. Set up the emulation:
    aif_em_model = BuildEmulation(
        sit_result=sit_process,
    )

    # 3. Memory stimulation patterns for both ground-truth and emulated systems:
    # TODO:
    # - Either reuse the same setup as in aifinch_groundtruth.py or set something
    #   just like it up with validation data.
    aif_validation_cues = PatternGenerator(songs)

    # 4. Set up knowth-truth input and output delivery:
    aif_kgt_in = RegionPath(
        src=aif_validation_cues,
        dst=kgt_system["regions"]["ltm"],
        method=["1-1", "patchclamp"],
    )
    aif_kgt_resp = SpikeMonitor()
    aif_kgt_out = RegionPath(
        src=kgt_system["regions"]["ltm"],
        dst=kgt_system["regions"]["resp"],
        method=["1-1", "patchclamp"],
    )
    aif_kgt_singing_finch = NotesToSound(soundlib="finch_trills.wav")
    aif_kgt_vocalization = PatternMapper(
        src=aif_kgt_resp, dst=aif_kgt_singing_finch, method="nearest"
    )

    # 5. Set up emulation output and output delivery:
    aif_em_in = RegionPath(
        src=aif_validation_cues, dst=aif_em_model, method=["1-1", "patchclamp"]
    )
    aif_em_resp = SpikeMonitor()
    aif_em_out = RegionPath(
        src=aif_em_model,
        dst=kgt_system["regions"]["resp"],
        method=["1-1", "patchclamp"],
    )
    aif_em_singing_finch = NotesToSound(soundlib="finch_trills.wav")
    aif_em_vocalization = PatternMapper(
        src=aif_em_resp, dst=aif_em_singing_finch, method="nearest"
    )

    aif_em_eval_system = {
        "em_model": {
            "ltm": aif_em_model,
        },
        "val_data": {
            "cue": aif_validation_cues,
        },
        "systems": {
            "kgt": {
                "regions": {
                    "cue": aif_validation_cues,
                    "ltm": kgt_system["regions"]["ltm"],
                    "resp": aif_kgt_resp,
                },
                "pathways": {
                    "cue": aif_kgt_in,
                    "resp": aif_kgt_out,
                    "singing": aif_kgt_vocalization,
                },
                "embodiment": {
                    "singing": aif_kgt_singing_finch,
                },
            },
            "em": {
                "regions": {
                    "cue": aif_validation_cues,
                    "ltm": aif_em_model,
                    "resp": aif_em_resp,
                },
                "pathways": {
                    "cue": aif_em_in,
                    "resp": aif_em_out,
                    "singing": aif_em_vocalization,
                },
                "embodiment": {
                    "singing": aif_em_singing_finch,
                },
            },
        },
    }
    return aif_em_eval_system


HELP = """
Usage: aifinch_emulation.py [-h]

       -h         Show this usage information.

       This script builds an emulation of the AI Finch based on results of
       system identification and translation, and it carries out an evaluation
       of the emulation by comparing performance and behavior with that of the
       ground-truth AI Finch system.

       By default, this script calls class methods in aifinch_translation.py,
       aifinch_acquisition.py, and aifinch_groundtruth.py to carry out all
       stages:

       1. Specification of a known ground-truth system and its behavior.
       2. Acquisition of data from the ground-truth system.
       3. System identification and translation.
       4. Building and evaluating the emulated system.

"""


def parse_command_line():
    from sys import argv

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == "-h":
            print(HELP)
            exit(0)


if __name__ == "__main__":
    parse_command_line()

    # 1. Instantiate or import the known ground-truth, acquisition systems, and system identification
    #    and translation process:
    aif_kgt_system = kgt.init(melodies_notes)
    aif_acq_system = acq.init(aif_kgt_system)
    aif_sit_process = sit.init(aif_acq_system)

    aif_em_eval_system = init(aif_kgt_system, aif_sit_process)

    # 6. Default performance evaluation comparing ground-truth and emulated behavior:
    #    Generate random cues for the KGT sytstem and for the emulation.
    #    Record responses and compare.
    aif_em_eval_system["systems"]["kgt"]["regions"]["cue"].all(
        cue_pattern_ratio=0.4, cue_sequence_length=3
    )
    aif_em_eval_system["systems"]["em"]["regions"]["cue"].all(
        cue_pattern_ratio=0.4, cue_sequence_length=3
    )
    behavior = EvaluateBehavior(
        kgt_behavior=aif_em_eval_system["systems"]["kgt"]["embodiment"],
        em_behavior=aif_em_eval_system["systems"]["em"]["embodiment"],
    )
    responses = EvaluateOutputActivity(
        kgt_resp=aif_em_eval_system["systems"]["kgt"]["regions"]["resp"],
        em_resp=aif_em_eval_system["systems"]["em"]["regions"]["resp"],
    )

    behavior.show()
    responses.show()
