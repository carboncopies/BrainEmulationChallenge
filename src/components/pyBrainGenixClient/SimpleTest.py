# Simple Test Example For BG
import time
import base64

import BrainGenix.NES as NES



def main():

    # Start Tests
    print("----------------------------")
    print("Starting BG-NES Simple Test")


    # Test Getting A Token
    SessionToken = NES.Client.GetInsecureToken(_Username="Admonishing", _Password="Instruction")
    print(f" -- API Returned Session Token '{SessionToken}'")

    # Create Client Configuration For Local Simulation
    print(" -- Creating Client Configuration For Local Simulation")
    ClientCfg = NES.Client.Configuration()
    ClientCfg.Mode = NES.Client.Modes.Remote
    ClientCfg.Host = "api.braingenix.org"
    ClientCfg.Port = 80
    # ClientCfg.Host = "localhost"
    # ClientCfg.Port = 8000
    ClientCfg.Token = SessionToken

    # Create Client Instance
    print(" -- Creating Client Instance")
    ClientInstance = NES.Client.Client(ClientCfg)

    assert(ClientInstance.IsReady())

    
    # Create A New Simulation
    print(" -- Creating Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = "My First Simulation"
    MySim = ClientInstance.CreateSimulation(SimulationCfg)
    

    # Create Sphere
    print(" -- Creating Sphere")
    SphereCfg = NES.Shapes.Sphere.Configuration()
    SphereCfg.Name = "My Sphere"
    SphereCfg.Radius_um = 4.
    SphereCfg.Center_um = [0, 0, 0]
    MySphere = MySim.AddSphere(SphereCfg)

    # Create Box
    print(" -- Creating Box")
    BoxCfg = NES.Shapes.Box.Configuration()
    BoxCfg.Name = "My Box"
    BoxCfg.CenterPosition_um = [0, 6, 0]
    BoxCfg.Dimensions_um = [1, 1, 1]
    BoxCfg.Rotation_rad = [0, 0, 0]
    MyBox = MySim.AddBox(BoxCfg)
    
    # Create Cylinder
    print(" -- Creating Cylinder")
    CylinderCfg = NES.Shapes.Cylinder.Configuration()
    CylinderCfg.Name = "My Cylinder"
    CylinderCfg.Point1Position_um = [0, 7.5, 0]
    CylinderCfg.Point2Position_um = [0, 7.5, 3]
    CylinderCfg.Point1Radius_um = 0.7
    CylinderCfg.Point2Radius_um = 2
    MyCylinder = MySim.AddCylinder(CylinderCfg)

    # Create Compartments
    print(" -- Creating BS Compartment With Sphere")
    Cfg = NES.Models.Compartments.BS.Configuration()
    Cfg.Name = "My Compartment 1"
    Cfg.SpikeThreshold_mV = 0.0
    Cfg.DecayTime_ms = 0.0
    Cfg.MembranePotential_mV = 0.0
    Cfg.Shape = MySphere
    MySphereCompartment = MySim.AddBSCompartment(Cfg)

    print(" -- Creating BS Compartment With Box")
    Cfg = NES.Models.Compartments.BS.Configuration()
    Cfg.Name = "My Compartment 2"
    Cfg.SpikeThreshold_mV = 0.0
    Cfg.DecayTime_ms = 0.0
    Cfg.MembranePotential_mV = 0.0
    Cfg.Shape = MyBox
    MyBoxCompartment = MySim.AddBSCompartment(Cfg)

    print(" -- Creating BS Compartment With Cylinder")
    Cfg = NES.Models.Compartments.BS.Configuration()
    Cfg.Name = "My Compartment 3"
    Cfg.SpikeThreshold_mV = 0.0
    Cfg.DecayTime_ms = 0.0
    Cfg.MembranePotential_mV = 0.0
    Cfg.Shape = MyCylinder
    MyCylinderCompartment = MySim.AddBSCompartment(Cfg)


    # Setup VSDA Renderer
    print(" -- Setting Up VSDA EM Renderer")
    EMConfig = NES.VSDA.EM.Configuration()
    EMConfig.PixelResolution_nm = 0.1
    EMConfig.ImageWidth_px = 256
    EMConfig.ImageHeight_px = 256
    EMConfig.SliceThickness_nm = 100
    EMConfig.ScanRegionOverlap_percent = 10
    VSDAEMInstance = MySim.AddVSDAEM(EMConfig)

    print(" -- Setting Up VSDA EM Scan Region")
    VSDAEMInstance.DefineScanRegion([-1,-1,-1], [9,9,9])
    
    print(" -- Queueing Render Operation")
    VSDAEMInstance.QueueRenderOperation()

    print(" -- Waiting Until Render Operation Done")
    while (VSDAEMInstance.GetRenderStatus()["RenderStatus"] != 5):
        time.sleep(0.5)

    print(" -- Getting Image Manifest")
    ImageHandles = VSDAEMInstance.GetImageStack()

    print(" -- Saving Images")
    for Image in ImageHandles:
        print(f"    -- Saving Image '{Image}'")
        ImageData = VSDAEMInstance.GetImage(Image)
        with open(Image.split("/")[1],"wb") as FileHandler:
            FileHandler.write(base64.decodebytes(ImageData))


if __name__ == "__main__":
    main()