
import pandas as pds
import subprocess
import autoassociative_connectome_myg
import re

df = pds.read_excel(open('NetmorphParOptim/test_sample.xlsx','rb')) 
print(df.head(10))
print(df.shape)

cols = df.columns
# print(cols[5])

df['usable_conns']=0


def find_port_in_file(filename, match_string):
    """
    Reads a file and searches for a line containing the match_string. 
    If found, extracts and returns the port number after the colon.
    """
    with open(filename, 'r') as f:
        for line in f:
            if match_string in line:
                # Extract port number after colon
                match = re.search(r': (\d+)', line)
                if match:
                    return int(match.group(1))
    return None


# for i in range(5):
#     subprocess.run(["sh", "check_ports_api.sh"])
#     subprocess.run(["sh", "check_ports_nes.sh"])
#     subprocess.run(["sh", "cd ~/BrainGenix/BrainGenix-API/Tools && ./Run.sh"])
#     subprocess.run(["sh", "cd ~/BrainGenix/BrainGenix-NES/Tools && ./Run.sh"])


# Helper functions
## Read NES.yaml after check_ports_nes.sh updatesit to get the port number for the NES API. 
# This is needed to connect the reservoir and connectome scripts to the correct port.

fname = "/home/mgabr001/BrainGenix/BrainGenix-NES/Binaries/NES.yaml"
port = find_port_in_file(fname, "Network_NES_API_Port:")-1     # Need Network Service port
print("Port: ", port)


### %%
for j in range(df.shape[0]
               ): # loop over number of  par lines in the sample excel file
    # for j in range(1): # loop over number of  par lines in the sample excel file
    pars=[]
    # print(df.iloc[j])
   
    for k in range(len(cols)): # number of parameters in the excel file
        # print(df.iloc[j][cols[k]])
        if k < 6:
            pars.append(int(df.iloc[j][cols[k]]))       # explicit type casting since the values are read as floats from the excel file, but we need integers for the parameters in the reservoir script.
        else:
            pars.append(float(df.iloc[j][cols[k]]))
    # print(f'string {pars[2]}')
    
    ####################################
    ## Test with original parameters with modified reservoir script. Number of usabele connections is suppose to be 83.
    ####################################

    # subprocess.run([
    # "python3",
    # "autoassociative_reservoir_myg.py",
    # "-Port", str(port),
    # "-modelfile", "nesvbp-autoassociative",
    # "-modelname", "myg-autoassociative" #,
    # # "-DoBlend", "True",
    # # "-BevelDepth", "0.2",
    # # "-BlendExec", "/home/mgabr001/blender-4.1.1-linux-x64/blender",
    # ])

    ####################################
    ## Run Reservoir script with Latin Hypercube generated parameters.
    ####################################

    subprocess.run([
    "python3",
    "autoassociative_reservoir_myg.py",
    "-Port", str(port),
    "-modelfile", "nesvbp-autoassociative",
    "-modelname", "myg-autoassociative",
    # "-DoBlend", "True",
    # "-BevelDepth", "0.2",
    # "-BlendExec", "/home/mgabr001/blender-4.1.1-linux-x64/blender",
    "-growdays", str(pars[0]),
    "-pyramidal", str(pars[1]),
    "-interneuron", str(pars[2]),
    "-minneuronseparation", str(pars[3]),
    "-shapeRadius", str(pars[4]),
    "-shapeThickness", str(pars[5]),
    "-dmWeight", str(pars[6])
    ])
    

    # Run connectomautoassociative_connectome_myg script to get number of usable connections for the generated reservoir. 
    # This is the main output that will be used for par optimization. 
    # I wrapped the original script into a function to return the number of usable connections as an integer.

    print(autoassociative_connectome_myg.net_connectome(port))

    df.loc[j, 'usable_conns'] = autoassociative_connectome_myg.net_connectome(port)   
    df.to_excel("NetmorphParOptim/test_sample_labeled.xlsx", index=False)
    

##### RUNNING ORIGINAL SCRIPTS AS A TEST. THE NUMBER OF USABLE CONNECTIONS SHOULD BE 83.

    # subprocess.run([
    # "python3",
    # "autoassociative_reservoir.py",
    # "-Port", "8030",
    # "-modelfile", "nesvbp-autoassociative",
    # "-modelname", "myg-autoassociative" #,
    # # "-DoBlend", "True",
    # # "-BevelDepth", "0.2",
    # # "-BlendExec", "/home/mgabr001/blender-4.1.1-linux-x64/blender",
    # ])

    # subprocess.run([
    #     "python3",
    #     "autoassociative_connectome.py",
    #     "-Port", "8030",
    #     "-modelname", "myg-autoassociative" #,
    # ])


