import sys; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
NES, client = L.connect()
codes = {}
for i in range(139, 164):
    r = client.RequestHandler.BuildPostQuery([{"Simulation/GetStatus": {"SimulationID": i}}], "/NES")[0]
    codes[i] = r.get('StatusCode')
print(codes)
