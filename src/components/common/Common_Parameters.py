# Common_Parameters.py
# Randal A. Koene, 20240101

'''
Parameters and command line parsing common to most scripts.
'''

import numpy as np
from datetime import datetime
from os import makedirs

class Common_Parameters:
    def __init__(self, scriptpath:str):
        self.scriptpath = scriptpath
        self.show = {
            'text': False,
            'regions': False,
            'cells': False,
            'voxels': False,
        }
        self.runtime_ms = 500.0
        self.randomseed = None
        self.savefolder = '/tmp/vbp_'+datetime.now().strftime("%F_%X")
        self.api_is_local = False
        self.linewidth = 0.5
        self.figsize = (6,6)
        self.figext = 'pdf'
        self.extra = {}
    def figspecs(self)->dict:
        return {
            'figsize': self.figsize,
            'linewidth': self.linewidth,
            'figext': self.figext,
        }
    def fullpath(self, file:str)->str:
        if file[0]=='/':
            return file
        return self.savefolder + '/' + file

COMMON_HELP='''
       -h         Show this usage information.
       -v         Be verbose, show all diagrams.
       -V         Show specified output (multiple -V statements allowed).
                  Options are: all, text, regions, cells, voxels.
       -t         Run for ms milliseconds.
       -R         Set random seed.
       -d         Directory to save to (default is /tmp/vbp_<datetime>.
       -l         Line width (default=0.5).
       -f         Figure size in inches (default=6.0).
       -x         Figure file type extension (default=pdf).
       -p         Run prototype code (default is NES interface).
       -a         NES interface API is running locally.
'''

def common_commandline_parsing(cmdline:list, pars:Common_Parameters, HELP:str)->str:
    arg = cmdline.pop(0)
    if arg == '-h':
        print(HELP)
        exit(0)
    elif arg== '-v':
        pars.show = {
            'text': True,
            'regions': True,
            'cells': True,
            'voxels': True,
        }
        return None
    elif arg== '-V':
        diagram = cmdline.pop(0)
        if diagram in pars.show:
            pars.show[diagram] = True
        elif diagram == 'all':
            pars.show = {
            'text': True,
            'regions': True,
            'cells': True,
            'voxels': True,
        }
        return None
    elif arg== '-t':
        pars.runtime_ms = float(cmdline.pop(0))
        return None
    elif arg== '-R':
        pars.randomseed = int(cmdline.pop(0))
        np.random.seed(pars.randomseed)
        return None
    elif arg== '-d':
        pars.savefolder = str(cmdline.pop(0))
        return None
    elif arg== '-l':
        pars.linewidth = float(cmdline.pop(0))
        return None
    elif arg== '-f':
        fig_side_size = float(cmdline.pop(0))
        pars.figsize = (fig_side_size, fig_side_size)
        return None
    elif arg== '-x':
        pars.figext = str(cmdline.pop(0))
        return None
    elif arg== '-p':
        return None
    elif arg== '-a':
        pars.api_is_local = True
        return None
    return arg

def make_savefolder(pars:Common_Parameters):
    makedirs(pars.savefolder, exist_ok=True)
    print('Saving output to %s.' % pars.savefolder)
