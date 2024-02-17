#!/usr/bin/env python3
# BG_API.py
# Randal A. Koene, 20230624

'''
Common utilities for making REST API requests through the
BrainGenix API.
'''

import requests
import json
import random
from time import sleep

import common.glb as glb
import BrainGenix.NES as NES

class Credentials:
    def __init__(self, user:str, passwd:str):
        self.user = user
        self.passwd = passwd

# This can be used when creating a simulation or when loading a simulation.
# When loading, the simname should be the save-name of the simulation
# (with its timestamp), and the loading flag must be True.
class SimClientInstance:
    def __init__(self, credentials:Credentials, simname:str, host:str='api.braingenix.org', port:int=443, use_https:bool=True, loading:bool=False):
        self.ClientCfg = NES.Client.Configuration()
        self.ClientCfg.Mode = NES.Client.Modes.Remote
        self.ClientCfg.Host = host
        self.ClientCfg.Port = port
        self.ClientCfg.UseHTTPS = use_https
        self.ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
        self.ClientCfg.Username = credentials.user
        self.ClientCfg.Password = credentials.passwd
        self.ClientInstance = NES.Client.Client(self.ClientCfg)
        assert(self.ClientInstance.IsReady())

        self.SimulationCfg = NES.Simulation.Configuration()
        if loading:
            namepos = simname.find('-')
            if namepos<0:
                self.SimulationCfg.Name = "UnNamed"
            else:
                self.SimulationCfg.Name = simname[namepos+1:]
            self.Sim = self.ClientInstance.CreateSimulation(self.SimulationCfg, create=False)
        else:
            self.SimulationCfg.Name = simname
            self.Sim = self.ClientInstance.CreateSimulation(self.SimulationCfg)

# Create one of these through the BG_API_Setup function to ensure
# that it is accessible through the global reference variable bg_api.
class BG_API:
    def __init__(self,
            credentials:Credentials,
            debug_api=True,
            local_port=8000,
            remote_host='api.braingenix.org',
            remote_port=443,
            is_local=False,
        ):
        self.credentials = credentials
        self.Simulation = None
        self.DEBUG_API = debug_api
        self.BGAPI_BASE_URI = None

        # These are used to select the host and port for
        # pyBrainGenixClient calls.
        self.local_backend = False
        self.local_host = 'localhost'
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.uri_host = None
        self.uri_port = None
        self.use_https = True

        self.autonames = [ ]
        self.ReqID = 0

        self.NESRequest_batch = []

        # Initializing the default URI
        if is_local:
            self.set_local()
        else:
            self.set_remote()

    # --------------------------------------------------------------------

    def make_bgapi_base_uri(self, host:str, port:int, use_https:bool):
        self.uri_host = host
        self.uri_port = port
        self.use_https = use_https
        if use_https:
            self.BGAPI_BASE_URI='https://%s:%s' % (host,str(port))
        else:
            self.BGAPI_BASE_URI='http://%s:%s' % (host,str(port))

    def set_local(self):
        self.local_backend = True
        self.make_bgapi_base_uri(self.local_host, self.local_port, use_https=False)

    def set_remote(self):
        self.local_backend = False
        self.make_bgapi_base_uri(self.remote_host, self.remote_port, use_https=True)

    def generate_autoname(self, prepend:str)->str:
        r = random.random()
        r_str = prepend+str(r)
        self.autonames.append(r_str)
        return r_str

    def gen_ReqID(self)->int:
        self.ReqID += 1
        return self.ReqID

    def get_SimID(self)->int:
        if not self.Simulation:
            return -1
        return self.Simulation.Sim.ID

   # --------------------------------------------------------------------

    # Not typically used due to BrainGenix.NES module.
    def API_call_raw(self, uri:str)->requests.Response:
        '''
        Make a raw call through the Braingenix API.
        The REST URI must already be prepared.
        '''
        return requests.get(uri)

    # Not typically used due to BrainGenix.NES module.
    def BGAPI_call(self, rq:str)->requests.Response:
        if self.DEBUG_API: print('Request is: '+str(rq))
        response = requests.get(self.BGAPI_BASE_URI+rq)
        if self.DEBUG_API: print('Response is: '+str(response.text))
        return response

    # Not typically used due to BrainGenix.NES module.
    def BGNES_handle_response(self,
            response:requests.Response,
            caller=str,
            retstrings:list=['StatusCode']
        )->list:

        if response.status_code==200:
            try:
                data = response.json()
                #if data['StatusCode']==0:
                if data['StatusCode']==0 or data['StatusCode']==3: # This is temporary!
                    retdata = []
                    for retstr in retstrings:
                        retdata.append(data[retstr])
                    return retdata
                else:
                    raise Exception('%s: API returned status code %s.' % (caller, data['StatusCode']))
            except Exception as e:
                raise Exception('%s: API did not return expected JSON data.' % caller)
        else:
            raise Exception('%s: Failed with GET status %s.' % (caller, response.status_code))

   # --------------------------------------------------------------------

    def BGNES_Version(self)->str:
        response = self.BGAPI_call('/Diagnostic/Version')
        return self.BGNES_handle_response(response, 'BGNES_Version', ['Version'])[0]

    def BGNES_Status(self)->list:
        response = self.BGAPI_call('/Diagnostic/Status')
        return self.BGNES_handle_response(response, 'BGNES_Status', ['SystemState', 'ServiceStateNES'])

    # def BGNES_GetToken(self, user:str, passwd:str)->str:
    #     # previously: response = BGAPI_call('/Auth/GetToken?Username=%s&Password=%s' % (user, passwd))
    #     # previously: return BGNES_handle_response(response, 'BGNES_GetToken', ['AuthKey'])[0]
    #     global SessionToken
    #     SessionToken = NES.Client.GetInsecureToken(_Username=user, _Password=passwd)
    #     return SessionToken

   # --------------------------------------------------------------------

    def BGNES_simulation_create(self, name:str, ExistingID:int = -1):
        Loading:bool = ExistingID != -1
        self.Simulation = SimClientInstance(
            credentials=self.credentials,
            simname=name,
            host=self.uri_host,
            port=self.uri_port,
            use_https=self.use_https,
            loading=Loading
        )
        if (ExistingID != -1):
            self.Simulation.Sim.ID = ExistingID
        return self.Simulation

    def BGNES_simulation_reset(self)->str:
        return self.Simulation.Sim.Reset()['StatusCode']

    def BGNES_simulation_runfor(self, Runtime_ms:float)->str:
        return self.Simulation.Sim.RunFor(Runtime_ms)['StatusCode']

    def BGNES_simulation_runfor_and_await_outcome(self, Runtime_ms:float, timeout_ms=10000)->bool:
        # Get the simulation timer before the next run:
        status_dict = self.BGNES_get_simulation_status()
        if status_dict['StatusCode'] != 0:
            print('Simulation status '+str(status_dict['StatusCode']))
            return False
        t_before_run = status_dict['InSimulationTime_ms']

        # Run:
        self.BGNES_simulation_runfor(Runtime_ms)

        # Await completion:
        dt_s = 0.005
        dt_ms = int(dt_s*1000)
        while True:
            sleep(dt_s)
            status_dict = self.BGNES_get_simulation_status()
            if status_dict['StatusCode'] != 0:
                print('Simulation failed. Status '+str(status_dict['StatusCode']))
                return False
            # Ensure that runfor started and that it ended.
            if status_dict['InSimulationTime_ms'] > t_before_run:
                if not status_dict['IsSimulating']:
                    return True
            timeout_ms -= dt_ms
            if timeout_ms <= 0:
                print('Waiting for simulation completion timed out.')
                return False

    def BGNES_get_simulation_status(self)->str:
        return self.Simulation.Sim.GetStatus()
        # seeking = [
        #     'IsSimulating',
        #     'RealWorldTimeRemaining_ms',
        #     'RealWorldTimeElapsed_ms',
        #     'InSimulationTime_ms',
        #     'InSimulationTimeRemaining_ms',
        #     'PercentComplete'
        # ]

    def BGNES_simulation_recordall(self, MaxRecordTime_ms:float)->str:
        return self.Simulation.Sim.RecordAll(MaxRecordTime_ms)['StatusCode']

    def BGNES_get_recording(self)->dict:
        return self.Simulation.Sim.GetRecording()

   # --------------------------------------------------------------------

    def BGNES_sphere_create(self, radius_um:float, center_um:tuple, name=None):
        SphereCfg = NES.Shapes.Sphere.Configuration()
        if name is None:
            name = self.generate_autoname('sphere-')
        SphereCfg.Name = name
        SphereCfg.Radius_um = radius_um
        SphereCfg.Center_um = list(center_um)
        sphere = self.Simulation.Sim.AddSphere(SphereCfg)
        return sphere

    def BGNES_cylinder_create(self, 
        Point1Radius_um:float,
        Point1Position_um: tuple,
        Point2Radius_um:float,
        Point2Position_um: tuple,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('cylinder-')
        CylinderCfg = NES.Shapes.Cylinder.Configuration()
        CylinderCfg.Name = name
        CylinderCfg.Point1Position_um = list(Point1Position_um)
        CylinderCfg.Point2Position_um = list(Point2Position_um)
        CylinderCfg.Point1Radius_um = Point1Radius_um
        CylinderCfg.Point2Radius_um = Point2Radius_um
        cylinder = self.Simulation.Sim.AddCylinder(CylinderCfg)
        return cylinder

    def BGNES_box_create(self, 
        CenterPosition_um:tuple,
        Dimensions_um:tuple,
        Rotation_rad:tuple,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('box-')
        BoxCfg = NES.Shapes.Box.Configuration()
        BoxCfg.Name = name
        BoxCfg.CenterPosition_um = list(CenterPosition_um)
        BoxCfg.Dimensions_um = list(Dimensions_um)
        BoxCfg.Rotation_rad = list(Rotation_rad)
        box = self.Simulation.Sim.AddBox(BoxCfg)
        return box

   # --------------------------------------------------------------------

    def BGNES_BS_compartment_create(self, 
        ShapeID:str,
        MembranePotential_mV:float,
        RestingPotential_mV:float,
        SpikeThreshold_mV:float,
        DecayTime_ms:float,
        AfterHyperpolarizationAmplitude_mV:float,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('compartment-')
        Cfg = NES.Models.Compartments.BS.Configuration()
        Cfg.Name = name
        Cfg.SpikeThreshold_mV = SpikeThreshold_mV
        Cfg.DecayTime_ms = DecayTime_ms
        Cfg.MembranePotential_mV = MembranePotential_mV
        Cfg.AfterHyperpolarizationAmplitude_mV = AfterHyperpolarizationAmplitude_mV
        Cfg.RestingPotential_mV = RestingPotential_mV
        Cfg.Shape = ShapeID
        compartment = self.Simulation.Sim.AddBSCompartment(Cfg)
        return compartment

    def BGNES_connection_staple_create(self, 
        SourceCompartmentID:str,
        DestinationCompartmentID:float,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('staple-')
        Cfg = NES.Models.Connections.Staple.Configuration()
        Cfg.Name = name
        Cfg.SourceCompartment = SourceCompartmentID
        Cfg.DestinationCompartment = DestinationCompartmentID
        staple = self.Simulation.Sim.AddStaple(Cfg)
        return staple

    def BGNES_BS_receptor_create(self, 
        SourceCompartmentID:str,
        DestinationCompartmentID:str,
        Conductance_nS:float,
        TimeConstantRise_ms:float,
        TimeConstantDecay_ms:float,
        ReceptorLocation_um:tuple,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('receptor-')
        Cfg = NES.Models.Connections.Receptor.Configuration()
        Cfg.Name = name
        Cfg.SourceCompartment = SourceCompartmentID
        Cfg.DestinationCompartment = DestinationCompartmentID
        Cfg.Conductance_nS = Conductance_nS
        Cfg.TimeConstantRise_ms = TimeConstantRise_ms
        Cfg.TimeConstantDecay_ms = TimeConstantDecay_ms
        Cfg.ReceptorLocation_um = ReceptorLocation_um
        receptor = self.Simulation.Sim.AddReceptor(Cfg)
        return receptor

    def BGNES_BS_neuron_create(self, 
        Soma,
        Axon,
        MembranePotential_mV:float,
        RestingPotential_mV:float,
        SpikeThreshold_mV:float,
        DecayTime_ms:float,
        AfterHyperpolarizationAmplitude_mV:float,
        PostsynapticPotentialRiseTime_ms:float,
        PostsynapticPotentialDecayTime_ms:float,
        PostsynapticPotentialAmplitude_nA:float,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('neuron-')
        Cfg = NES.Models.Neurons.BS.Configuration()
        Cfg.Name = name
        Cfg.Soma = Soma
        Cfg.Axon = Axon
        Cfg.MembranePotential_mV = MembranePotential_mV
        Cfg.RestingPotential_mV = RestingPotential_mV
        Cfg.SpikeThreshold_mV = SpikeThreshold_mV
        Cfg.DecayTime_ms = DecayTime_ms
        Cfg.AfterHyperpolarizationAmplitude_mV = AfterHyperpolarizationAmplitude_mV
        Cfg.PostsynapticPotentialRiseTime_ms = PostsynapticPotentialRiseTime_ms
        Cfg.PostsynapticPotentialDecayTime_ms = PostsynapticPotentialDecayTime_ms
        Cfg.PostsynapticPotentialAmplitude_nA = PostsynapticPotentialAmplitude_nA
        neuron = self.Simulation.Sim.AddBSNeuron(Cfg)
        return neuron

   # --------------------------------------------------------------------

    def BGNES_DAC_create(self, 
        DestinationCompartmentID:str,
        ClampLocation_um:tuple,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('DAC-')
        Cfg = NES.Tools.PatchClampDAC.Configuration()
        Cfg.Name = name
        Cfg.DestinationCompartment = DestinationCompartmentID
        Cfg.ClampLocation_um = ClampLocation_um
        DAC = self.Simulation.Sim.AddPatchClampDAC(Cfg)
        return DAC

    def BGNES_NESRequest(self)->str:
        # Send.
        # RequestJSONstr = json.dumps(self.NESRequest_batch)
        # res = self.Simulation.ClientInstance.NESRequest(RequestJSONstr)
        res = self.Simulation.ClientInstance.NESRequest(self.NESRequest_batch)
        # Clear batch buffer.
        self.NESRequest_batch = []
        return res

    def BGNES_add_to_batch(self, Req:dict):
        self.NESRequest_batch.append(Req)

    # Adds request ID and wraps in brackets, then adds to batch.
    def BGNES_make_and_batch_NESRequest(self,
        ReqFunc:str,
        ReqParams:dict,):

        ReqID = self.gen_ReqID()
        Req = {
            "ReqID": ReqID,
            ReqFunc: ReqParams,
        }

        self.BGNES_add_to_batch(Req)

    def BGNES_NES_Common(self,
        ReqFunc:str,
        ReqParams:dict,
        batch_it:bool,):

        SimID = self.get_SimID()
        if SimID < 0:
            return None

        ReqParams["SimulationID"] = SimID
        self.BGNES_make_and_batch_NESRequest(ReqFunc, ReqParams)
        if batch_it:
            return "batched"
        return self.BGNES_NESRequest() # Send the batch immediately.

    # Returns (success, first_response_dict).
    def BGNES_First_NESResponse(self, source:str, batch_it:bool, responses)->tuple:
        if batch_it:
            if isinstance(responses, str):
                return ((responses == "batched"), {})
            return (False, {})
        if not isinstance(responses, list):
            print('Bad response format. Expected list of NESRequest responses.')
            return (False, {})
        firstreq_response = responses[0]
        if not isinstance(firstreq_response, dict):
            print('Bad response format. Expected NESRequest response dict.')
            return (False, {})
        if "StatusCode" not in firstreq_response:
            print('Bad response format. Missing StatusCode.')
            return (False, {})
        if firstreq_response["StatusCode"] != 0:
            print(str(source)+' failed. StatusCode: '+str(firstreq_response["StatusCode"]))
            return (False, {})
        return (True, firstreq_response)

    def BGNES_set_specific_AP_times(self,
        TimeNeuronPairs:list,
        batch_it=False):

        ReqFunc = 'Simulation/SetSpecificAPTimes'
        ReqParams = {
            "TimeNeuronPairs": TimeNeuronPairs,
        }
        return self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)

    # spont_spike_interval_ms_stdev == 0 means no spontaneous activity
    def BGNES_set_spontaneous_activity(self,
        spont_spike_interval_ms_mean:float,
        spont_spike_interval_ms_stdev:float,
        neuron_ids:list,
        batch_it=False)->bool:

        ReqFunc = 'Simulation/SetSpontaneousActivity'
        ReqParams = {
            'SpikeIntervalMean_ms': spont_spike_interval_ms_mean,
            'SpikeIntervalStDev_ms': spont_spike_interval_ms_stdev,
            'NeuronIDs': neuron_ids,
        }
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        success, first_response = self.BGNES_First_NESResponse('Set Spontaneous Activity', batch_it, responses)
        return success

    def get_vec3_from_response(self, response, prefix:str, units="um")->tuple:
        xlabel = prefix+'X_'+units
        ylabel = prefix+'Y_'+units
        zlabel = prefix+'Z_'+units
        if not (xlabel in response and ylabel in response and zlabel in response):
            print('Bad format. Expected 3D vector.')
            return (False, [])
        x = response[xlabel]
        y = response[ylabel]
        z = response[zlabel]
        if not (isinstance(x, (float,int)) and isinstance(y, (float,int)) and isinstance(z, (float,int))):
            print('Wrong types. Expected 3D vector of floats or ints.')
            return (False, [])
        return (True, [x, y, z])

    def get_list_from_response(self, response, listkey:str)->tuple:
        if not listkey in response:
            print('Bad format. Expected list.')
            return (False, [])
        thelist = response[listkey]
        if not isinstance(thelist, list):
            print('Wrong type. Expected list.')
            return (False, [])
        return (True, thelist)

    def BGNES_get_geometric_center(self, batch_it=False)->tuple:
        ReqFunc = "Simulation/GetGeoCenter"
        ReqParams = {}
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        success, first_response = self.BGNES_First_NESResponse('Get Geometric Center', batch_it, responses)
        if not success:
            return (False, [])
        return self.get_vec3_from_response(first_response, "GeoCenter")

    def BGNES_attach_recording_electrodes(self,
        set_of_electrode_specs:list,
        batch_it=False)->list:

        ReqFunc = "Simulation/AttachRecordingElectrodes"
        ReqParams = {
            "ElectrodeSpecs": set_of_electrode_specs,
        }
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        success, first_response = self.BGNES_First_NESResponse('Attach Recording Electrodes', batch_it, responses)
        if not success:
            return []
        return self.get_list_from_response(first_response, "ElectrodeIDs")

    def BGNES_calcium_imaging_attach(self, calcium_specs:dict, batch_it=False):
        ReqFunc = "CalciumImagingAttach"
        ReqParams = calcium_specs
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Ca Imaging Attach', batch_it, responses)[0]

    def BGNES_calcium_imaging_show_voxels(self, batch_it=False)->tuple:
        ReqFunc = "CalciumImagingShowVoxels"
        ReqParams = {}
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Ca Imaging Show Voxels', batch_it, responses)

    def BGNES_calcium_imaging_record_aposteriori(self, batch_it=False)->bool:
        ReqFunc = "CalciumImagingRecordAposteriori"
        ReqParams = {}
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Ca Imaging Record A-Posteriori', batch_it, responses)[0]

    # 0.0 means stop recording, -1.0 means record forever.
    def BGNES_set_record_instruments(self, t_max_ms:float, batch_it=False)->bool:
        ReqFunc = "Simulation/SetRecordInstruments"
        ReqParams = {
            'MaxRecordTime_ms': t_max_ms,
        }
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Set Record Instruments', batch_it, responses)[0]

    def BGNES_get_instrument_recordings(self, batch_it=False)->tuple:
        ReqFunc = "Simulation/GetInstrumentRecordings"
        ReqParams = {}
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Get Instrument Recordings', batch_it, responses)

    def BGNES_CaImagingSetupMicroscope(self,
            VoxelResolution_nm: float, # is um
            ImageWidth_px: int,
            ImageHeight_px: int,
            NumVoxelsPerSlice: int,
            ScanRegionOverlap_percent: float,
            NumPixelsPerVoxel_px: int,
            FlourescingNeuronIDs: list, # Empty means all.
            CalciumIndicator: str,
            IndicatorRiseTime_ms: float,
            IndicatorDecayTime_ms: float,
            IndicatorInterval_ms: float,
            BrightnessAmplification: float,
            batch_it=False,
        )->bool:
        ReqFunc = "VSDA/Ca/SetupMicroscope"
        ReqParams = {
            "VoxelResolution_nm": VoxelResolution_nm, # is um
            "ImageWidth_px": ImageWidth_px,
            "ImageHeight_px": ImageHeight_px,
            "NumVoxelsPerSlice": NumVoxelsPerSlice,
            "ScanRegionOverlap_percent": ScanRegionOverlap_percent,
            "NumPixelsPerVoxel_px": NumPixelsPerVoxel_px,
            "FlourescingNeuronIDs": FlourescingNeuronIDs,
            "CalciumIndicator": CalciumIndicator,
            "IndicatorRiseTime_ms": IndicatorRiseTime_ms,
            "IndicatorDecayTime_ms": IndicatorDecayTime_ms,
            "IndicatorInterval_ms": IndicatorInterval_ms,
            "BrightnessAmplification": BrightnessAmplification,
        }
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return self.BGNES_First_NESResponse('Setup Ca Imaging Microscope', batch_it, responses)[0]

    def BGNES_DefineScanRegion(self,
        Point1_um:list,
        Point2_um:list,
        batch_it=False)->tuple:
        ReqFunc = "VSDA/Ca/DefineScanRegion"
        ReqParams = {
            "Point1_um": Point1_um,
            "Point2_um": Point2_um,
        }
        success, first_response  = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        if not success:
            return (False, "")
        return self.BGNES_First_NESResponse('Define Scan Region', batch_it, responses)[0]
        if "ScanRegionID" not in first_response:
            return (False, "")
        return (True, first_response["ScanRegionID"])

    def BGNES_CaQueueRenderOperation(self,
        ScanRegionID:str,
        batch_it=False)->bool:
        ReqFunc = "VSDA/Ca/QueueRenderOperation"
        ReqParams = {
            "ScanRegionID": ScanRegionID,
        }
        success, first_response  = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        return success

    def GetCaRenderStatus(self)->tuple:
        ReqFunc = "VSDA/Ca/GetRenderStatus"
        ReqParams = {}
        return self.BGNES_NES_Common(ReqFunc, ReqParams, False)

    def CaWaitForRender(self)->bool:
        try:
            NES.VSDA.CA.WaitForRender(StatusFunc=self.GetCaRenderStatus)
        except Exception as e:
            print('Wait for Render failed.')
            return False
        return True

    def GetCaImageStack(self, ScanRegionID:str, batch_it=False)->tuple:
        ReqFunc = "VSDA/Ca/GetImageStack"
        ReqParams = {
            "ScanRegionID": ScanRegionID,
        }
        success, first_response  = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)
        if not success:
            return (False, [])
        if "RenderedImages" not in first_response:
            return (False, [])
        return (True, first_response["RenderedImages"])

    def BGNES_save(self, batch_it=False):
        ReqFunc = 'Simulation/Save'
        ReqParams = {}
        return self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)

    # This returns a Simulation object (with temporary Sim.ID) and
    # a task ID for the loading task to watch with BGNES_get_manager_task_status().
    def BGNES_load(self, timestampedname:str)->int:
        self.Simulation = SimClientInstance(
            credentials=self.credentials,
            simname=timestampedname,
            host=self.uri_host,
            port=self.uri_port,
            use_https=self.use_https,
            loading=True,
        )
        ReqFunc = 'Simulation/Load'
        ReqParams = {
            "SavedSimName": timestampedname,
        }
        responses = self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it=False)
        success, firstreq_response = self.BGNES_First_NESResponse('Loading', False, responses)
        if not success:
            exit(1)
        if "TaskID" not in firstreq_response:
            print("Missing Loading Task ID.")
            exit(1)
        TaskID = firstreq_response["TaskID"]
        return TaskID

    def BGNES_get_manager_task_status(self, taskID:int, batch_it=False):
        ReqFunc = 'ManTaskStatus'
        ReqParams = {
            'TaskID': taskID,
        }
        return self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)

    # NOTE: This has to use the new NESRequest API.
    # Format:
    # "PatchClampDACSetOutputList": {
    #   "SimulationID": <SimID>,
    #   "PatchClampDACID": <DAC-ID>,
    #   "ControlData": [
    #      [ <t_ms>, <v_mV> ],
    #      (more pairs)
    #   ]
    # }
    # 
    def BGNES_DAC_set_output_list(self, 
        TargetDAC,
        DACControlPairs:list,
        batch_it=False):

        ReqFunc = 'PatchClampDACSetOutputList'
        ReqParams = {
            "PatchClampDACID": TargetDAC.ID,
            "ControlData": DACControlPairs,
        }
        return self.BGNES_NES_Common(ReqFunc, ReqParams, batch_it)

    def BGNES_ADC_create(self, 
        SourceCompartmentID:str,
        ClampLocation_um:tuple,
        name=None)->str:
        if name is None:
            name = self.generate_autoname('ADC-')
        Cfg = NES.Tools.PatchClampADC.Configuration()
        Cfg.Name = name
        Cfg.SourceCompartment = SourceCompartmentID
        Cfg.ClampLocation_um = ClampLocation_um
        ADC = self.Simulation.Sim.AddPatchClampADC(Cfg)
        return ADC

    def BGNES_ADC_set_sample_rate(self, 
        TargetADC,
        Timestep_ms:float)->str:
        return TargetADC.SetSampleRate(Timestep_ms)

    def BGNES_ADC_get_recorded_data(self, 
        TargetADC)->list:
        responsedict = TargetADC.GetRecordedData()
        data = responsedict['RecordedData_mV']
        statuscode = responsedict['StatusCode']
        timestep = responsedict['Timestep_ms']
        if statuscode != 0:
            return None, None
        return data, timestep

    # -- Higher level functions: ------------------------------------

    def BGNES_QuickStart(self, scriptversion:str, versionmustmatch:bool, verbose=False)->bool:
        '''
        Check system version compatibility, check system status, and
        obtain authentication token in a single call.
        '''
        version = self.BGNES_Version()
        if verbose: print('BGNES Version: '+str(version))
        if versionmustmatch:
            if version != scriptversion:
                print('Version mismatch. Script version is %s.' % scriptversion)
                return False

        systemstate, servicestate = self.BGNES_Status()
        if systemstate != 'Healthy':
            print('System state: '+str(systemstate))
            return False
        elif verbose:
            print('System state: '+str(systemstate))
        if servicestate != 0:
            print('NES service status: '+str(servicestate))
            return False
        elif verbose:
            print('NES service status: '+str(servicestate))

        return True

def BG_API_Setup(
    user:str,
    passwd:str,
    debug_api=True,
    local_port=8000,
    remote_host='api.braingenix.org',
    remote_port=443,
    is_local=False,
    ):
    glb.bg_api = BG_API(
        credentials=Credentials(user=user, passwd=passwd),
        debug_api=debug_api,
        local_port=local_port,
        remote_host=remote_host,
        remote_port=remote_port,
        is_local=is_local,
        )

# -- Testing API calls: -----------------------------------------

if __name__ == '__main__':

    BG_API_Setup(user='Admonishing', passwd='Instruction')

    from sys import argv
    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-L':
            glb.bg_api.set_local()

    scriptversion='0.0.1'
    print('Getting version and status...')
    glb.bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=True)

    print('Calling BGNES_simulation_create...')
    glb.bg_api.BGNES_simulation_create(name='test')
    print('Simulation: '+str(glb.bg_api.Simulation.Sim.ID))

    print('Calling BGNES_sphere_create...')
    sphere = glb.bg_api.BGNES_sphere_create(
        radius_um=10, 
        center_um=(0,0,0)
    )
    print('Shape ID: '+str(sphere.ID))

    print('Calling BGNES_cylinder_create...')
    cylinder = glb.bg_api.BGNES_cylinder_create(
        Point1Radius_um=10,
        Point1Position_um=(0,0,0),
        Point2Radius_um=20,
        Point2Position_um=(10,10,10)
    )
    print('Shape ID: '+str(cylinder.ID))

    print('Calling BGNES_box_create...')
    box = glb.bg_api.BGNES_box_create(
        CenterPosition_um=(0,0,0),
        Dimensions_um=(10,10,10),
        Rotation_rad=(0,0,0)
    )
    print('Shape ID: '+str(box.ID))

    print('Calling BGNES_BS_compartment_create...')
    compartment = glb.bg_api.BGNES_BS_compartment_create(
        ShapeID=sphere.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-50.0,
        SpikeThreshold_mV=30.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0
    )
    print('Compartment ID: '+str(compartment.ID))

    print('Calling BGNES_BS_compartment_create for second compartment...')
    second_compartment = glb.bg_api.BGNES_BS_compartment_create(
        ShapeID=cylinder.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-50.0,
        SpikeThreshold_mV=30.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0
    )
    print('Second Compartment ID: '+str(second_compartment.ID))

    print('Calling BGNES_connection_staple_create...')
    staple = glb.bg_api.BGNES_connection_staple_create(
        SourceCompartmentID=compartment.ID,
        DestinationCompartmentID=second_compartment.ID
    )
    print('Staple ID: '+str(staple.ID))

    print('Calling BGNES_BS_receptor_create...')
    receptor = glb.bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=compartment.ID, 
        DestinationCompartmentID=second_compartment.ID,
        Conductance_nS=50.0,
        TimeConstantRise_ms=5.0,
        TimeConstantDecay_ms=30.0,
        ReceptorLocation_um=(5,5,5),
    )
    print('Receptor ID: '+str(receptor.ID))

    print('Calling BGNES_BS_neuron_create...')
    neuron = glb.bg_api.BGNES_BS_neuron_create(
        Soma=sphere.ID, 
        Axon=cylinder.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-60.0,
        SpikeThreshold_mV=-50.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0,
        PostsynapticPotentialRiseTime_ms=5.0,
        PostsynapticPotentialDecayTime_ms=25.0,
        PostsynapticPotentialAmplitude_mV=20.0,
    )
    print('Neuron ID: '+str(neuron.ID))

    print('Calling BGNES_DAC_create...')
    DAC = glb.bg_api.BGNES_DAC_create(
        DestinationCompartmentID=compartment.ID,
        ClampLocation_um=(2,2,2),
    )
    print('DAC ID: '+str(DAC.ID))

    print('Calling BGNES_DAC_set_output_list...')
    DAC_control_commands = [(0, -60.0), (100.0, -40.0), (105.0, -60.0), (200.0, -40.0), (205.0, -60.0), (300.0, -40.0), (305.0, -60.0), (400.0, -40.0), (405.0, -60.0)]
    print('With control commands: '+str(DAC_control_commands))
    status = glb.bg_api.BGNES_DAC_set_output_list(
        TargetDAC=DAC,
        DACControlPairs=DAC_control_commands,
    )
    #print(str(status.text))
    for resp in status:
        if resp['StatusCode'] != 0:
            raise Exception('NES request returned an error in request '+str(resp['ReqID']))
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_create...')
    ADC = glb.bg_api.BGNES_ADC_create(
        SourceCompartmentID=compartment.ID,
        ClampLocation_um=(2,2,2),
    )
    print('ADC ID: '+str(ADC.ID))

    print('Calling BGNES_ADC_set_sample_rate...')
    status = glb.bg_api.BGNES_ADC_set_sample_rate(
        TargetADC=ADC,
        Timestep_ms=1.0
    )
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_get_recorded_data...')
    data, timestep = glb.bg_api.BGNES_ADC_get_recorded_data(
        TargetADC=ADC
    )
    print('Data: '+str(data))
    print('Timestep: '+str(timestep))

    print('Setting record all...')
    status = glb.bg_api.BGNES_simulation_recordall(-1)
    print('Status: '+str(status))

    print('Running the simulation...')
    status = glb.bg_api.BGNES_simulation_runfor(500.0)
    print('Status: '+str(status))

    print('Checking simulation status...')
    while True:
        status = glb.bg_api.BGNES_get_simulation_status()
        print('Status: '+str(status))
        if not status['IsSimulating']:
            break
    print('Simulation done.')

    print('Retrieving recorded data...')
    data = glb.bg_api.BGNES_get_recording()
    print('Data: '+str(data))

    print('Resetting the simulation...')
    status = glb.bg_api.BGNES_simulation_reset()
    print('Status: '+str(status))
