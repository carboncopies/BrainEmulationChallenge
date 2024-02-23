# glb.py
# Randal A. Koene, 20240125

'''
Global reference values. Imported and used throughout modules and programs.

We use these globals so that we do not need to pass objects such as BG_API
to every call that needs some of its functions whether using NES or
prototype code (it gets messy, trust me).

NOTE: Do 'import common.glb as glb' and refer to variables as glb.<var>.
      Do not do 'from .common.glb import <var>'', as that may make a copy
      (especially if <var> was still set to None), while you want a
      reference to the same created object.
'''

# Reference to BG_API object set by BG_API_Setup.
global bg_api
bg_api = None
