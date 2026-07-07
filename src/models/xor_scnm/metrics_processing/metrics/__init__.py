# metrics/__init__.py  

from metrics.spike_train.behavioural import run as behavioural, report as behavioural_report
from metrics.voltage_dependent.vm_visualization import run as vm_visualization
from metrics.information_theory.entropy import run as entropy, report as entropy_report
from metrics.information_theory.joint_entropy import run as joint_entropy, report as joint_entropy_report 

METRICS = [
    #{"name": "behavioural",  "run": behavioural,  "report": behavioural_report},
    #{"name": "vm_visualization", "run": vm_visualization, "report": None},
    #{"name":entropy, "run": entropy, "report": entropy_report},
    {"name":joint_entropy, "run": joint_entropy, "report": joint_entropy_report}
]