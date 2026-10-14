#!../../../venv/bin/python
# test_generated_config.py
# Randal A. Koene, 20261014

# Tests a Netmorph configuration file produced by the browser based
# Netmorph configuration tool (or written by hand), independent of
# any specific example model.
#
# Based on autoassociative_reservoir.py, but simplified:
# - The configuration is used as-is. No region names or neuron
#   counts are injected, because a generated file can define any
#   regions. Only the growth days can optionally be overridden.
# - A local preflight check parses the file and reports regions,
#   expected neuron counts and suspicious statements before NES
#   is contacted. Use -checkonly to stop after the preflight.
# - After growth, the connectome is retrieved and summarized, and
#   the summary is compared with the neuron counts expected from
#   the configuration.
#
# For example:
#   ./test_generated_config.py -configfile ../autoassociative/nesvbp-autoassociative -checkonly
#   ./test_generated_config.py -configfile my-generated-config
#   ./test_generated_config.py -configfile my-generated-config -growdays 5 -modelname mytest

scriptversion='0.1.0'

import json
import argparse
import os

import vbpcommon as vbp

Parser = argparse.ArgumentParser(description="Test a generated Netmorph configuration file with NES")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-configfile", required=True, type=str, help="Generated Netmorph configuration file to test")
Parser.add_argument("-modelname", default="", type=str, help="If given, save the grown model at the NES server under this name")
Parser.add_argument("-growdays", default=0, type=int, help="Override number of days of Netmorph growth (0 means use the configuration value)")
Parser.add_argument("-checkonly", action='store_true', help="Only run the local preflight check, do not contact NES")
Parser.add_argument("-outdir", default="output", type=str, help="Directory for plots and the summary file")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Args = Parser.parse_args()

DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'configtest',
    scriptversion,
    _initIN = {
        'configfile': Args.configfile,
        'growdays_override': str(Args.growdays),
    },
    _initOUT = {
        'modelname': Args.modelname,
    })

FIGSPECS={ 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }

# Receptor type IDs used in ConnectionTypes (see vbpcommon.PlotAndStoreConnections)
RECEPTOR_TYPES = { 1: 'AMPA', 2: 'GABA', 3: 'NMDA' }

# Netmorph statements that may legitimately appear more than once
REPEATABLE = [ 'substitute', 'include' ]


# ----- Preflight: parse the configuration locally -----

def parse_netmorph_config(content:str)->tuple:
    '''
    Parses Netmorph 'name=value;' statements, ignoring '#' comments.
    Returns (params dict, list of warnings). Later assignments
    override earlier ones, as when appending overrides to a model.
    Repeatable statements (e.g. substitute=) are collected as lists.
    '''
    params = { name: [] for name in REPEATABLE }
    warnings = []
    lines = [ line.split('#', 1)[0] for line in content.splitlines() ]
    statements = ' '.join(lines).split(';')
    if statements[-1].strip():
        warnings.append('Trailing text without terminating ";": '+statements[-1].strip())
    for statement in statements[:-1]:
        statement = statement.strip()
        if not statement:
            continue
        if '=' not in statement:
            warnings.append('Statement without "=": '+statement)
            continue
        name, value = statement.split('=', 1)
        name = name.strip()
        if not name or ' ' in name:
            warnings.append('Suspicious parameter name in: '+statement)
        if '=' in value:
            warnings.append('Possibly missing ";" in: '+statement)
        if name in REPEATABLE:
            params[name].append(value.strip())
            continue
        if name in params and params[name] != value.strip():
            warnings.append('Parameter %s reassigned from %s to %s' % (name, params[name], value.strip()))
        params[name] = value.strip()
    return params, warnings

def int_param(params:dict, name:str, warnings:list)->int:
    if name not in params:
        return 0
    try:
        return int(params[name])
    except ValueError:
        warnings.append('Parameter %s is not an integer: %s' % (name, params[name]))
        return 0

def preflight(params:dict, warnings:list)->dict:
    '''
    Extracts the expected network architecture from the parsed parameters.
    '''
    for required in [ 'days', 'shape' ]:
        if required not in params:
            warnings.append('Missing parameter: '+required)
    for included in params['include']:
        warnings.append('include=%s is not expanded here and must be resolvable by Netmorph on the NES server' % included)

    regions = {}
    if params.get('shape') == 'regions':
        if 'regions' not in params:
            warnings.append('shape=regions but no regions parameter')
        regionnames = [ r.strip() for r in params.get('regions', '').split(',') if r.strip() ]
        for region in regionnames:
            pyramidal = int_param(params, region+'.pyramidal', warnings)
            interneuron = int_param(params, region+'.interneuron', warnings)
            neurons = int_param(params, region+'.neurons', warnings)
            if region+'.shape' not in params:
                warnings.append('Region %s has no shape' % region)
            if pyramidal + interneuron + neurons == 0:
                warnings.append('Region %s has no neurons' % region)
            regions[region] = {
                'pyramidal': pyramidal,
                'interneuron': interneuron,
                'other': neurons,
            }
        # Parameters prefixed with a name that is not a region, a cell type,
        # an all_* selector or a declared label may be typos in region names.
        # Labels are declared by substitute=LABEL:..., *.prefix=LABEL and *_label=LABEL.
        known_prefixes = set(regionnames) | { 'pyramidal', 'interneuron', 'pia', 'tsem', 'eri' }
        known_prefixes |= { s.split(':', 1)[0].strip() for s in params['substitute'] }
        known_prefixes |= { value for name, value in params.items() if name not in REPEATABLE and (name.endswith('.prefix') or name.endswith('_label')) }
        unknown_prefixes = sorted({ name.split('.', 1)[0] for name in params if '.' in name and not name.startswith('all_') } - known_prefixes)
        if unknown_prefixes:
            warnings.append('Parameter prefixes that are not declared regions (check they are intended): '+', '.join(unknown_prefixes))

    expected_total = sum([ r['pyramidal'] + r['interneuron'] + r['other'] for r in regions.values() ])
    return {
        'days': params.get('days'),
        'randomseed': params.get('randomseed'),
        'regions': regions,
        'expected_neurons': expected_total,
        'expected_pyramidal': sum([ r['pyramidal'] for r in regions.values() ]),
        'expected_interneuron': sum([ r['interneuron'] for r in regions.values() ]),
    }

try:
    with open(Args.configfile, 'r') as f:
        modelcontent = f.read()
except Exception as e:
    vbp.ErrorExit(DBdata, 'configfile error: '+str(e))

params, warnings = parse_netmorph_config(modelcontent)
architecture = preflight(params, warnings)
vbp.AddOutputToDB(DBdata, 'preflight', { 'architecture': architecture, 'warnings': warnings })

print(' -- Preflight check of '+Args.configfile)
print('    Parameters parsed: %d' % len(params))
print('    Growth days: %s' % str(architecture['days']))
for region, counts in architecture['regions'].items():
    print('    Region %s: %d pyramidal, %d interneuron, %d other' % (region, counts['pyramidal'], counts['interneuron'], counts['other']))
print('    Expected neurons: %d' % architecture['expected_neurons'])
for warning in warnings:
    print('    WARNING: '+warning)

if Args.checkonly:
    vbp.UpdateExpsDB(DBdata)
    print(' -- Done (check only).')
    exit(0)

if Args.growdays:
    modelcontent += '\ndays=%d;\n' % Args.growdays


# ----- Grow the network with Netmorph in NES -----

ClientCfg, ClientInstance = vbp.ClientFromArgs(DBdata, Args)
SimulationCfg, MySim = vbp.NewSimulation(DBdata, ClientInstance, 'Netmorph-configtest')

MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors

RunResponse = MySim.Netmorph_RunAndWait(modelcontent, _NeuronClass='LIFC')
if not RunResponse["Success"]:
    vbp.ErrorExit(DBdata, 'NES.Netmorph error: Netmorph build failed with status response: '+str(RunResponse["NetmorphStatus"]))

vbp.AddOutputToDB(DBdata, 'NetmorphOutputDirectory', str(RunResponse["NetmorphOutputDirectory"]))
print(" -- Netmorph output files directory is "+str(RunResponse["NetmorphOutputDirectory"]))

if Args.modelname:
    try:
        MySim.ModelSave(Args.modelname)
        print(" -- Neuronal Circuit Model saved as "+Args.modelname)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Model save failed')


# ----- Retrieve and summarize the connectome -----

def summarize_connectome(connections_dict:dict)->dict:
    targets = connections_dict['ConnectionTargets']
    types = connections_dict['ConnectionTypes']
    numreceptors = connections_dict['NumReceptors']
    numneurons = len(targets)

    connections_by_type = { name: 0 for name in RECEPTOR_TYPES.values() }
    receptors_by_type = { name: 0 for name in RECEPTOR_TYPES.values() }
    excitatory = set()  # neurons with outgoing AMPA (pyramidal)
    inhibitory = set()  # neurons with outgoing GABA (interneuron)
    has_input = set()
    autapses = 0
    for pre in range(numneurons):
        for i in range(len(targets[pre])):
            typename = RECEPTOR_TYPES.get(types[pre][i], 'unknown')
            connections_by_type[typename] = connections_by_type.get(typename, 0) + 1
            receptors_by_type[typename] = receptors_by_type.get(typename, 0) + numreceptors[pre][i]
            if typename == 'AMPA':
                excitatory.add(pre)
            elif typename == 'GABA':
                inhibitory.add(pre)
            has_input.add(targets[pre][i])
            if targets[pre][i] == pre:
                autapses += 1

    has_output = { pre for pre in range(numneurons) if len(targets[pre]) > 0 }
    return {
        'neurons': numneurons,
        'connections_by_type': connections_by_type,
        'receptors_by_type': receptors_by_type,
        'neurons_with_AMPA_output': len(excitatory),
        'neurons_with_GABA_output': len(inhibitory),
        'neurons_without_output': numneurons - len(has_output),
        'neurons_without_input': numneurons - len(has_input),
        'autapses': autapses,
    }

try:
    connections_dict = MySim.GetConnectome()
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome: '+str(e))

if connections_dict.get('StatusCode') != 0:
    vbp.ErrorExit(DBdata, 'NES error: connectome request returned status '+str(connections_dict.get('StatusCode')))

summary = summarize_connectome(connections_dict)
vbp.AddOutputToDB(DBdata, 'connectome_summary', summary)

print(' -- Connectome summary')
print(json.dumps(summary, indent=2))

checks = []
if architecture['expected_neurons'] and summary['neurons'] != architecture['expected_neurons']:
    checks.append('Neuron count %d differs from the %d expected from the configuration' % (summary['neurons'], architecture['expected_neurons']))
if summary['neurons_with_AMPA_output'] > architecture['expected_pyramidal']:
    checks.append('More neurons with AMPA output (%d) than pyramidal neurons configured (%d)' % (summary['neurons_with_AMPA_output'], architecture['expected_pyramidal']))
if summary['neurons_with_GABA_output'] > architecture['expected_interneuron']:
    checks.append('More neurons with GABA output (%d) than interneurons configured (%d)' % (summary['neurons_with_GABA_output'], architecture['expected_interneuron']))
if sum(summary['connections_by_type'].values()) == 0:
    checks.append('No connections were formed')
if summary['neurons_without_output'] > 0:
    checks.append('%d neurons make no outgoing connections' % summary['neurons_without_output'])
if summary['neurons_without_input'] > 0:
    checks.append('%d neurons receive no connections' % summary['neurons_without_input'])
for check in checks:
    print('    CHECK: '+check)
vbp.AddOutputToDB(DBdata, 'checks', checks)

os.makedirs(Args.outdir, exist_ok=True)
for receptor in [ 'AMPA', 'GABA' ]:
    if summary['connections_by_type'][receptor] == 0:
        continue
    for usematrix in [ 'weights', 'numreceptors' ]:
        nameappend = 'configtest_%s_%s' % (receptor, usematrix)
        if not vbp.PlotAndStoreConnections(connections_dict, Args.outdir, nameappend, FIGSPECS, receptor=receptor, usematrix=usematrix):
            vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of %s %s' % (receptor, usematrix))

summaryfile = os.path.join(Args.outdir, 'configtest_summary.json')
try:
    with open(summaryfile, 'w') as f:
        json.dump({ 'configfile': Args.configfile, 'architecture': architecture, 'warnings': warnings, 'connectome': summary, 'checks': checks }, f, indent=2)
    print(' -- Summary saved to '+summaryfile)
except Exception as e:
    vbp.ErrorToDB(DBdata, 'File error: Unable to save summary: '+str(e))

vbp.UpdateExpsDB(DBdata)

print(" -- Done.")
